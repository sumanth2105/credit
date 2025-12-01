from django.contrib import admin
from .models import (
    Profile, Beneficiary, LoanHistory, ConsumptionData,
    AIScoreLog, BeneficiaryDocument, LoanApplication
)
from .models import Case1Details, Case2Details, Case2Loan, Case3Details, Case3Loan
from .models import Case4Details, Case4Loan

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


@admin.register(Case1Details)
class Case1DetailsAdmin(admin.ModelAdmin):
    list_display = ("beneficiary", "electricity_units", "average_bank_balance", "created_at")
    search_fields = ("beneficiary__name",)


@admin.register(Case2Details)
class Case2DetailsAdmin(admin.ModelAdmin):
    list_display = ("beneficiary", "number_of_active_loans", "last_6_months_avg_bank_balance", "created_at")
    search_fields = ("beneficiary__name",)


@admin.register(Case2Loan)
class Case2LoanAdmin(admin.ModelAdmin):
    list_display = ("case2", "loan_number", "loan_amount", "emi", "last_emi_date")
    search_fields = ("case2__beneficiary__name",)


@admin.register(Case3Details)
class Case3DetailsAdmin(admin.ModelAdmin):
    list_display = ("beneficiary", "number_of_active_loans", "last_6_months_avg_bank_balance", "created_at")
    search_fields = ("beneficiary__name",)


@admin.register(Case3Loan)
class Case3LoanAdmin(admin.ModelAdmin):
    list_display = ("case3", "loan_number", "loan_amount", "emi", "last_emi_date")
    search_fields = ("case3__beneficiary__name",)


@admin.register(Case4Details)
class Case4DetailsAdmin(admin.ModelAdmin):
    list_display = ("beneficiary", "number_of_active_loans", "last_6_months_avg_bank_balance", "created_at")
    search_fields = ("beneficiary__name",)


@admin.register(Case4Loan)
class Case4LoanAdmin(admin.ModelAdmin):
    list_display = ("case4", "loan_number", "loan_amount", "emi", "last_emi_date")
    search_fields = ("case4__beneficiary__name",)
