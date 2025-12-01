from django import forms
from api.models import BeneficiaryDocument, Beneficiary

class Case1Form(forms.Form):
    electricity_bill = forms.DecimalField(label="Electricity Bill")
    mobile_bill = forms.DecimalField(label="Mobile Bill")
    utility_bills = forms.DecimalField(label="Utility Bills")




class BeneficiaryRegisterForm(forms.Form):
    username = forms.CharField(max_length=150)
    password = forms.CharField(widget=forms.PasswordInput)
    name = forms.CharField(max_length=150)
    age = forms.IntegerField(required=False)
    location = forms.CharField(max_length=150)
    GENDER_CHOICES = [
        ("male", "Male"),
        ("female", "Female"),
        ("other", "Other"),
    ]
    gender = forms.ChoiceField(choices=GENDER_CHOICES, required=False)
    date_of_birth = forms.DateField(required=False, widget=forms.DateInput(attrs={"type": "date"}))
    # Minimal mandatory fields for registration
    consent_given = forms.BooleanField(required=True, label="I consent to data usage and verification")
    phone = forms.CharField(max_length=20, required=True)
    pincode = forms.CharField(max_length=20, required=True)
    email = forms.EmailField(required=False)


class BeneficiaryEditForm(forms.Form):
    name = forms.CharField(max_length=150)
    age = forms.IntegerField(required=False)
    location = forms.CharField(max_length=150, required=False)
    GENDER_CHOICES = [
        ("male", "Male"),
        ("female", "Female"),
        ("other", "Other"),
    ]
    gender = forms.ChoiceField(choices=GENDER_CHOICES, required=False)
    date_of_birth = forms.DateField(required=False, widget=forms.DateInput(attrs={"type": "date"}))
    phone = forms.CharField(max_length=20, required=False)
    pincode = forms.CharField(max_length=20, required=False)
    email = forms.EmailField(required=False)
    # Location & Residence
    location_type = forms.CharField(max_length=50, required=False, label="Location Type (rural/urban)")
    state = forms.CharField(max_length=100, required=False)
    district = forms.CharField(max_length=100, required=False)
    household_size = forms.IntegerField(required=False)
    # Socio-Economic
    ...
    work_consistency_days = forms.IntegerField(required=False, label="Work Consistency (Days/Month)")
    # New categorization fields (already there)
    number_of_loans = forms.IntegerField(required=True, label="Number of Loans")
    emi_due_delays = forms.IntegerField(required=True, label="Number of EMI Due Delays")
    credit_card = forms.ChoiceField(
        choices=[('no', 'No'), ('yes', 'Yes')],
        required=True,
        label="Do you have a credit card?"
    )
    cibil_score = forms.IntegerField(required=False, label="CIBIL Score (if credit card is Yes)")

    # 🔥 New: reason for changes
    change_reason = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={"rows": 3}),
        label="Reason for changing loan / EMI / credit-card / CIBIL details (if you changed them)"
    )


class BeneficiaryDocumentForm(forms.ModelForm):
    class Meta:
        model = BeneficiaryDocument
        fields = ["doc_type", "document_number", "image"]


class Case1DetailsForm(forms.ModelForm):
    payments_regularity = forms.NullBooleanField(
    required=False,
    widget=forms.Select(choices=[
        ('', 'Select'),
        ('true', 'Yes'),
        ('false', 'No'),
    ])
)

    digital_payment_frequency = forms.ChoiceField(choices=[('low','Low'),('medium','Medium'),('high','High')], required=False)

    class Meta:
        from api.models import Case1Details
        model = Case1Details
        fields = [
            'electricity_units', 'electricity_bill', 'payments_regularity',
            'average_mobile_bill', 'gas_bill', 'gas_frequency',
            'employment_type', 'working_days_per_month', 'digital_payment_frequency',
            'average_bank_balance', 'cash_inflow', 'cash_outflow', 'transactions_per_month'
        ]
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].required = False


