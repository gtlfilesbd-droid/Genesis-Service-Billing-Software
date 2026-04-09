from django.db import models
from django.contrib.auth.models import User


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    
    # Permissions
    can_add_client = models.BooleanField(default=False, verbose_name='Can Add Client')
    can_edit_client = models.BooleanField(default=False, verbose_name='Can Edit Client')
    can_delete_client = models.BooleanField(default=False, verbose_name='Can Delete Client')
    can_generate_bill = models.BooleanField(default=False, verbose_name='Can Generate Bill')
    can_edit_bill = models.BooleanField(default=False, verbose_name='Can Edit Bill')
    can_delete_bill = models.BooleanField(default=False, verbose_name='Can Delete Bill')
    can_view_reports = models.BooleanField(default=False, verbose_name='Can View Reports')
    can_export_reports = models.BooleanField(default=False, verbose_name='Can Export Reports')

    phone = models.CharField(max_length=20, blank=True, null=True)
    department = models.CharField(max_length=100, blank=True, null=True)
    profile_picture = models.ImageField(upload_to='profiles/', blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'User Profile'
        verbose_name_plural = 'User Profiles'

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} - Profile"
