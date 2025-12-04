from django.db import models
from django.contrib.auth.models import User
import uuid
from django import forms
from django.utils import timezone

ROLE_CHOICES = [
    ("beneficiary", "Beneficiary"),
    ("officer", "Officer"),
]





def generate_beneficiary_id():
    """
    Generate next beneficiary ID in sequence:
    BEN100000, BEN100001, BEN100002, ...
    """
    from api.models import Beneficiary  # local import to avoid circular import
    try:
        # Get the last beneficiary ordered by id (string, but fixed numeric width)
        last_ben = Beneficiary.objects.all().order_by("-id").first()
        if last_ben:
            # Extract number from id like "BEN100005" -> 100005
            num = int(last_ben.id.replace("BEN", ""))
            return f"BEN{num + 1:06d}"
        else:
            return "BEN100000"
    except Exception:
        # Fallback if anything goes wrong (e.g., DB not ready yet)
        return "BEN100000"


class Profile(models.Model):
    """
    One-to-one profile for each auth.User.
    Deleting the user will also delete the profile.
    """
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="profile",
    )
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default="beneficiary",
    )
    picture = models.URLField(blank=True, null=True)

    def __str__(self):
        return f"{self.user.username} ({self.role})"


class Beneficiary(models.Model):
    CASE1 = "CASE1"
    CASE2 = "CASE2"
    CASE3 = "CASE3"
    CASE4 = "CASE4"

    CASE_TYPE_CHOICES = [
        (CASE1, "Case 1"),
        (CASE2, "Case 2"),
        (CASE3, "Case 3"),
        (CASE4, "Case 4"),
    ]

    id = models.CharField(
        max_length=20,
        primary_key=True,
        default=generate_beneficiary_id,
        editable=False,
    )

    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="beneficiaries",
    )
    officer = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="uploaded_beneficiaries",
    )

    name = models.CharField(max_length=256)
    age = models.PositiveIntegerField(null=True, blank=True)

    GENDER_CHOICES = [
        ("male", "Male"),
        ("female", "Female"),
        ("other", "Other"),
    ]
    gender = models.CharField(
        max_length=10,
        choices=GENDER_CHOICES,
        null=True,
        blank=True,
    )

    date_of_birth = models.DateField(null=True, blank=True)
    phone = models.CharField(max_length=20, null=True, blank=True)
    email = models.EmailField(null=True, blank=True)

    location = models.CharField(max_length=256, blank=True)
    consent_given = models.BooleanField(default=False)
    location_type = models.CharField(
        max_length=50,
        blank=True,
        null=True,  # rural / urban
    )
    state = models.CharField(max_length=100, blank=True, null=True)
    district = models.CharField(max_length=100, blank=True, null=True)
    pincode = models.CharField(max_length=20, blank=True, null=True)
    household_size = models.PositiveIntegerField(null=True, blank=True)
    education_level = models.CharField(max_length=100, blank=True, null=True)
    marital_status = models.CharField(max_length=50, blank=True, null=True)
    ration_card_type = models.CharField(max_length=50, blank=True, null=True)
    govt_subsidy_received = models.BooleanField(default=False)
    aadhaar_verified = models.BooleanField(default=False)
    pan_available = models.BooleanField(default=False)
    bank_account_active = models.BooleanField(default=False)

    income_est = models.FloatField(null=True, blank=True)
    estimated_monthly_income = models.FloatField(null=True, blank=True)
    income_category = models.CharField(max_length=50, blank=True, null=True)
    employment_type = models.CharField(max_length=50, blank=True, null=True)
    work_consistency_days = models.PositiveIntegerField(null=True, blank=True)

    eligibility_label = models.CharField(max_length=50, blank=True, null=True)
    model_score = models.FloatField(null=True, blank=True)
    approval_flag = models.BooleanField(null=True, blank=True)
    other_details = models.JSONField(null=True, blank=True, default=dict)

    risk_band = models.CharField(max_length=50, blank=True, null=True)
    need_band = models.CharField(max_length=50, blank=True, null=True)
    score = models.FloatField(null=True, blank=True)
    eligibility = models.CharField(max_length=50, blank=True, null=True)

    # credit history fields
    number_of_loans = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Total number of loans",
    )
    emi_due_delays = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="No. of delayed EMIs",
    )
    credit_card_available = models.BooleanField(
        null=True,
        blank=True,
        help_text="Has credit card?",
    )
    cibil_score = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Reported CIBIL score",
    )

    case_type = models.CharField(
        max_length=10,
        choices=CASE_TYPE_CHOICES,
        null=True,
        blank=True,
        help_text="One of CASE1 / CASE2 / CASE3 / CASE4",
    )

    # Store reason when number_of_loans or emi_due_delays are changed
    loans_dues_change_reason = models.TextField(
        null=True,
        blank=True,
        help_text=(
            "Reason for changing number of loans or EMI due delays "
            "after first submission"
        ),
    )

    # OTP-related fields
    otp_code = models.CharField(max_length=6, null=True, blank=True)
    otp_created_at = models.DateTimeField(null=True, blank=True)
    is_phone_verified = models.BooleanField(default=False)

    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)



    def __str__(self):
        return f"{self.name} ({self.id})"
    
    def compute_case_type(self):
       
        n = self.number_of_loans or 0
        d = self.emi_due_delays or 0
    

    def generate_otp(self):
        import random
        self.otp_code = f"{random.randint(100000, 999999)}"
        self.otp_created_at = timezone.now()
        self.save(update_fields=["otp_code", "otp_created_at"])
        return self.otp_code

    
    def is_otp_valid(self, otp_input, expiry_minutes=5):
        if not self.otp_code or not otp_input:
            return False
        if str(self.otp_code) != str(otp_input).strip():
            return False
        if not self.otp_created_at:
            return False
        if timezone.now() > self.otp_created_at + timezone.timedelta(minutes=expiry_minutes):
            return False
        return True

