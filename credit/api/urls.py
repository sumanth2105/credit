# api/urls.py
from django.urls import path
from api.views import beneficiary_register
from . import views

urlpatterns = [
    # templates / auth
    path("", views.login_page, name="login_page"),
    path('login/', views.user_login, name='login'),
    path("beneficiary/register/", views.beneficiary_register, name="beneficiary_register"),
    path("beneficiary/verify-otp/", views.beneficiary_verify_otp, name="beneficiary_verify_otp"),
    path("home/", views.home_page, name="home_page"),
    path("logout/", views.logout_view, name="logout"),

    # officer endpoints
    path("officer/upload/", views.officer_upload, name="officer_upload"),
    path("officer/beneficiaries/", views.officer_beneficiaries, name="officer_beneficiaries"),
    path("officer/beneficiary/<str:beneficiary_id>/", views.officer_beneficiary_details, name="officer_beneficiary_details"),
    path("officer/beneficiary/<str:beneficiary_id>/documents/", views.officer_beneficiary_documents, name="officer_beneficiary_documents"),
    path("officer/score/<str:beneficiary_id>/", views.officer_score, name="officer_score"),
    path("officer/dashboard-stats/", views.officer_dashboard_stats, name="officer_dashboard_stats"),
    path("officer/ai-explain/<str:beneficiary_id>/", views.get_ai_explanation, name="ai_explain"),

    # beneficiary endpoints
    path("beneficiary/profile/", views.beneficiary_profile, name="beneficiary_profile"),
    path("beneficiary/loans/", views.beneficiary_loans, name="beneficiary_loans"),
    path("beneficiary/score/", views.beneficiary_score, name="beneficiary_score"),
    path("beneficiary/calculate/", views.beneficiary_calculate, name="beneficiary_calculate"),
    path("beneficiary/edit/", views.beneficiary_edit, name="beneficiary_edit"),
    path("beneficiary/documents/", views.beneficiary_documents, name="beneficiary_documents"),
    path("beneficiary/upload-document/", views.upload_beneficiary_document, name="upload_document"),
    path("case/details/", views.case_details, name="case_details"),

    path(
        "beneficiary/sync-external/",
        views.sync_external_data,
        name="sync_external_data"
    ),


    path("case1/input/", views.case1_input, name="case1_input"),
    path("income/scoring/", views.income_scoring, name="income_scoring"),
     # Beneficiary loan apply
    path("beneficiary/apply-loan/", views.beneficiary_apply_loan, name="beneficiary_apply_loan"),

    # Officer loan application list & decision
    path("officer/loan-applications/", views.officer_loan_applications, name="officer_loan_applications"),
    path("officer/loan-applications/<int:app_id>/decide/", views.officer_decide_loan, name="officer_decide_loan"),

]
