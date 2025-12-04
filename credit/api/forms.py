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
    GENDER_CHOICES = [
        ("male", "Male"),
        ("female", "Female"),
        ("other", "Other"),
    ]
    gender = forms.ChoiceField(choices=GENDER_CHOICES, required=False)
    date_of_birth = forms.DateField(required=False, widget=forms.DateInput(attrs={"type": "date"}))
    phone = forms.CharField(max_length=20, required=True)
    email = forms.EmailField(required=False)
    consent_given = forms.BooleanField(required=True, label="I consent to data usage and verification")


from django import forms

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

    date_of_birth = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={"type": "date"})
    )
    phone = forms.CharField(max_length=20, required=False)
    pincode = forms.CharField(max_length=20, required=False)
    email = forms.EmailField(required=False)
    location_type = forms.CharField(
        max_length=50,
        required=False,
        label="Location Type (rural/urban)",
    )
    state = forms.CharField(max_length=100, required=False)
    district = forms.CharField(max_length=100, required=False)
    household_size = forms.IntegerField(required=False)

    EDUCATION_LEVEL_CHOICES = [
        ("no_formal_education", "No Formal Education"),
        ("primary_education", "Primary Education"),
        ("middle_school", "Middle School"),
        ("secondary_education", "Secondary Education (10+2)"),
        ("diploma_vocational", "Diploma / Vocational Training"),
        ("undergraduate", "Undergraduate Degree (Bachelor’s)"),
        ("postgraduate", "Postgraduate Degree (Master’s)"),
        ("doctorate", "Doctorate (PhD)"),
        ("post_doctoral", "Post-Doctoral Research"),
    ]
    education_level = forms.ChoiceField(
        choices=EDUCATION_LEVEL_CHOICES,
        required=False,
        label="Education Level",
    )

    MARITAL_STATUS_CHOICES = [
        ("married", "Married"),
        ("unmarried", "Unmarried"),
        ("divorced", "Divorced"),
    ]
    marital_status = forms.ChoiceField(
        choices=MARITAL_STATUS_CHOICES,
        required=False,
        label="Marital Status",
    )

    RATION_CARD_TYPE_CHOICES = [
        ("none", "No Ration Card"),
        ("apl", "APL Card"),
        ("bpl", "BPL Card"),
        ("aay", "Antyodaya (AAY) Card"),
        ("other", "Other"),
    ]
    ration_card_type = forms.ChoiceField(
        choices=RATION_CARD_TYPE_CHOICES,
        required=False,
        label="Ration Card Type",
    )

    GOVERNMENT_SUBSIDY_CHOICES = [
        ("no", "No"),
        ("yes", "Yes"),
    ]
    government_subsidy = forms.ChoiceField(
        choices=GOVERNMENT_SUBSIDY_CHOICES,
        required=False,
        label="Do you receive any government subsidy?",
    )


    EMPLOYMENT_TYPE_CHOICES = [
        ("unemployed", "Unemployed"),
        ("self_employed", "Self-employed"),
        ("private", "Private Sector Employee"),
        ("government", "Government Employee"),
        ("student", "Student"),
        ("retired", "Retired"),
        ("other", "Other"),
    ]
    employment_type = forms.ChoiceField(
        choices=EMPLOYMENT_TYPE_CHOICES,
        required=False,
        label="Employment Type",
    )

    # --- Loan / credit info ---
    work_consistency_days = forms.IntegerField(
        required=False,
        label="Work Consistency (Days/Month)"
    )
    number_of_loans = forms.IntegerField(
        required=True,
        label="Number of Loans"
    )
    emi_due_delays = forms.IntegerField(
        required=True,
        label="Number of EMI Due Delays"
    )
    credit_card = forms.ChoiceField(
        choices=[('no', 'No'), ('yes', 'Yes')],
        required=True,
        label="Do you have a credit card?"
    )
    cibil_score = forms.IntegerField(
        required=False,
        label="CIBIL Score (if credit card is Yes)"
    )

    change_reason = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={"rows": 3}),
        label="Reason for changing loan / EMI / credit-card / CIBIL details (if you changed them)"
    )