def compute_case_type(self):
    n = self.number_of_loans or 0
    d = self.emi_due_delays or 0
    if n == 0 and d == 0:
        return self.CASE1
    if n == 0 and d > 0:
        return self.CASE4
    if n <= 3 and d <= 2:
        return self.CASE2
    if n > 3:
        return self.CASE3

    return None



# NEW UNIFIED MODEL
class CaseDetails(models.Model):
    """
    Unified details model for all case types (CASE1–CASE4).

    One row per Beneficiary, with all financial/utility fields.
    Fields that are not used for a given case-type will stay NULL/blank.
    """
    beneficiary = models.OneToOneField(
        Beneficiary,
        on_delete=models.CASCADE,
        related_name="case_details",
    )

    # Snapshot of which case this row is currently being used for
    case_type = models.CharField(
        max_length=10,
        choices=Beneficiary.CASE_TYPE_CHOICES,
        null=True,
        blank=True,
    )

    # ---- Utility bills ----
    electricity_units = models.PositiveIntegerField(null=True, blank=True)
    electricity_bill = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    payments_regularity = models.BooleanField(
        null=True,
        blank=True,
        help_text="Are payments regular? (Yes/No)",
    )
    average_mobile_bill = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    gas_bill = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    gas_frequency = models.CharField(max_length=50, null=True, blank=True)

    # ---- Employment / income behaviour ----
    employment_type = models.CharField(max_length=150, null=True, blank=True)
    working_days_per_month = models.PositiveIntegerField(null=True, blank=True)
    digital_payment_frequency = models.CharField(
        max_length=10,
        choices=[
            ("low", "Low"),
            ("medium", "Medium"),
            ("high", "High"),
        ],
        null=True,
        blank=True,
    )

    # ---- Banking ----
    average_bank_balance = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    cash_inflow = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    cash_outflow = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    transactions_per_month = models.PositiveIntegerField(null=True, blank=True)
    last_6_months_avg_bank_balance = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    number_of_active_loans = models.PositiveIntegerField(null=True, blank=True)

    # ---- Extra wealth / risk info (from Case3/4 union) ----
    total_properties_value = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    wealth_index = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    any_business = models.BooleanField(null=True, blank=True)
    insurance_coverage = models.BooleanField(null=True, blank=True)
    luxury_expenditures = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    outstanding_bank_balance = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    loan_purpose = models.CharField(max_length=256, null=True, blank=True)
    loan_history_cibil = models.TextField(null=True, blank=True)
    reasons_for_delay = models.TextField(null=True, blank=True)
    number_of_active_loans = models.PositiveIntegerField(
        null=True, blank=True
    )
    total_emi_per_month = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True
    )
    number_of_due_delays = models.PositiveIntegerField(
        null=True, blank=True
    )

    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"CaseDetails for {self.beneficiary.name} ({self.beneficiary.id})"




