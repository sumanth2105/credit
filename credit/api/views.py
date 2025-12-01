import csv
import io
import logging
from api.forms import (
    Case1Form, BeneficiaryRegisterForm, BeneficiaryDocumentForm, BeneficiaryEditForm,
    Case1DetailsForm, Case2DetailsForm, Case2LoanForm, Case3DetailsForm, Case3LoanForm
)
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponseForbidden
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from .models import (
    Beneficiary, LoanHistory, ConsumptionData, AIScoreLog, Profile,
    BeneficiaryDocument, LoanApplication, Case1Details, Case2Details, Case2Loan,
    Case3Details, Case3Loan
)
from .models import Case4Details, Case4Loan
from api.forms import Case4DetailsForm, Case4LoanForm
from django.contrib.auth.models import User
from django.utils import timezone

logger = logging.getLogger(__name__)




# ---------- Helper: auto income scoring & reset AI fields ----------

def auto_compute_income_from_details(ben):
    """
    Auto-generate income_est using electricity_bill, mobile_bill, gas_bill
    from whichever CaseXDetails exists + beneficiary.estimated_monthly_income.
    Also reset AI scoring fields (score, risk, etc.) so ML model can overwrite later.
    """
    # 1. Pick the first available Case-details object for this beneficiary
    details = None
    for attr in ("case1_details", "case2_details", "case3_details", "case4_details"):
        try:
            details = getattr(ben, attr)
            if details is not None:
                break
        except Exception:
            continue

    # 2. Extract bills
    ele = mob = gas = 0.0
    if details:
        ele = float(getattr(details, "electricity_bill", 0) or 0)
        mob = float(getattr(details, "average_mobile_bill", 0) or 0)
        gas = float(getattr(details, "gas_bill", 0) or 0)

    total_bills = ele + mob + gas

    # 3. Personal estimated income from profile form
    personal_est = float(ben.estimated_monthly_income or 0)

    # 4. Map bills → income band (simple heuristic, can be replaced by ML later)
    income_from_bills = 0
    if total_bills <= 0:
        income_from_bills = 0
    elif total_bills <= 1000:
        income_from_bills = 6000
    elif total_bills <= 2000:
        income_from_bills = 10000
    elif total_bills <= 4000:
        income_from_bills = 16000
    else:
        income_from_bills = 25000

    # final income_est = max(personal_est, bill-based)
    final_income = max(personal_est, income_from_bills) if (personal_est or income_from_bills) else None
    ben.income_est = final_income

    # 5. Recompute income_category from income_est (same logic used elsewhere)
    base = float(final_income or 0)
    if base == 0:
        ben.income_category = None
    elif base < 10000:
        ben.income_category = "very low"
    elif base < 25000:
        ben.income_category = "low"
    elif base < 40000:
        ben.income_category = "lower medium"
    elif base < 75000:
        ben.income_category = "medium"
    elif base <= 100000:
        ben.income_category = "upper medium"
    else:
        ben.income_category = "high"

    # 6. Reset scoring fields: ML model will later update these
    ben.score = None
    ben.model_score = None
    ben.risk_band = None
    ben.need_band = None
    ben.eligibility_label = None
    ben.approval_flag = None
    ben.eligibility = "unknown"

    ben.save()


# ---------- Templates & Auth ----------

