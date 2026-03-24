from django.urls import path

from .views import (
    ApplyJobView,
    AssistantChatView,
    AssistantRecommendationsView,
    JobDetailView,
    JobListView,
    JobSearchView,
    LoginView,
    MeView,
    RefreshView,
    RegisterView,
    SaveJobView,
    UserSavedJobsView,
)


urlpatterns = [
    path("auth/register", RegisterView.as_view(), name="auth-register"),
    path("auth/login", LoginView.as_view(), name="auth-login"),
    path("auth/refresh", RefreshView.as_view(), name="auth-refresh"),
    path("auth/me", MeView.as_view(), name="auth-me"),
    path("jobs", JobListView.as_view(), name="jobs-list"),
    path("jobs/<int:pk>", JobDetailView.as_view(), name="jobs-detail"),
    path("jobs/search", JobSearchView.as_view(), name="jobs-search"),
    path("jobs/save", SaveJobView.as_view(), name="jobs-save"),
    path("jobs/apply", ApplyJobView.as_view(), name="jobs-apply"),
    path("user/saved", UserSavedJobsView.as_view(), name="user-saved"),
    path("assistant/chat", AssistantChatView.as_view(), name="assistant-chat"),
    path("assistant/recommendations", AssistantRecommendationsView.as_view(), name="assistant-recommendations"),
]