class Case2DetailsForm(forms.ModelForm):
    payments_regularity = forms.NullBooleanField(
    required=False,
    widget=forms.Select(choices=[
        ('', 'Select'),
        ('true', 'Yes'),
        ('false', 'No'),
    ])
)
    digital_payment_frequency = forms.ChoiceField(choices=[('low','Low'),('medium','Medium'),('high','High')], required=False)

    class Meta:
        from api.models import Case2Details
        model = Case2Details
        fields = [
            'electricity_units', 'electricity_bill', 'payments_regularity',
            'average_mobile_bill', 'gas_bill', 'gas_frequency',
            'employment_type', 'working_days_per_month', 'digital_payment_frequency',
            'average_bank_balance', 'cash_inflow', 'cash_outflow', 'transactions_per_month',
            'last_6_months_avg_bank_balance', 'number_of_active_loans'
        ]
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].required = False


class Case2LoanForm(forms.ModelForm):
    class Meta:
        from api.models import Case2Loan
        model = Case2Loan
        fields = ['loan_number', 'loan_type', 'loan_amount', 'loan_sanction_date', 'tenure_months', 'emi', 'last_emi_date']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].required = False


class Case3DetailsForm(forms.ModelForm):
    payments_regularity = forms.NullBooleanField(
    required=False,
    widget=forms.Select(choices=[
        ('', 'Select'),
        ('true', 'Yes'),
        ('false', 'No'),
    ])
)
    digital_payment_frequency = forms.ChoiceField(choices=[('low','Low'),('medium','Medium'),('high','High')], required=False)

    class Meta:
        from api.models import Case3Details
        model = Case3Details
        fields = [
            'electricity_units', 'electricity_bill', 'payments_regularity',
            'average_mobile_bill', 'gas_bill', 'gas_frequency',
            'employment_type', 'working_days_per_month', 'digital_payment_frequency',
            'average_bank_balance', 'cash_inflow', 'cash_outflow', 'transactions_per_month',
            'last_6_months_avg_bank_balance', 'number_of_active_loans',
            'total_properties_value', 'wealth_index', 'any_business', 'insurance_coverage',
            'luxury_expenditures', 'outstanding_bank_balance', 'loan_purpose', 'loan_history_cibil'
        ]
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].required = False


class Case3LoanForm(forms.ModelForm):
    class Meta:
        from api.models import Case3Loan
        model = Case3Loan
        fields = ['loan_number', 'loan_type', 'loan_amount', 'loan_sanction_date', 'tenure_months', 'emi', 'last_emi_date', 'outstanding_bank_balance', 'loan_purpose', 'loan_history_cibil']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].required = False


class Case4DetailsForm(forms.ModelForm):
    payments_regularity = forms.NullBooleanField(
    required=False,
    widget=forms.Select(choices=[
        ('', 'Select'),
        ('true', 'Yes'),
        ('false', 'No'),
    ])
)
    digital_payment_frequency = forms.ChoiceField(choices=[('low','Low'),('medium','Medium'),('high','High')], required=False)

    class Meta:
        from api.models import Case4Details
        model = Case4Details
        fields = [
            'electricity_units', 'electricity_bill', 'payments_regularity',
            'average_mobile_bill', 'gas_bill', 'gas_frequency',
            'employment_type', 'working_days_per_month', 'digital_payment_frequency',
            'average_bank_balance', 'cash_inflow', 'cash_outflow', 'transactions_per_month',
            'last_6_months_avg_bank_balance', 'reasons_for_delay', 'number_of_active_loans'
        ]
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].required = False


class Case4LoanForm(forms.ModelForm):
    class Meta:
        from api.models import Case4Loan
        model = Case4Loan
        fields = ['loan_number', 'loan_type', 'loan_amount', 'loan_sanction_date', 'tenure_months', 'emi', 'last_emi_date']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].required = False
