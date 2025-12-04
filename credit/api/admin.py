from django.contrib import admin
from .models import (
    Profile, Beneficiary, LoanHistory, ConsumptionData,
    AIScoreLog, BeneficiaryDocument, LoanApplication
)
from django.contrib import admin
from .models import (
    Beneficiary,
    Profile,
    LoanApplication,
    CaseDetails,

)


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "role")


class BeneficiaryDocumentInline(admin.TabularInline):
    model = BeneficiaryDocument
    extra = 1


# ✅ MERGED BeneficiaryAdmin — only ONE registration
@admin.register(Beneficiary)
class BeneficiaryAdmin(admin.ModelAdmin):
    list_display = ("name", "user", "officer", "score", "eligibility", "created_at")
    search_fields = ("name", "user__username", "user__email")
    inlines = [BeneficiaryDocumentInline]


@admin.register(LoanHistory)
class LoanHistoryAdmin(admin.ModelAdmin):
    list_display = ("beneficiary", "amount", "tenure", "repayment_status", "created_at")


@admin.register(ConsumptionData)
class ConsumptionDataAdmin(admin.ModelAdmin):
    list_display = ("beneficiary", "electricity_bill", "mobile_bill", "created_at")


@admin.register(AIScoreLog)
class AIScoreLogAdmin(admin.ModelAdmin):
    list_display = ("beneficiary", "score", "model_used", "created_at")
    readonly_fields = ("created_at",)


@admin.register(BeneficiaryDocument)
class BeneficiaryDocumentAdmin(admin.ModelAdmin):
    list_display = ("beneficiary", "doc_type", "document_number", "uploaded_at")
    list_filter = ("doc_type",)
    search_fields = ("beneficiary__name", "document_number")


@admin.register(LoanApplication)
class LoanApplicationAdmin(admin.ModelAdmin):
    list_display = ("beneficiary", "loan_amount", "tenure_months", "status", "officer", "created_at")
    list_filter = ("status",)
    search_fields = ("beneficiary__name", "beneficiary__user__username", "email", "phone")


@admin.register(CaseDetails)
class CaseDetailsAdmin(admin.ModelAdmin):
    list_display = (
        "beneficiary",
        "case_type",
        "average_bank_balance",
        "number_of_active_loans",
        "total_emi_per_month",
        "number_of_due_delays",
        "number_of_active_loans",
        "total_emi_per_month",   
        "number_of_due_delays",
        "created_at",
    )
    list_filter = ("case_type",)
    search_fields = (
        "beneficiary__name",
        "beneficiary__phone_number",
        "beneficiary__aadhar_number",
    )

    