class LoanHistory(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    beneficiary = models.ForeignKey(Beneficiary, on_delete=models.CASCADE, related_name="loans")
    amount = models.FloatField()
    tenure = models.PositiveIntegerField()  # months
    repayment_status = models.CharField(max_length=50, default="Pending")
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Loan {self.amount} for {self.beneficiary.name}"

class ConsumptionData(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    beneficiary = models.ForeignKey(Beneficiary, on_delete=models.CASCADE, related_name="consumption_records")
    electricity_bill = models.FloatField(null=True, blank=True)
    mobile_bill = models.FloatField(null=True, blank=True)
    other_bills = models.FloatField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Consumption for {self.beneficiary.name}"

class AIScoreLog(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    beneficiary = models.ForeignKey(Beneficiary, on_delete=models.CASCADE, related_name="ai_logs")
    score = models.FloatField()
    risk_band = models.CharField(max_length=50)
    need_band = models.CharField(max_length=50)
    explanation = models.TextField()
    model_used = models.CharField(max_length=100, default="fallback")
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"AILog {self.score} for {self.beneficiary.name}"



class BeneficiaryDocument(models.Model):
    DOC_AADHAAR = "AADHAAR"
    DOC_PAN = "PAN"
    DOC_ELECTRICITY = "ELECTRICITY"
    DOC_MOBILE = "MOBILE"
    DOC_WATER = "WATER"
    DOC_GAS = "GAS"

    DOC_TYPE_CHOICES = [
        (DOC_AADHAAR, "Aadhaar Card"),
        (DOC_PAN, "PAN Card"),
        (DOC_ELECTRICITY, "Electricity Bill"),
        (DOC_MOBILE, "Mobile Bill"),
        (DOC_WATER, "Water Bill"),
        (DOC_GAS, "Gas Bill"),
    ]

    beneficiary = models.ForeignKey(
        Beneficiary,
        on_delete=models.CASCADE,
        related_name="documents"
    )
    doc_type = models.CharField(
        max_length=20,
        choices=DOC_TYPE_CHOICES
    )
    document_number = models.CharField(
        max_length=100,
        help_text="Aadhaar number / PAN number / consumer number / phone number etc."
    )
    image = models.ImageField(
        upload_to="beneficiary_docs/",
        null=True,
        blank=True,
        help_text="Scanned copy or photo of the document"
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("beneficiary", "doc_type")   # only one of each type per beneficiary

    def __str__(self):
        return f"{self.beneficiary.name} - {self.get_doc_type_display()}"
    




class LoanApplication(models.Model):
    STATUS_PENDING = "PENDING"
    STATUS_APPROVED = "APPROVED"
    STATUS_REJECTED = "REJECTED"

    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending"),
        (STATUS_APPROVED, "Approved"),
        (STATUS_REJECTED, "Rejected"),
    ]

    beneficiary = models.ForeignKey(
        Beneficiary,
        on_delete=models.CASCADE,
        related_name="loan_applications"
    )
    loan_amount = models.DecimalField(max_digits=12, decimal_places=2)
    tenure_months = models.IntegerField()
    phone = models.CharField(max_length=20)
    email = models.EmailField()
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING
    )
    officer = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="approved_loans"
    )
    decision_notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.beneficiary.name} - {self.loan_amount} ({self.status})"


