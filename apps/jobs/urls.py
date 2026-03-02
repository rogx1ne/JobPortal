from django.urls import path

from . import views


app_name = "jobs"


urlpatterns = [
    path("", views.job_list, name="list"),
    path("<int:pk>/", views.job_detail, name="detail"),
    path("employer/", views.employer_job_list, name="employer_jobs"),
    path("employer/create/", views.job_create, name="create"),
    path("employer/<int:pk>/edit/", views.job_edit, name="edit"),
    path("employer/<int:pk>/delete/", views.job_delete, name="delete"),
]

