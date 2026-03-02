from __future__ import annotations

from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import EmployerProfile, JobSeekerProfile, Role, User


@receiver(post_save, sender=User)
def ensure_role_profile(sender, instance: User, created: bool, **kwargs) -> None:
    if instance.role == Role.EMPLOYER:
        EmployerProfile.objects.get_or_create(
            user=instance, defaults={"company_name": instance.username}
        )
    elif instance.role == Role.JOB_SEEKER:
        JobSeekerProfile.objects.get_or_create(user=instance)
