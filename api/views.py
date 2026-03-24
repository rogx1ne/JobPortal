from __future__ import annotations

from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from jobs.models import Application, Job, Profile, SavedJob
from services.assistant_service import generate_assistant_reply, get_assistant_recommendations
from services.search_service import hybrid_rank_jobs

from .serializers import (
    ApplyJobSerializer,
    AssistantChatSerializer,
    AssistantRecommendationSerializer,
    JobSerializer,
    ProfileUpdateSerializer,
    RegisterSerializer,
    SaveJobSerializer,
    SavedJobSerializer,
    UserSerializer,
)


def _parse_int(value: str | None) -> int | None:
    if not value:
        return None
    if not value.isdigit():
        return None
    return int(value)


class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]


class LoginView(TokenObtainPairView):
    permission_classes = [permissions.AllowAny]


class RefreshView(TokenRefreshView):
    permission_classes = [permissions.AllowAny]


class MeView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        Profile.objects.get_or_create(user=request.user)
        return Response(UserSerializer(request.user).data)

    def patch(self, request):
        profile, _ = Profile.objects.get_or_create(user=request.user)
        serializer = ProfileUpdateSerializer(profile, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(UserSerializer(request.user).data, status=status.HTTP_200_OK)


class JobListView(generics.ListAPIView):
    serializer_class = JobSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        queryset = Job.objects.filter(is_active=True).order_by("-posted_at", "-last_seen_at")

        q = self.request.query_params.get("q", "").strip()
        location = self.request.query_params.get("location", "").strip()
        role = self.request.query_params.get("role", "").strip()
        experience = self.request.query_params.get("experience", "").strip()
        salary_min = _parse_int(self.request.query_params.get("salary_min"))
        salary_max = _parse_int(self.request.query_params.get("salary_max"))

        if location:
            queryset = queryset.filter(location__icontains=location)
        if role:
            queryset = queryset.filter(role__icontains=role)
        if experience:
            queryset = queryset.filter(experience__icontains=experience)
        if salary_min is not None:
            queryset = queryset.filter(Q(salary_max__gte=salary_min) | Q(salary_min__gte=salary_min))
        if salary_max is not None:
            queryset = queryset.filter(Q(salary_min__lte=salary_max) | Q(salary_max__lte=salary_max))
        if q:
            queryset = queryset.filter(
                Q(title__icontains=q)
                | Q(company_name__icontains=q)
                | Q(description_snippet__icontains=q)
                | Q(role__icontains=q)
            )
        return queryset


class JobSearchView(JobListView):
    def get_queryset(self):
        q = self.request.query_params.get("q", "").strip()
        location = self.request.query_params.get("location", "").strip()
        role = self.request.query_params.get("role", "").strip()
        experience = self.request.query_params.get("experience", "").strip()
        limit = _parse_int(self.request.query_params.get("limit")) or 100
        limit = max(1, min(limit, 200))

        base_queryset = super().get_queryset()
        if not q:
            return base_queryset[:limit]

        candidates = base_queryset[: max(300, limit)]
        ranked = hybrid_rank_jobs(
            jobs=candidates,
            query=q,
            location=location,
            role=role,
            experience=experience,
            limit=limit,
        )
        return ranked


class JobDetailView(generics.RetrieveAPIView):
    serializer_class = JobSerializer
    permission_classes = [permissions.AllowAny]
    queryset = Job.objects.filter(is_active=True)


class SaveJobView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = SaveJobSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        job = get_object_or_404(Job, id=serializer.validated_data["job_id"], is_active=True)
        saved, _ = SavedJob.objects.get_or_create(user=request.user, job=job)
        return Response(SavedJobSerializer(saved).data, status=status.HTTP_201_CREATED)


class ApplyJobView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = ApplyJobSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        job = get_object_or_404(Job, id=serializer.validated_data["job_id"], is_active=True)
        application, _ = Application.objects.update_or_create(
            user=request.user,
            job=job,
            defaults={
                "status": serializer.validated_data.get("status", "applied"),
                "notes": serializer.validated_data.get("notes", ""),
            },
        )
        return Response(
            {
                "id": application.id,
                "job_id": job.id,
                "status": application.status,
                "applied_at": application.applied_at,
            },
            status=status.HTTP_201_CREATED,
        )


class UserSavedJobsView(generics.ListAPIView):
    serializer_class = SavedJobSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return SavedJob.objects.filter(user=self.request.user).select_related("job", "job__source")


class AssistantChatView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = AssistantChatSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        payload = generate_assistant_reply(
            user=request.user,
            message=serializer.validated_data["message"],
            job_id=serializer.validated_data.get("job_id"),
        )
        return Response(payload, status=status.HTTP_200_OK)


class AssistantRecommendationsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        serializer = AssistantRecommendationSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        recommendations = get_assistant_recommendations(
            user=request.user,
            query=serializer.validated_data.get("q", ""),
            limit=serializer.validated_data.get("limit", 10),
        )
        return Response({"recommendations": recommendations}, status=status.HTTP_200_OK)
