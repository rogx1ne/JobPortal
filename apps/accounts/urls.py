from django.contrib.auth import views as auth_views
from django.urls import path

from . import views
from .forms import BootstrapAuthenticationForm


app_name = "accounts"


urlpatterns = [
    path(
        "login/",
        auth_views.LoginView.as_view(
            template_name="accounts/login.html",
            authentication_form=BootstrapAuthenticationForm,
        ),
        name="login",
    ),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("register/", views.register, name="register"),
    path("register/employer/", views.register_employer, name="register_employer"),
    path("register/jobseeker/", views.register_job_seeker, name="register_jobseeker"),
    path("profile/jobseeker/", views.job_seeker_profile, name="jobseeker_profile"),
    path("profile/employer/", views.employer_profile, name="employer_profile"),
]
