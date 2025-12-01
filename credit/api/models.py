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
    """Generate next beneficiary ID in sequence BEN100000, BEN100001, etc."""
    from api.models import Beneficiary
    try:
        # Get the last beneficiary
        last_ben = Beneficiary.objects.all().order_by('-id').first()
        if last_ben:
            # Extract number from id like "BEN100005" -> 100005
            num = int(last_ben.id.replace('BEN', ''))
            return f"BEN{num + 1:06d}"
        else:
            return "BEN100000"
    except:
        return "BEN100000"






class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default="beneficiary")
    picture = models.URLField(blank=True, null=True)

    def __str__(self):
        return f"{self.user.username} ({self.role})"
    


class Beneficiary(models.Model):
    id = models.CharField(max_length=20, primary_key=True, default=generate_beneficiary_id, editable=False)
    name = models.CharField(max_length=256)
    age = models.PositiveIntegerField(null=True, blank=True)
    GENDER_CHOICES = [
        ("male", "Male"),
        ("female", "Female"),
        ("other", "Other"),
    ]
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, null=True, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    phone = models.CharField(max_length=20, null=True, blank=True)
    email = models.EmailField(null=True, blank=True)
    location = models.CharField(max_length=256, blank=True)
    consent_given = models.BooleanField(default=False)
    location_type = models.CharField(max_length=50, blank=True, null=True)  # rural/urban
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
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="beneficiaries")
    officer = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="uploaded_beneficiaries")
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    case_type = models.CharField(
        max_length=10,
        null=True,
        blank=True,
        help_text="One of CASE1/CASE2/CASE3/CASE4"
    )
    case_type = models.CharField(
        max_length=10,
        null=True,
        blank=True,
        help_text="One of CASE1/CASE2/CASE3/CASE4"
    )

    # Store reason when number_of_loans or emi_due_delays are changed
    loans_dues_change_reason = models.TextField(
        null=True,
        blank=True,
        help_text="Reason for changing number of loans or EMI due delays after first submission"
    )


    def __str__(self):
        return f"{self.name} ({self.id})"

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


class Case1Details(models.Model):
    DIGITAL_FREQ_CHOICES = [
        ("low", "Low"),
        ("medium", "Medium"),
        ("high", "High"),
    ]

    beneficiary = models.OneToOneField(
        Beneficiary,
        on_delete=models.CASCADE,
        related_name="case1_details",
    )
    electricity_units = models.PositiveIntegerField(null=True, blank=True)
    electricity_bill = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    payments_regularity = models.BooleanField(null=True, blank=True, help_text="Are payments regular? (Yes/No)")
    average_mobile_bill = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    gas_bill = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    gas_frequency = models.CharField(max_length=50, null=True, blank=True)
    employment_type = models.CharField(max_length=150, null=True, blank=True)
    working_days_per_month = models.PositiveIntegerField(null=True, blank=True)
    digital_payment_frequency = models.CharField(max_length=10, choices=DIGITAL_FREQ_CHOICES, null=True, blank=True)
    average_bank_balance = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    cash_inflow = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    cash_outflow = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    transactions_per_month = models.PositiveIntegerField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Case1Details for {self.beneficiary.name} ({self.beneficiary.id})"


class Case2Details(models.Model):
    DIGITAL_FREQ_CHOICES = [
        ("low", "Low"),
        ("medium", "Medium"),
        ("high", "High"),
    ]

    beneficiary = models.OneToOneField(
        Beneficiary,
        on_delete=models.CASCADE,
        related_name="case2_details",
    )
    electricity_units = models.PositiveIntegerField(null=True, blank=True)
    electricity_bill = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    payments_regularity = models.BooleanField(null=True, blank=True, help_text="Are payments regular? (Yes/No)")
    average_mobile_bill = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    gas_bill = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    gas_frequency = models.CharField(max_length=50, null=True, blank=True)
    employment_type = models.CharField(max_length=150, null=True, blank=True)
    working_days_per_month = models.PositiveIntegerField(null=True, blank=True)
    digital_payment_frequency = models.CharField(max_length=10, choices=DIGITAL_FREQ_CHOICES, null=True, blank=True)
    average_bank_balance = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    cash_inflow = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    cash_outflow = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    transactions_per_month = models.PositiveIntegerField(null=True, blank=True)
    last_6_months_avg_bank_balance = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    number_of_active_loans = models.PositiveIntegerField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Case2Details for {self.beneficiary.name} ({self.beneficiary.id})"


class Case2Loan(models.Model):
    """Represents an active loan entry attached to a Case2Details record.

    Multiple `Case2Loan` objects can be associated with a `Case2Details` to represent
    loan1, loan2, etc.
    """
    case2 = models.ForeignKey(
        Case2Details,
        on_delete=models.CASCADE,
        related_name='loans'
    )
    loan_number = models.PositiveIntegerField(default=1, help_text="1 for loan1, 2 for loan2, etc.")
    loan_type = models.CharField(max_length=150, null=True, blank=True)
    loan_amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    loan_sanction_date = models.DateField(null=True, blank=True)
    tenure_months = models.PositiveIntegerField(null=True, blank=True)
    emi = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    last_emi_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['loan_number']

    def __str__(self):
        return f"Loan {self.loan_number} for {self.case2.beneficiary.name} - {self.loan_amount}"


