from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from .models import EmployerProfile, JobSeekerProfile, Role, User


class EmployerProfileInline(admin.StackedInline):
    model = EmployerProfile
    extra = 0
    can_delete = False


class JobSeekerProfileInline(admin.StackedInline):
    model = JobSeekerProfile
    extra = 0
    can_delete = False


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    fieldsets = DjangoUserAdmin.fieldsets + (
        ("Job Portal", {"fields": ("role", "created_at", "updated_at")}),
    )
    readonly_fields = ("created_at", "updated_at")
    list_display = ("username", "email", "role", "is_active", "is_staff")
    list_filter = ("role", "is_active", "is_staff")
    search_fields = ("username", "email", "first_name", "last_name")
    inlines = (EmployerProfileInline, JobSeekerProfileInline)

    def save_model(self, request, obj, form, change):
        if obj.is_superuser:
            obj.role = Role.ADMIN
        super().save_model(request, obj, form, change)


@admin.register(EmployerProfile)
class EmployerProfileAdmin(admin.ModelAdmin):
    list_display = ("company_name", "user", "created_at")
    search_fields = ("company_name", "user__username", "user__email")


@admin.register(JobSeekerProfile)
class JobSeekerProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "created_at")
    search_fields = ("user__username", "user__email")
