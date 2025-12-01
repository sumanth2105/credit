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
    EDUCATION_LEVEL_CHOICES = [
        ("No Formal Education", "No Formal Education"),
        ("10th", "10th"),
        ("Higher Secondary (Class 11–12)", "Higher Secondary (Class 11–12)"),
        ("Diploma / ITI / Vocational", "Diploma / ITI / Vocational"),
        ("Undergraduate (Bachelor’s Degree)", "Undergraduate (Bachelor’s Degree)"),
        ("Postgraduate (Master’s Degree)", "Postgraduate (Master’s Degree)"),
        ("Professional Degree", "Professional Degree"),
        ("Doctorate / PhD", "Doctorate / PhD"),
        ("Other", "Other"),
    ]
    education_level = forms.ChoiceField(choices=EDUCATION_LEVEL_CHOICES, required=False)
    MARITAL_STATUS_CHOICES = [
        ("Married", "Married"),
        ("Unmarried", "Unmarried"),
    ]
    marital_status = forms.ChoiceField(choices=MARITAL_STATUS_CHOICES, required=False)
    ration_card_type = forms.CharField(max_length=50, required=False)
    govt_subsidy_received = forms.BooleanField(required=False, label="Government Subsidy Received")
    # Verification flags
    aadhaar_verified = forms.BooleanField(required=False, label="Aadhaar Verified")
    pan_available = forms.BooleanField(required=False, label="PAN Available")
    bank_account_active = forms.BooleanField(required=False, label="Bank Account Active")
    # Financial
    # `estimated_monthly_income` is editable by the beneficiary.
    # `income_est` (scoring estimate) remains system/officer-managed and is not editable here.
    estimated_monthly_income = forms.FloatField(required=False, label="Estimated Monthly Income")
    EMPLOYMENT_TYPE_CHOICES = [
        ("Self-Employed", "Self-Employed"),
        ("Government Employee", "Government Employee"),
        ("Central Government", "Central Government"),
        ("State Government", "State Government"),
        ("Public Sector Undertaking (PSU)", "Public Sector Undertaking (PSU)"),
        ("Private Sector Employee", "Private Sector Employee"),
        ("Casual / Daily Wage Worker", "Casual / Daily Wage Worker"),
        ("Skilled / Unskilled Worker", "Skilled / Unskilled Worker"),
        ("Gig Worker (Swiggy, Zomato, Uber, etc.)", "Gig Worker (Swiggy, Zomato, Uber, etc.)"),
        ("Home-Based Worker", "Home-Based Worker"),
        ("Agricultural Worker / Farmer", "Agricultural Worker / Farmer"),
    ]
    employment_type = forms.ChoiceField(choices=EMPLOYMENT_TYPE_CHOICES, required=False)
    work_consistency_days = forms.IntegerField(required=False, label="Work Consistency (Days/Month)")
    # Scoring & Decision (managed by system/officer; not editable by beneficiary)
    # New categorization fields
    number_of_loans = forms.IntegerField(required=True, label="Number of Loans")
    emi_due_delays = forms.IntegerField(required=True, label="Number of EMI Due Delays")
    credit_card = forms.ChoiceField(choices=[('no','No'),('yes','Yes')], required=True, label="Do you have a credit card?")
    cibil_score = forms.IntegerField(required=False, label="CIBIL Score (if credit card is Yes)")

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