class Case3Details(models.Model):
    """Detailed fields captured for beneficiaries classified as Case 3.

    Linked one-to-one with `Beneficiary` so you can access via
    `beneficiary.case3_details`.
    """
    DIGITAL_FREQ_CHOICES = [
        ("low", "Low"),
        ("medium", "Medium"),
        ("high", "High"),
    ]

    beneficiary = models.OneToOneField(
        Beneficiary,
        on_delete=models.CASCADE,
        related_name="case3_details",
    )
    electricity_units = models.PositiveIntegerField(null=True, blank=True)
    electricity_bill = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    payments_regularity = models.BooleanField(null=True, blank=True, help_text="Are payments regular? (Yes/No)")
    average_mobile_bill = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    gas_bill = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    gas_frequency = models.CharField(max_length=50, null=True, blank=True)
    employment_type = models.CharField(max_length=150, null=True, blank=True)
    working_days_per_month = models.PositiveIntegerField(null=True, blank=True)
    digital_payment_frequency = models.CharField(max_length=10, choices=DIGITAL_FREQ_CHOICES, null=True, blank=True)
    average_bank_balance = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    cash_inflow = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    cash_outflow = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    transactions_per_month = models.PositiveIntegerField(null=True, blank=True)
    last_6_months_avg_bank_balance = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    number_of_active_loans = models.PositiveIntegerField(null=True, blank=True)
    total_properties_value = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    wealth_index = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    any_business = models.BooleanField(null=True, blank=True)
    insurance_coverage = models.BooleanField(null=True, blank=True)
    luxury_expenditures = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    outstanding_bank_balance = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    loan_purpose = models.CharField(max_length=256, null=True, blank=True)
    loan_history_cibil = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Case3Details for {self.beneficiary.name} ({self.beneficiary.id})"


class Case3Loan(models.Model):
    """Loan entries attached to Case3Details. Multiple entries allowed."""
    case3 = models.ForeignKey(
        Case3Details,
        on_delete=models.CASCADE,
        related_name='loans'
    )
    loan_number = models.PositiveIntegerField(default=1, help_text="1 for loan1, 2 for loan2, etc.")
    loan_type = models.CharField(max_length=150, null=True, blank=True)
    loan_amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    loan_sanction_date = models.DateField(null=True, blank=True)
    tenure_months = models.PositiveIntegerField(null=True, blank=True)
    emi = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    last_emi_date = models.DateField(null=True, blank=True)
    outstanding_bank_balance = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    loan_purpose = models.CharField(max_length=256, null=True, blank=True)
    loan_history_cibil = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['loan_number']

    def __str__(self):
        return f"Case3 Loan {self.loan_number} for {self.case3.beneficiary.name} - {self.loan_amount}"


class Case4Details(models.Model):
    """Detailed fields captured for beneficiaries classified as Case 4.

    Linked one-to-one with `Beneficiary` so you can access via
    `beneficiary.case4_details`.
    """
    DIGITAL_FREQ_CHOICES = [
        ("low", "Low"),
        ("medium", "Medium"),
        ("high", "High"),
    ]

    beneficiary = models.OneToOneField(
        Beneficiary,
        on_delete=models.CASCADE,
        related_name="case4_details",
    )
    electricity_units = models.PositiveIntegerField(null=True, blank=True)
    electricity_bill = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    payments_regularity = models.BooleanField(null=True, blank=True, help_text="Are payments regular? (Yes/No)")
    average_mobile_bill = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    gas_bill = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    gas_frequency = models.CharField(max_length=50, null=True, blank=True)
    employment_type = models.CharField(max_length=150, null=True, blank=True)
    working_days_per_month = models.PositiveIntegerField(null=True, blank=True)
    digital_payment_frequency = models.CharField(max_length=10, choices=DIGITAL_FREQ_CHOICES, null=True, blank=True)
    average_bank_balance = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    cash_inflow = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    cash_outflow = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    transactions_per_month = models.PositiveIntegerField(null=True, blank=True)
    last_6_months_avg_bank_balance = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    reasons_for_delay = models.TextField(null=True, blank=True)
    number_of_active_loans = models.PositiveIntegerField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Case4Details for {self.beneficiary.name} ({self.beneficiary.id})"


class Case4Loan(models.Model):
    """Loan entries attached to Case4Details. Multiple entries allowed."""
    case4 = models.ForeignKey(
        Case4Details,
        on_delete=models.CASCADE,
        related_name='loans'
    )
    loan_number = models.PositiveIntegerField(default=1, help_text="1 for loan1, 2 for loan2, etc.")
    loan_type = models.CharField(max_length=150, null=True, blank=True)
    loan_amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    loan_sanction_date = models.DateField(null=True, blank=True)
    tenure_months = models.PositiveIntegerField(null=True, blank=True)
    emi = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    last_emi_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['loan_number']

    def __str__(self):
        return f"Case4 Loan {self.loan_number} for {self.case4.beneficiary.name} - {self.loan_amount}"
