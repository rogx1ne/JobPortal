from django.urls import path

from . import views


app_name = "applications"


urlpatterns = [
    path("apply/<int:job_id>/", views.apply_to_job, name="apply"),
    path("mine/", views.my_applications, name="my_applications"),
    path("job/<int:job_id>/applicants/", views.job_applicants, name="job_applicants"),
    path(
        "application/<int:application_id>/status/",
        views.update_application_status,
        name="update_status",
    ),
]

