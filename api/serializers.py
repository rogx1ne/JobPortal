from __future__ import annotations

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from jobs.models import Application, Job, Profile, SavedJob


User = get_user_model()


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ("id", "username", "email", "password")

    def validate_password(self, value: str) -> str:
        validate_password(value)
        return value

    def create(self, validated_data: dict) -> User:
        user = User.objects.create_user(
            username=validated_data["username"],
            email=validated_data.get("email", ""),
            password=validated_data["password"],
        )
        Profile.objects.get_or_create(user=user)
        return user


class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ("full_name", "headline", "bio", "skills", "resume_url")


class ProfileUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ("full_name", "headline", "bio", "skills", "resume_url")


class UserSerializer(serializers.ModelSerializer):
    profile = ProfileSerializer()

    class Meta:
        model = User
        fields = ("id", "username", "email", "profile")


class JobSerializer(serializers.ModelSerializer):
    source = serializers.CharField(source="source.name", read_only=True)

    class Meta:
        model = Job
        fields = (
            "id",
            "title",
            "company_name",
            "location",
            "role",
            "experience",
            "salary_min",
            "salary_max",
            "salary_currency",
            "description_snippet",
            "source",
            "source_url",
            "posted_at",
        )


class SaveJobSerializer(serializers.Serializer):
    job_id = serializers.IntegerField(min_value=1)


class ApplyJobSerializer(serializers.Serializer):
    job_id = serializers.IntegerField(min_value=1)
    status = serializers.ChoiceField(choices=Application._meta.get_field("status").choices, required=False)
    notes = serializers.CharField(required=False, allow_blank=True)


class SavedJobSerializer(serializers.ModelSerializer):
    job = JobSerializer()

    class Meta:
        model = SavedJob
        fields = ("id", "created_at", "job")


class ApplicationSerializer(serializers.ModelSerializer):
    job = JobSerializer(read_only=True)

    class Meta:
        model = Application
        fields = ("id", "status", "notes", "applied_at", "job")


class AssistantChatSerializer(serializers.Serializer):
    message = serializers.CharField(max_length=2000)
    job_id = serializers.IntegerField(min_value=1, required=False)


class AssistantRecommendationSerializer(serializers.Serializer):
    q = serializers.CharField(max_length=255, required=False, allow_blank=True)
    limit = serializers.IntegerField(min_value=1, max_value=25, required=False)
