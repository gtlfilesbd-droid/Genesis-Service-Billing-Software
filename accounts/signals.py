from django.db.models.signals import post_save
from django.contrib.auth.models import User
from django.dispatch import receiver
from .models import UserProfile


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """If a profile already exists, keep it in sync when User is saved.

    Do not auto-create here: adding a user in Admin also saves the UserProfile
    inline, which would otherwise hit a duplicate OneToOne (user_id) insert.
    Orphan users get a profile on first request via context_processor / get_profile.
    """
    try:
        instance.profile.save()
    except UserProfile.DoesNotExist:
        pass