class BeneficiaryDocumentForm(forms.ModelForm):
    class Meta:
        model = BeneficiaryDocument
        fields = ["doc_type", "document_number", "image"]



from api.models import CaseDetails, Beneficiary  # at top of file if not already

class CaseDetailsForm(forms.ModelForm):
    payments_regularity = forms.NullBooleanField(
        required=False,
        widget=forms.Select(choices=[
            ('', 'Select'),
            ('true', 'Yes'),
            ('false', 'No'),
        ])
    )
    digital_payment_frequency = forms.ChoiceField(
        choices=[('low', 'Low'), ('medium', 'Medium'), ('high', 'High')],
        required=False
    )

    class Meta:
        model = CaseDetails
        fields = [
            # same union fields as the model
            'electricity_units', 'electricity_bill', 'payments_regularity',
            'average_mobile_bill', 'gas_bill', 'gas_frequency',
            'employment_type', 'working_days_per_month', 'digital_payment_frequency',
            'average_bank_balance', 'cash_inflow', 'cash_outflow',
            'transactions_per_month', 'last_6_months_avg_bank_balance',
            'number_of_active_loans', 'total_properties_value', 'wealth_index',
            'any_business', 'insurance_coverage', 'luxury_expenditures',
            'outstanding_bank_balance', 'loan_purpose', 'loan_history_cibil',
            'reasons_for_delay',
        ]

    # 👇 IMPORTANT: limit fields per case-type
    CASE_FIELD_MAP = {
        Beneficiary.CASE1: [
            'electricity_units', 'electricity_bill', 'payments_regularity',
            'average_mobile_bill', 'gas_bill', 'gas_frequency',
            'employment_type', 'working_days_per_month', 'digital_payment_frequency',
            'average_bank_balance', 'cash_inflow', 'cash_outflow',
            'transactions_per_month',
        ],
        Beneficiary.CASE2: [
            'electricity_units', 'electricity_bill', 'payments_regularity',
            'average_mobile_bill', 'gas_bill', 'gas_frequency',
            'employment_type', 'working_days_per_month', 'digital_payment_frequency',
            'average_bank_balance', 'cash_inflow', 'cash_outflow',
            'transactions_per_month', 'last_6_months_avg_bank_balance',
            'number_of_active_loans',
        ],
        Beneficiary.CASE3: [
            'electricity_units', 'electricity_bill', 'payments_regularity',
            'average_mobile_bill', 'gas_bill', 'gas_frequency',
            'employment_type', 'working_days_per_month', 'digital_payment_frequency',
            'average_bank_balance', 'cash_inflow', 'cash_outflow',
            'transactions_per_month', 'last_6_months_avg_bank_balance',
            'number_of_active_loans', 'total_properties_value', 'wealth_index',
            'any_business', 'insurance_coverage', 'luxury_expenditures',
            'outstanding_bank_balance', 'loan_purpose', 'loan_history_cibil',
        ],
        Beneficiary.CASE4: [
            'electricity_units', 'electricity_bill', 'payments_regularity',
            'average_mobile_bill', 'gas_bill', 'gas_frequency',
            'employment_type', 'working_days_per_month', 'digital_payment_frequency',
            'average_bank_balance', 'cash_inflow', 'cash_outflow',
            'transactions_per_month', 'last_6_months_avg_bank_balance',
            'number_of_active_loans', 'reasons_for_delay',
        ],
    }

    def __init__(self, *args, **kwargs):
        # we pass case_type from the view
        case_type = kwargs.pop("case_type", None)
        super().__init__(*args, **kwargs)

        # All fields optional
        for f in self.fields.values():
            f.required = False

        # If case_type known: disable + clear fields not relevant for that case
        if case_type in self.CASE_FIELD_MAP:
            allowed = set(self.CASE_FIELD_MAP[case_type])
            for name, field in self.fields.items():
                if name not in allowed:
                    field.widget.attrs["readonly"] = True
                    field.widget.attrs["disabled"] = True
                    field.required = False





