from django.urls import path

from . import views


app_name = "jobs"

urlpatterns = [
    path("search/", views.search, name="search"),
]