def login_page(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return redirect("home_page")
        else:
            return render(request, "login.html", {"error": "Invalid credentials"})
    return render(request, "login.html")



def user_login(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        role = request.POST.get("role") 

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            # redirect based on role
            if role == "officer":
                return redirect("/officer/dashboard-stats/")
            else:
                return redirect("/beneficiary/profile/")
        else:
            return render(request, "login.html", {"error": "Invalid credentials"})

    return render(request, "login.html")


#------------sign up for beneficiary----------
def beneficiary_register(request):
    if request.method == "POST":
        form = BeneficiaryRegisterForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            name = form.cleaned_data['name']
            age = form.cleaned_data['age']
            location = form.cleaned_data['location']
            gender = form.cleaned_data.get('gender')
            date_of_birth = form.cleaned_data.get('date_of_birth')
            phone = form.cleaned_data.get('phone')
            email = form.cleaned_data.get('email')
            consent_given = form.cleaned_data.get('consent_given')
            pincode = form.cleaned_data.get('pincode')

            # 1. Create Django User
            user = User.objects.create_user(username=username, password=password)
            if email:
                user.email = email
                user.save()

            # 2. Create Profile with role = beneficiary
            Profile.objects.create(user=user, role="beneficiary")

            # 3. Create Beneficiary entry
            Beneficiary.objects.create(
                user=user,
                name=name,
                age=age,
                gender=gender,
                date_of_birth=date_of_birth,
                phone=phone,
                email=email,
                location=location,
                income_est=0,
                estimated_monthly_income=0,
                score=0,
                risk_band="unknown",
                need_band="unknown",
                eligibility="unknown",
                consent_given=consent_given,
                pincode=pincode
            )

            # 4. Auto login
            login(request, user)

            # 5. Redirect to home
            return redirect("/beneficiary/profile/")
    else:
        form = BeneficiaryRegisterForm()

    return render(request, "beneficiary_register.html", {"form": form})



@login_required
def home_page(request):
    # Pass user profile info into template
    profile = getattr(request.user, "profile", None)
    return render(request, "home.html", {"user": request.user, "profile": profile})

def logout_view(request):
    logout(request)
    return redirect("login_page")

# ---------- Helpers ----------

def is_officer(user):
    profile = getattr(user, "profile", None)
    if profile and profile.role == "officer":
        return True
    return user.is_staff  # fallback: staff users are officers

# ---------- Officer endpoints ----------

@login_required
def officer_upload(request):
    if not is_officer(request.user):
        return HttpResponseForbidden("Officer access required")

    message = None
    error = None

    if request.method == "POST":
        uploaded_file = request.FILES.get("file")
        if not uploaded_file:
            error = "CSV file required."
        else:
            try:
                content = uploaded_file.read().decode("utf-8")
                reader = csv.DictReader(io.StringIO(content))
                added = 0
                for row in reader:
                    def _p_bool(val):
                        if val is None:
                            return False
                        v = str(val).strip().lower()
                        return v in ("1", "true", "yes", "y")

                    ben = Beneficiary.objects.create(
                        name=row.get("name") or "",
                        age=int(row["age"]) if row.get("age") else None,
                        location=row.get("location") or "",
                        state=row.get("state") or None,
                        district=row.get("district") or None,
                        pincode=row.get("pincode") or None,
                        phone=row.get("phone") or None,
                        income_est=float(row["income_est"]) if row.get("income_est") else None,
                        estimated_monthly_income=float(row["estimated_monthly_income"]) if row.get("estimated_monthly_income") else None,
                        consent_given=_p_bool(row.get("consent_given")),
                        aadhaar_verified=_p_bool(row.get("aadhaar_verified")),
                        pan_available=_p_bool(row.get("pan_available")),
                        bank_account_active=_p_bool(row.get("bank_account_active")),
                        employment_type=row.get("employment_type") or None,
                        officer=request.user,
                        created_at=timezone.now()
                    )
                    # compute income_category for uploaded record using the higher of the two fields
                    try:
                        v1 = float(ben.income_est) if ben.income_est is not None else 0.0
                    except Exception:
                        v1 = 0.0
                    try:
                        v2 = float(ben.estimated_monthly_income) if ben.estimated_monthly_income is not None else 0.0
                    except Exception:
                        v2 = 0.0
                    base = max(v1, v2)
                    if base < 10000:
                        ben.income_category = "very low"
                    elif base < 25000:
                        ben.income_category = "low"
                    elif base < 40000:
                        ben.income_category = "lower medium"
                    elif base < 75000:
                        ben.income_category = "medium"
                    elif base <= 100000:
                        ben.income_category = "upper medium"
                    else:
                        ben.income_category = "high"
                    ben.save()
                    # loan
                    if row.get("loan_amount"):
                        LoanHistory.objects.create(
                            beneficiary=ben,
                            amount=float(row.get("loan_amount", 0)),
                            tenure=int(row.get("tenure", 12)),
                            repayment_status=row.get("repayment_status", "Pending"),
                            created_at=timezone.now()
                        )
                    # consumption
                    if row.get("electricity_bill") or row.get("mobile_bill"):
                        ConsumptionData.objects.create(
                            beneficiary=ben,
                            electricity_bill=float(row["electricity_bill"]) if row.get("electricity_bill") else None,
                            mobile_bill=float(row["mobile_bill"]) if row.get("mobile_bill") else None,
                            other_bills=float(row["other_bills"]) if row.get("other_bills") else None,
                            created_at=timezone.now()
                        )
                    added += 1
                message = f"Successfully uploaded {added} beneficiaries"
            except Exception as e:
                logger.exception("Upload error")
                error = str(e)

    return render(request, "officer_upload.html", {
        "message": message,
        "error": error
    })


@login_required
@require_http_methods(["GET"])
def officer_beneficiaries(request):
    if not is_officer(request.user):
        return HttpResponseForbidden("Officer access required")
    qs = Beneficiary.objects.all().order_by("-created_at")[:1000]
    return render(request, "officer_beneficiaries.html", {
        "beneficiaries": qs
    })


@login_required
@require_http_methods(["POST"])
def officer_score(request, beneficiary_id):
    if not is_officer(request.user):
        return HttpResponseForbidden("Officer access required")
    ben = get_object_or_404(Beneficiary, pk=beneficiary_id)

    loans = list(ben.loans.all())
    consumption = ben.consumption_records.last()

    # Fallback scoring logic (same as earlier)
    try:
        score = 600
        paid_loans = sum(1 for loan in loans if loan.repayment_status == "Paid")
        score += paid_loans * 50
        risk_band = "Low Risk" if score > 650 else "High Risk"
        need_band = "High Need" if (ben.income_est or 0) < 50000 else "Low Need"
        eligibility = "Eligible" if score > 600 else "Not Eligible"

        ben.score = score
        ben.risk_band = risk_band
        ben.need_band = need_band
        ben.eligibility = eligibility
        ben.save()

        AIScoreLog.objects.create(
            beneficiary=ben,
            score=score,
            risk_band=risk_band,
            need_band=need_band,
            explanation="Fallback scoring algorithm used.",
            model_used="fallback",
            created_at=timezone.now()
        )

        return JsonResponse({"score": score, "risk_band": risk_band, "need_band": need_band, "eligibility": eligibility})
    except Exception as e:
        logger.exception("Scoring error")
        return JsonResponse({"detail": str(e)}, status=500)


@login_required
@require_http_methods(["GET"])
def officer_dashboard_stats(request):
    if not is_officer(request.user):
        return HttpResponseForbidden("Officer access required")
    all_b = Beneficiary.objects.all()
    total = all_b.count()
    scored = [b for b in all_b if b.score is not None]
    avg_score = sum(b.score for b in scored) / len(scored) if scored else 0
    high_risk = all_b.filter(risk_band="High Risk").count()
    low_risk = all_b.filter(risk_band="Low Risk").count()
    eligible = all_b.filter(eligibility="Eligible").count()

    ranges = [
        {"range": "300-400", "count": len([b for b in scored if 300 <= b.score < 400])},
        {"range": "400-500", "count": len([b for b in scored if 400 <= b.score < 500])},
        {"range": "500-600", "count": len([b for b in scored if 500 <= b.score < 600])},
        {"range": "600-700", "count": len([b for b in scored if 600 <= b.score < 700])},
        {"range": "700-800", "count": len([b for b in scored if 700 <= b.score < 800])},
        {"range": "800-900", "count": len([b for b in scored if 800 <= b.score <= 900])},
    ]

    return render(request, "officer_dashboard.html", {
        "total_beneficiaries": total,
        "average_score": round(avg_score, 2),
        "high_risk_count": high_risk,
        "low_risk_count": low_risk,
        "eligible_count": eligible,
        "score_distribution": ranges,
    })


@login_required
@require_http_methods(["GET"])
def get_ai_explanation(request, beneficiary_id):
    if not is_officer(request.user):
        return HttpResponseForbidden("Officer access required")
    ben = get_object_or_404(Beneficiary, pk=beneficiary_id)
    log = ben.ai_logs.all().order_by("-created_at").first()
    
    return render(request, "officer_ai_explanation.html", {
        "beneficiary": ben,
        "log": log
    })


@login_required
@require_http_methods(["GET"])
def officer_beneficiary_documents(request, beneficiary_id):
    """Allow officers to view documents uploaded by a beneficiary"""
    if not is_officer(request.user):
        return HttpResponseForbidden("Officer access required")
    
    ben = get_object_or_404(Beneficiary, pk=beneficiary_id)
    docs = BeneficiaryDocument.objects.filter(beneficiary=ben)
    
    return render(request, "officer_beneficiary_documents.html", {
        "beneficiary": ben,
        "documents": docs
    })


@login_required
@require_http_methods(["GET"])
def officer_beneficiary_details(request, beneficiary_id):
    """Show detailed beneficiary profile with all info for officer"""
    if not is_officer(request.user):
        return HttpResponseForbidden("Officer access required")
    
    ben = get_object_or_404(Beneficiary, pk=beneficiary_id)
    docs = BeneficiaryDocument.objects.filter(beneficiary=ben)
    loans = ben.loans.all()
    log = ben.ai_logs.all().order_by("-created_at").first()
    
    # Fetch case-specific details based on beneficiary's category
    case1_details = None
    case2_details = None
    case2_loans = None
    case3_details = None
    case3_loans = None
    case4_details = None
    case4_loans = None
    
    try:
        case1_details = ben.case1_details
    except Case1Details.DoesNotExist:
        pass
    
    try:
        case2_details = ben.case2_details
        case2_loans = case2_details.loans.all()
    except Case2Details.DoesNotExist:
        pass
    
    try:
        case3_details = ben.case3_details
        case3_loans = case3_details.loans.all()
    except Case3Details.DoesNotExist:
        pass
    
    try:
        case4_details = ben.case4_details
        case4_loans = case4_details.loans.all()
    except Case4Details.DoesNotExist:
        pass
    
    return render(request, "officer_beneficiary_details.html", {
        "beneficiary": ben,
        "documents": docs,
        "loans": loans,
        "ai_log": log,
        "case1_details": case1_details,
        "case2_details": case2_details,
        "case2_loans": case2_loans,
        "case3_details": case3_details,
        "case3_loans": case3_loans,
        "case4_details": case4_details,
        "case4_loans": case4_loans,
    })


# ---------- Beneficiary endpoints ----------

@login_required
@require_http_methods(["GET"])
def beneficiary_profile(request):
    profile = getattr(request.user, "profile", None)
    if not profile or profile.role != "beneficiary":
        return HttpResponseForbidden("Beneficiary access required")

    ben = Beneficiary.objects.filter(user=request.user).first()
    if not ben:
        return JsonResponse({"detail": "Profile not found"}, status=404)
    
    # Pass all beneficiary fields to template
    context = {
        "beneficiary": ben,
        # Basic info
        "id": str(ben.id),
        "name": ben.name,
        "age": ben.age,
        "gender": ben.gender,
        "date_of_birth": ben.date_of_birth,
        "phone": ben.phone,
        "email": ben.email,
        "location": ben.location,
        # CASE1 detailed fields
        "consent_given": ben.consent_given,
        "location_type": ben.location_type,
        "state": ben.state,
        "district": ben.district,
        "pincode": ben.pincode,
        "household_size": ben.household_size,
        "education_level": ben.education_level,
        "marital_status": ben.marital_status,
        "ration_card_type": ben.ration_card_type,
        "govt_subsidy_received": ben.govt_subsidy_received,
        # Verification flags
        "aadhaar_verified": ben.aadhaar_verified,
        "pan_available": ben.pan_available,
        "bank_account_active": ben.bank_account_active,
        # Financial
        "income_est": ben.income_est,
        "estimated_monthly_income": ben.estimated_monthly_income,
        "income_category": ben.income_category,
        "employment_type": ben.employment_type,
        "work_consistency_days": ben.work_consistency_days,
        # Decision & Scoring
        "eligibility_label": ben.eligibility_label,
        "model_score": ben.model_score,
        "approval_flag": ben.approval_flag,
        "score": ben.score,
        "risk_band": ben.risk_band,
        "need_band": ben.need_band,
        "eligibility": ben.eligibility,
        # Misc
        "other_details": ben.other_details,
    }
    return render(request, "beneficiary_home.html", context)


@login_required
@require_http_methods(["GET"])
def beneficiary_loans(request):
    profile = getattr(request.user, "profile", None)
    if not profile or profile.role != "beneficiary":
        return HttpResponseForbidden("Beneficiary access required")

    ben = Beneficiary.objects.filter(user=request.user).first()
    if not ben:
        return JsonResponse([], safe=False)
    loans = ben.loans.all().values("id", "amount", "tenure", "repayment_status", "created_at")
    return JsonResponse(list(loans), safe=False)


@login_required
@require_http_methods(["GET"])
def beneficiary_score(request):
    profile = getattr(request.user, "profile", None)
    if not profile or profile.role != "beneficiary":
        return HttpResponseForbidden("Beneficiary access required")
    ben = Beneficiary.objects.filter(user=request.user).first()
    if not ben:
        return JsonResponse({"detail": "Profile not found"}, status=404)
    return JsonResponse({
        "score": ben.score,
        "risk_band": ben.risk_band,
        "need_band": ben.need_band,
        "eligibility": ben.eligibility
    })


@login_required
@csrf_exempt
@require_http_methods(["POST"])
def beneficiary_calculate(request):
    profile = getattr(request.user, "profile", None)
    if not profile or profile.role != "beneficiary":
        return HttpResponseForbidden("Beneficiary access required")
    import json
    body = json.loads(request.body.decode("utf-8"))
    loan_amount = float(body.get("loan_amount", 0))
    tenure = int(body.get("tenure", 0))
    electricity_bill = float(body.get("electricity_bill", 0))
    mobile_bill = float(body.get("mobile_bill", 0))

    base_score = 600
    if loan_amount > 100000:
        base_score -= 20
    if tenure >= 24:
        base_score += 30
    elif tenure >= 12:
        base_score += 15
    total_bills = electricity_bill + mobile_bill
    if total_bills > 5000:
        base_score += 40
    elif total_bills > 2000:
        base_score += 20
    score = min(900, max(300, base_score))
    return JsonResponse({
        "estimated_score": score,
        "risk_band": "Low Risk" if score > 650 else "High Risk",
        "need_band": "High Need" if loan_amount > 50000 else "Low Need",
        "message": "This is an estimated score. Actual score may vary based on complete profile analysis."
    })



#----------edit beneficiary data-------
@login_required

def beneficiary_edit(request):
    if not request.user.is_authenticated:
        return redirect("/login/")

    profile = getattr(request.user, "profile", None)
    if not profile or profile.role != "beneficiary":
        return HttpResponseForbidden("Beneficiary access required")

    ben = Beneficiary.objects.filter(user=request.user).first()
    if not ben:
        return HttpResponseForbidden("Beneficiary profile not found")

    if request.method == "POST":
        form = BeneficiaryEditForm(request.POST)
        if form.is_valid():
            # ---------- Basic fields ----------
            ben.name = form.cleaned_data["name"]
            ben.age = form.cleaned_data["age"]
            ben.location = form.cleaned_data["location"]
            ben.gender = form.cleaned_data.get("gender")
            ben.date_of_birth = form.cleaned_data.get("date_of_birth")
            ben.phone = form.cleaned_data.get("phone")
            ben.email = form.cleaned_data.get("email")
            ben.pincode = form.cleaned_data.get("pincode")
            ben.location_type = form.cleaned_data.get("location_type")
            ben.state = form.cleaned_data.get("state")
            ben.district = form.cleaned_data.get("district")
            ben.household_size = form.cleaned_data.get("household_size")
            ben.education_level = form.cleaned_data.get("education_level")
            ben.marital_status = form.cleaned_data.get("marital_status")
            ben.ration_card_type = form.cleaned_data.get("ration_card_type")
            ben.govt_subsidy_received = form.cleaned_data.get("govt_subsidy_received", False)
            ben.aadhaar_verified = form.cleaned_data.get("aadhaar_verified", False)
            ben.pan_available = form.cleaned_data.get("pan_available", False)
            ben.bank_account_active = form.cleaned_data.get("bank_account_active", False)

            ben.estimated_monthly_income = form.cleaned_data.get("estimated_monthly_income")
            # recompute income_category (same as before)
            try:
                v1 = float(getattr(ben, "income_est", 0) or 0.0)
            except Exception:
                v1 = 0.0
            try:
                v2 = float(ben.estimated_monthly_income) if ben.estimated_monthly_income is not None else 0.0
            except Exception:
                v2 = 0.0
            base = max(v1, v2)
            if base < 10000:
                ben.income_category = "very low"
            elif base < 25000:
                ben.income_category = "low"
            elif base < 40000:
                ben.income_category = "lower medium"
            elif base < 75000:
                ben.income_category = "medium"
            elif base <= 100000:
                ben.income_category = "upper medium"
            else:
                ben.income_category = "high"

            ben.employment_type = form.cleaned_data.get("employment_type")
            ben.work_consistency_days = form.cleaned_data.get("work_consistency_days")

            # ---------- Critical fields ----------
            new_number_of_loans = form.cleaned_data.get("number_of_loans")
            new_emi_due_delays = form.cleaned_data.get("emi_due_delays")
            credit_card_choice = form.cleaned_data.get("credit_card")  # 'yes' / 'no'
            new_credit_card_available = True if credit_card_choice == "yes" else False
            new_cibil_score = form.cleaned_data.get("cibil_score")

            # Old values (may be None initially)
            old_number_of_loans = ben.number_of_loans
            old_emi_due_delays = ben.emi_due_delays
            old_credit_card_available = ben.credit_card_available
            old_cibil_score = ben.cibil_score

            # First time? -> all four are None
            first_time = (
                old_number_of_loans is None and
                old_emi_due_delays is None and
                old_credit_card_available is None and
                old_cibil_score is None
            )

            # Which fields actually changed?
            critical_changes = []
            if old_number_of_loans != new_number_of_loans:
                critical_changes.append("number_of_loans")
            if old_emi_due_delays != new_emi_due_delays:
                critical_changes.append("emi_due_delays")
            if old_credit_card_available != new_credit_card_available:
                critical_changes.append("credit_card_available")
            if old_cibil_score != new_cibil_score:
                critical_changes.append("cibil_score")

            change_reason = form.cleaned_data.get("change_reason", "").strip()

            # 🔒 If NOT first time and there are changes but no reason -> error
            if critical_changes and not first_time and not change_reason:
                form.add_error(
                    "change_reason",
                    "Please provide a reason for changing your loan/EMI/credit-card/CIBIL details."
                )
                return render(request, "beneficiary_edit.html", {"form": form, "beneficiary": ben})

            # Save reason if provided and changes happened
            if critical_changes and change_reason:
                ben.loans_dues_change_reason = change_reason

            # Save new critical values to model
            ben.number_of_loans = new_number_of_loans
            ben.emi_due_delays = new_emi_due_delays
            ben.credit_card_available = new_credit_card_available
            ben.cibil_score = new_cibil_score

            # ---------- Compute & store case_type ----------
            ben.case_type = ben.compute_case_type()

            ben.save()

            # Redirect based on stored case_type
            if ben.case_type == Beneficiary.CASE1:
                return redirect('case1_details')
            elif ben.case_type == Beneficiary.CASE2:
                return redirect('case2_details')
            elif ben.case_type == Beneficiary.CASE3:
                return redirect('case3_details')
            elif ben.case_type == Beneficiary.CASE4:
                return redirect('case4_details')
            else:
                # fallback: stay on page and show category text
                return render(
                    request,
                    "beneficiary_edit.html",
                    {"form": form, "beneficiary": ben, "category": "Uncategorized"}
                )

    else:
        # GET: prefill form with existing data
        form = BeneficiaryEditForm(initial={
            "name": ben.name,
            "age": ben.age,
            "location": ben.location,
            "gender": ben.gender,
            "date_of_birth": ben.date_of_birth,
            "phone": ben.phone,
            "email": ben.email,
            "pincode": ben.pincode,
            "location_type": ben.location_type,
            "state": ben.state,
            "district": ben.district,
            "household_size": ben.household_size,
            "education_level": ben.education_level,
            "marital_status": ben.marital_status,
            "ration_card_type": ben.ration_card_type,
            "govt_subsidy_received": ben.govt_subsidy_received,
            "aadhaar_verified": ben.aadhaar_verified,
            "pan_available": ben.pan_available,
            "bank_account_active": ben.bank_account_active,
            "employment_type": ben.employment_type,
            "work_consistency_days": ben.work_consistency_days,
            "estimated_monthly_income": ben.estimated_monthly_income,
            "number_of_loans": ben.number_of_loans or 0,
            "emi_due_delays": ben.emi_due_delays or 0,
            "credit_card": "yes" if ben.credit_card_available else "no",
            "cibil_score": ben.cibil_score,
            "change_reason": "",  # empty by default
        })

    return render(request, "beneficiary_edit.html", {"form": form, "beneficiary": ben})




#-----------Documents----------


@login_required
def upload_beneficiary_document(request):
    user = request.user
    beneficiary = get_object_or_404(Beneficiary, user=user)

    DOC_TYPES = [
        ("AADHAAR", "Aadhaar Card"),
        ("PAN", "PAN Card"),
        ("ELECTRICITY", "Electricity Bill"),
        ("MOBILE", "Mobile Bill"),
        ("RATION", "Ration Card"),
        ("PASSBOOK", "Bank Passbook"),
        ("OTHER", "Other Document"),
    ]

    if request.method == "POST":
        try:
            for dt, _label in DOC_TYPES:
                doc_num = request.POST.get(f"document_number_{dt}")
                file_obj = request.FILES.get(f"image_{dt}")

                if (doc_num and doc_num.strip()) or file_obj:
                    # create or update document
                    obj, created = BeneficiaryDocument.objects.get_or_create(
                        beneficiary=beneficiary,
                        doc_type=dt,
                        defaults={"document_number": doc_num or ""}
                    )
                    if doc_num:
                        obj.document_number = doc_num
                    if file_obj:
                        obj.image = file_obj
                    obj.save()

            # ✅ after uploading docs: auto-compute income & reset scoring
            auto_compute_income_from_details(beneficiary)

            # ✅ redirect to scoring (we use profile as scoring page)
            return redirect("beneficiary_profile")

        except Exception as e:
            logger.exception("Document upload error")

    # GET or error case: just render the upload page
    existing_docs = BeneficiaryDocument.objects.filter(beneficiary=beneficiary)
    existing_by_type = {d.doc_type: d for d in existing_docs}

    return render(
        request,
        "beneficiary_documents.html",
        {
            "beneficiary": beneficiary,
            "doc_types": DOC_TYPES,
            "existing_docs": existing_by_type,
        },
    )





@login_required
def beneficiary_documents(request):
    profile = getattr(request.user, "profile", None)
    if not profile or profile.role != "beneficiary":
        return HttpResponseForbidden("Beneficiary access required")

    ben = Beneficiary.objects.filter(user=request.user).first()
    if not ben:
        return JsonResponse({"detail": "Profile not found"}, status=404)

    docs = BeneficiaryDocument.objects.filter(beneficiary=ben)

    return render(request, "beneficiary_documents.html", {
        "beneficiary": ben,
        "documents": docs
    })





#---------income scoring---------


from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, render

def _get_bill_values_for_beneficiary(ben):
    """
    Try to fetch electricity, mobile, gas bill values from whichever
    case-details model exists for this beneficiary.
    """
    details = None
    for attr in ("case1_details", "case2_details", "case3_details", "case4_details"):
        try:
            d = getattr(ben, attr)
            if d:
                details = d
                break
        except Exception:
            continue

    if not details:
        return 0.0, 0.0, 0.0

    def safe_get(obj, *names):
        for name in names:
            if hasattr(obj, name):
                val = getattr(obj, name)
                if val is not None:
                    try:
                        return float(val)
                    except Exception:
                        pass
        return 0.0

    ele = safe_get(details, "electricity_bill", "electricity_amount")
    mob = safe_get(details, "average_mobile_bill", "mobile_bill", "mobile_recharge")
    gas = safe_get(details, "gas_bill", "gas_amount")
    return ele, mob, gas


@login_required
def case1_input(request):
    """
    Global income scoring for ALL beneficiaries.

    - No form.
    - Uses data already filled:
        - bills from case1/2/3/4 details
        - estimated_monthly_income from personal details
    - Computes score + income band (up to 1,00,000)
    - Updates Beneficiary
    - Shows result page
    """
    profile = getattr(request.user, "profile", None)
    if not profile or profile.role != "beneficiary":
        return HttpResponseForbidden("Beneficiary access required")

    ben = get_object_or_404(Beneficiary, user=request.user)

    # 1. Get bills
    ele, mob, gas = _get_bill_values_for_beneficiary(ben)
    uti = ele + mob + gas

    # 2. Scoring
    ele_score = 5 if ele <= 300 else 15 if ele <= 600 else 30
    mob_score = 5 if mob <= 100 else 15 if mob <= 200 else 25
    uti_score = 3 if uti <= 200 else 7 if uti <= 500 else 10
    total_score = ele_score + mob_score + uti_score

    # 3. Score → income band up to 1,00,000
    if total_score <= 20:
        income_band = "< 10,000"
        income_val = 8000
    elif total_score <= 40:
        income_band = "10,000 – 25,000"
        income_val = 18000
    elif total_score <= 60:
        income_band = "25,000 – 40,000"
        income_val = 32000
    elif total_score <= 80:
        income_band = "40,000 – 75,000"
        income_val = 55000
    else:
        income_band = "75,000 – 1,00,000"
        income_val = 90000

    # 4. Combine with personal estimated income
    personal_est = float(ben.estimated_monthly_income or 0)
    final_income = max(income_val, personal_est) if (income_val or personal_est) else None

    # 5. Update Beneficiary
    ben.score = total_score
    ben.income_est = final_income

    base = float(final_income or 0)
    if base == 0:
        ben.income_category = None
    elif base < 10000:
        ben.income_category = "very low"
    elif base < 25000:
        ben.income_category = "low"
    elif base < 40000:
        ben.income_category = "lower medium"
    elif base < 75000:
        ben.income_category = "medium"
    elif base <= 100000:
        ben.income_category = "upper medium"
    else:
        ben.income_category = "high"

    if total_score <= 20:
        ben.risk_band = "Low"
        ben.need_band = "High"
    elif total_score <= 40:
        ben.risk_band = "Medium"
        ben.need_band = "Medium"
    else:
        ben.risk_band = "High"
        ben.need_band = "High"

    ben.eligibility = True
    ben.save()

    return render(
        request,
        "income_scoring_result.html",  # or case1_result.html if you already have it
        {
            "total_score": total_score,
            "income": final_income,
            "income_band": income_band,
            "electricity_bill": ele,
            "mobile_bill": mob,
            "gas_bill": gas,
        },
    )




@login_required
def case1_details(request):
    ben = get_object_or_404(Beneficiary, user=request.user)

    if ben.case_type and ben.case_type != Beneficiary.CASE1:
        return HttpResponseForbidden("You are not allowed to access Case 1 details.")

    # Get existing details if they exist
    try:
        details = ben.case1_details
    except Exception:
        details = None

    if request.method == "POST":
        # Bind POST data
        form = Case1DetailsForm(request.POST, instance=details)

        if form.is_valid():
            obj = form.save(commit=False)
            obj.beneficiary = ben

            # Map yes/no to True/False if this field is still used
            pr = form.cleaned_data.get("payments_regularity")
            if pr == "yes":
                obj.payments_regularity = True
            elif pr == "no":
                obj.payments_regularity = False

            obj.save()

            # ✅ redirect ONLY after successful save
            return redirect("beneficiary_edit")

        else:
            # ❗ Do NOT redirect; fall through and re-render with errors
            print("CASE1 ERRORS:", form.errors)

    else:
        # GET request → show existing data or empty form
        form = Case1DetailsForm(instance=details)

    # ✅ In both GET and invalid POST, render template with the current form
    return render(request, "case1_details.html", {"form": form})


from .models import Case2Details  # make sure this import exists at the top

@login_required
def case2_details(request):
    ben = get_object_or_404(Beneficiary, user=request.user)
    if ben.case_type and ben.case_type != Beneficiary.CASE2:
        return HttpResponseForbidden("You are not allowed to access Case 2 details.")

    details, created = Case2Details.objects.get_or_create(beneficiary=ben)

    if request.method == "POST":
        form = Case2DetailsForm(request.POST, instance=details)

        if form.is_valid():
            obj = form.save(commit=False)
            obj.beneficiary = ben
            obj.save()
            return redirect("beneficiary_edit")
        print("CASE2 ERRORS:", form.errors)

    else:
        form = Case2DetailsForm(instance=details)
    return render(request, "case2_details.html", {"form": form})


@login_required
def case2_add_loan(request):
    profile = getattr(request.user, "profile", None)
    if not profile or profile.role != "beneficiary":
        return HttpResponseForbidden("Beneficiary access required")

    ben = Beneficiary.objects.filter(user=request.user).first()
    if not ben:
        return HttpResponseForbidden("Beneficiary profile not found")

    try:
        details = ben.case2_details
    except Case2Details.DoesNotExist:
        details = Case2Details.objects.create(beneficiary=ben)

    if request.method == 'POST':
        form = Case2LoanForm(request.POST)
        if form.is_valid():
            loan = form.save(commit=False)
            loan.case2 = details
            if not loan.loan_number:
                loan.loan_number = details.loans.count() + 1
            loan.save()
            return redirect('case2_details')
    else:
        initial = {'loan_number': details.loans.count() + 1}
        form = Case2LoanForm(initial=initial)

    return render(request, "case2_add_loan.html", {"form": form, "beneficiary": ben})


@login_required
def case3_details(request):
    ben = get_object_or_404(Beneficiary, user=request.user)
    if ben.case_type and ben.case_type != Beneficiary.CASE4:
        return HttpResponseForbidden("You are not allowed to access Case 4 details.")
    try:
        details = ben.case3_details
    except Exception:
        details = None

    if request.method == "POST":
        form = Case3DetailsForm(request.POST, instance=details)

        if form.is_valid():
            obj = form.save(commit=False)
            obj.beneficiary = ben
            obj.save()
        else:
            print("CASE3 ERRORS:", form.errors)
        return redirect("beneficiary_edit")
    form = Case3DetailsForm(instance=details)
    return render(request, "case3_details.html", {"form": form})



@login_required
def case3_add_loan(request):
    profile = getattr(request.user, "profile", None)
    if not profile or profile.role != "beneficiary":
        return HttpResponseForbidden("Beneficiary access required")

    ben = Beneficiary.objects.filter(user=request.user).first()
    if not ben:
        return HttpResponseForbidden("Beneficiary profile not found")

    try:
        details = ben.case3_details
    except Case3Details.DoesNotExist:
        details = Case3Details.objects.create(beneficiary=ben)

    if request.method == 'POST':
        form = Case3LoanForm(request.POST)
        if form.is_valid():
            loan = form.save(commit=False)
            loan.case3 = details
            if not loan.loan_number:
                loan.loan_number = details.loans.count() + 1
            loan.save()
            return redirect('case3_details')
    else:
        initial = {'loan_number': details.loans.count() + 1}
        form = Case3LoanForm(initial=initial)

    return render(request, "case3_add_loan.html", {"form": form, "beneficiary": ben})


@login_required
def case4_details(request):
    ben = get_object_or_404(Beneficiary, user=request.user)
    if ben.case_type and ben.case_type != Beneficiary.CASE4:
        return HttpResponseForbidden("You are not allowed to access Case 4 details.")
    try:
        details = ben.case4_details
    except Exception:
        details = None

    if request.method == "POST":
        form = Case4DetailsForm(request.POST, instance=details)

        if form.is_valid():
            obj = form.save(commit=False)
            obj.beneficiary = ben
            obj.save()
        else:
            print("CASE4 ERRORS:", form.errors)
        return redirect("beneficiary_edit")
    form = Case4DetailsForm(instance=details)
    return render(request, "case4_details.html", {"form": form})



@login_required
def case4_add_loan(request):
    profile = getattr(request.user, "profile", None)
    if not profile or profile.role != "beneficiary":
        return HttpResponseForbidden("Beneficiary access required")

    ben = Beneficiary.objects.filter(user=request.user).first()
    if not ben:
        return HttpResponseForbidden("Beneficiary profile not found")

    try:
        details = ben.case4_details
    except Case4Details.DoesNotExist:
        details = Case4Details.objects.create(beneficiary=ben)

    if request.method == 'POST':
        form = Case4LoanForm(request.POST)
        if form.is_valid():
            loan = form.save(commit=False)
            loan.case4 = details
            if not loan.loan_number:
                loan.loan_number = details.loans.count() + 1
            loan.save()
            return redirect('case4_details')
    else:
        initial = {'loan_number': details.loans.count() + 1}
        form = Case4LoanForm(initial=initial)

    return render(request, "case4_add_loan.html", {"form": form, "beneficiary": ben})


#----------Loan Application----------

@login_required
def beneficiary_apply_loan(request):
    profile = getattr(request.user, "profile", None)
    if not profile or profile.role != "beneficiary":
        return HttpResponseForbidden("Beneficiary access required")

    ben = Beneficiary.objects.filter(user=request.user).first()
    if not ben:
        return HttpResponseForbidden("Beneficiary profile not found")

    if request.method == "POST":
        loan_amount = request.POST.get("loan_amount")
        tenure_months = request.POST.get("tenure_months")
        phone = request.POST.get("phone")
        email = request.POST.get("email")

        # basic validation
        if not (loan_amount and tenure_months and phone and email):
            return render(request, "beneficiary_apply_loan.html", {
                "beneficiary": ben,
                "error": "All fields are required."
            })

        # Ensure mandatory documents are uploaded before allowing application
        required = ["AADHAAR", "PAN", "ELECTRICITY", "MOBILE"]
        missing = []
        display = {
            "AADHAAR": "Aadhaar",
            "PAN": "PAN",
            "ELECTRICITY": "Electricity Bill",
            "MOBILE": "Mobile Bill",
        }
        for dt in required:
            q = BeneficiaryDocument.objects.filter(beneficiary=ben, doc_type=dt).first()
            if not q or not q.image:
                missing.append(display.get(dt, dt))

        if missing:
            return render(request, "beneficiary_apply_loan.html", {
                "beneficiary": ben,
                "error": "Cannot apply: missing required documents: " + ", ".join(missing)
            })

        LoanApplication.objects.create(
            beneficiary=ben,
            loan_amount=loan_amount,
            tenure_months=tenure_months,
            phone=phone,
            email=email,
            status=LoanApplication.STATUS_PENDING,
        )

    return render(request, "beneficiary_loan_submitted.html", {
            "beneficiary": ben
        })

    # GET: show empty form (or you can prefill email/phone)
    return render(request, "beneficiary_apply_loan.html", {
        "beneficiary": ben
    })


#-------------loan request to the officer----------


@login_required
def officer_loan_applications(request):
    if not is_officer(request.user):
        return HttpResponseForbidden("Officer access required")

    apps = LoanApplication.objects.all().order_by("-created_at")

    return render(request, "officer_loan_applications.html", {
        "applications": apps
    })


@login_required
@require_http_methods(["POST"])
def officer_decide_loan(request, app_id):
    if not is_officer(request.user):
        return HttpResponseForbidden("Officer access required")

    app = get_object_or_404(LoanApplication, pk=app_id)

    decision = request.POST.get("decision")  # "approve" or "reject"
    notes = request.POST.get("notes", "")

    if decision == "approve":
        app.status = LoanApplication.STATUS_APPROVED
        # Optionally create LoanHistory when approved
        LoanHistory.objects.create(
            beneficiary=app.beneficiary,
            amount=float(app.loan_amount),
            tenure=app.tenure_months,
            repayment_status="Pending",
            created_at=timezone.now()
        )
    elif decision == "reject":
        app.status = LoanApplication.STATUS_REJECTED

    app.officer = request.user
    app.decision_notes = notes
    app.save()

    return redirect("officer_loan_applications")



@login_required
def income_scoring(request):
    """
    View used by path('income/scoring/').
    Calculates credit score for the logged-in beneficiary and shows a simple result page.
    """
    profile = getattr(request.user, "profile", None)
    if not profile or profile.role != "beneficiary":
        return HttpResponseForbidden("Beneficiary access required")

    ben = get_object_or_404(Beneficiary, user=request.user)

    score, band, label = compute_credit_score_for_beneficiary(ben)

    # You can either redirect to profile or render a result page.
    return render(
        request,
        "income_scoring_result.html",
        {
            "beneficiary": ben,
            "score": score,
            "risk_band": band,
            "eligibility_label": label,
        },
    )


def compute_credit_score_for_beneficiary(ben):
    """
    Simple rule-based credit score: 300–900.
    Uses whatever fields are available on the Beneficiary safely.
    """

    # --- Safely read attributes (0 if missing) ---
    ontime = getattr(ben, "on_time_payment_ratio_12m", None) or 0
    max_dpd = getattr(ben, "max_dpd", None) or 0
    missed = getattr(ben, "missed_emi_count_12m", None) or 0
    default_flag = bool(getattr(ben, "default_flag", False))
    cibil = getattr(ben, "cibil_score", None)
    dti = getattr(ben, "debt_to_income_ratio", None) or 0
    active_loans = getattr(ben, "number_of_active_loans", None) or 0
    income = getattr(ben, "estimated_monthly_income", None) or getattr(ben, "income_est", None) or 0
    avg_balance = getattr(ben, "average_bank_balance", None) or 0
    util_ratio = getattr(ben, "utility_bills_ontime_ratio", None) or 0
    digital_freq = getattr(ben, "digital_payments_frequency", None) or 0
    transactions = getattr(ben, "transactions_count", None) or 0
    fraud = bool(getattr(ben, "fraud_flag", False))
    hard6 = getattr(ben, "hard_inquiries_last_6_months", None) or 0
    emp_type = (getattr(ben, "employment_type", None) or "").lower()
    work_days = getattr(ben, "work_consistency_days", None) or 0
    years_business = getattr(ben, "years_in_business", None) or 0
    seasonal = bool(getattr(ben, "seasonal_business_flag", False))

    # ---------- 1. Repayment + CIBIL (0–100) ----------
    if default_flag:
        repay_score = 0
    else:
        if ontime >= 0.95:
            repay_score = 40
        elif ontime >= 0.80:
            repay_score = 25
        else:
            repay_score = 10

        if max_dpd > 90:
            repay_score -= 25
        elif max_dpd > 30:
            repay_score -= 15
        elif max_dpd > 0:
            repay_score -= 5

        if missed >= 3:
            repay_score -= 10

        repay_score = max(0, min(60, repay_score))

    cibil_part = 0
    if cibil is not None:
        if cibil >= 780:
            cibil_part = 40
        elif cibil >= 720:
            cibil_part = 30
        elif cibil >= 650:
            cibil_part = 20
        elif cibil >= 600:
            cibil_part = 10
        else:
            cibil_part = 0

    block_repayment = max(0, min(100, repay_score + cibil_part))

    # ---------- 2. Debt burden (0–100) ----------
    block_debt = 100
    if dti > 0.60:
        block_debt -= 50
    elif dti > 0.40:
        block_debt -= 30
    elif dti > 0.25:
        block_debt -= 15

    if active_loans > 5:
        block_debt -= 30
    elif active_loans > 3:
        block_debt -= 20
    elif active_loans > 1:
        block_debt -= 10

    block_debt = max(0, min(100, block_debt))

    # ---------- 3. Income & stability (0–100) ----------
    if income < 8000:
        inc_score = 10
    elif income < 15000:
        inc_score = 25
    elif income < 30000:
        inc_score = 40
    elif income < 60000:
        inc_score = 50
    else:
        inc_score = 60

    if emp_type in ("salaried", "government") and work_days >= 25:
        stab_score = 40
    elif emp_type in ("self-employed", "business") and years_business >= 3:
        stab_score = 30
    elif seasonal or work_days < 20:
        stab_score = 15
    else:
        stab_score = 20

    block_income = max(0, min(100, inc_score + stab_score))

    # ---------- 4. Banking & cashflow (0–100) ----------
    denom = float(income or 1.0)
    liquidity_ratio = avg_balance / denom

    if liquidity_ratio >= 1.0:
        liq_score = 40
    elif liquidity_ratio >= 0.5:
        liq_score = 30
    elif liquidity_ratio >= 0.2:
        liq_score = 20
    else:
        liq_score = 10

    if util_ratio >= 0.9:
        util_score = 40
    elif util_ratio >= 0.7:
        util_score = 25
    else:
        util_score = 10

    if digital_freq >= 15 and transactions >= 20:
        digi_score = 20
    elif digital_freq >= 5:
        digi_score = 10
    else:
        digi_score = 5

    block_bank = max(0, min(100, liq_score + util_score + digi_score))

    # ---------- 5. Flags & inquiries (0–100) ----------
    block_flags = 100
    if fraud:
        block_flags = 0
    else:
        if hard6 > 4:
            block_flags -= 40
        elif hard6 > 1:
            block_flags -= 20

    block_flags = max(0, min(100, block_flags))

    # ---------- 6. Weighted overall 0–100 ----------
    overall_0_100 = (
        0.35 * block_repayment +
        0.20 * block_debt +
        0.20 * block_income +
        0.15 * block_bank +
        0.10 * block_flags
    )

    credit_score = 300 + (overall_0_100 / 100.0) * 600
    credit_score = int(round(credit_score))

    # ---------- 7. Risk band ----------
    if credit_score >= 800:
        risk_band = "Very_Low_Risk"
    elif credit_score >= 750:
        risk_band = "Low_Risk"
    elif credit_score >= 700:
        risk_band = "Medium_Risk"
    elif credit_score >= 650:
        risk_band = "High_Risk"
    else:
        risk_band = "Very_High_Risk"

    # ---------- 8. Eligibility label ----------
    if risk_band in ("Very_Low_Risk", "Low_Risk"):
        eligibility_label = "Eligible_Auto"
    elif risk_band == "Medium_Risk":
        eligibility_label = "Eligible_Manual"
    else:
        eligibility_label = "Not_Eligible"

    # Save to model (fields you already have like model_score, risk_band, eligibility_label)
    if hasattr(ben, "model_score"):
        ben.model_score = credit_score
    if hasattr(ben, "risk_band"):
        ben.risk_band = risk_band
    if hasattr(ben, "eligibility_label"):
        ben.eligibility_label = eligibility_label

    ben.save()

    return credit_score, risk_band, eligibility_label



@login_required
def beneficiary_score(request):
    
    ben = get_object_or_404(Beneficiary, user=request.user)

    score, risk_band, eligibility_label = compute_credit_score_for_beneficiary(ben)

    return render(
        request,
        "beneficiary_score.html",   
        {
            "beneficiary": ben,
            "credit_score": score,
            "risk_band": risk_band,
            "eligibility_label": eligibility_label,
        },
    )


