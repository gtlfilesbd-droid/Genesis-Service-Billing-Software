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

    can_access_dashboard = models.BooleanField(
        default=True,
        verbose_name='Can access dashboard',
        help_text='If off, user is sent to Bills after login and cannot open the dashboard.',
    )
    dashboard_show_financial_summary = models.BooleanField(
        default=True,
        verbose_name='Dashboard: financial summary',
        help_text='Clients count, monthly/total revenue, outstanding.',
    )
    dashboard_show_workflow_queues = models.BooleanField(
        default=True,
        verbose_name='Dashboard: workflow queue cards',
        help_text='Pending / Submitted / Paid shortcut cards.',
    )
    dashboard_show_activity = models.BooleanField(
        default=True,
        verbose_name='Dashboard: recent activity',
        help_text='Recent bills, submitted watch list, recent clients.',
    )
    can_submit_bill = models.BooleanField(
        default=True,
        verbose_name='Can submit bills (pending to submitted)',
        help_text='Send mature pending bills to the client; queue and bulk submit.',
    )
    can_mark_bill_paid = models.BooleanField(
        default=True,
        verbose_name='Can mark bills paid (submitted to paid)',
        help_text='Record payment on submitted bills; queue and bulk mark paid.',
    )

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


class AuditLog(models.Model):
    """Immutable log of sensitive dashboard actions (e.g. hard deletes) for admin review."""

    ACTION_DELETE = 'delete'

    ACTION_CHOICES = [
        (ACTION_DELETE, 'Delete'),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='audit_logs',
        verbose_name='User',
    )
    action = models.CharField(max_length=32, choices=ACTION_CHOICES, db_index=True)
    target_model = models.CharField(max_length=120, db_index=True, verbose_name='Object type')
    object_pk = models.CharField(max_length=64, verbose_name='Object ID')
    object_repr = models.CharField(max_length=500, blank=True, verbose_name='Description')
    ip_address = models.CharField(max_length=45, blank=True, verbose_name='IP address')
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Audit log'
        verbose_name_plural = 'Audit logs'

    def __str__(self):
        who = self.user.get_username() if self.user_id else '(unknown)'
        return f'{who} {self.action} {self.target_model} #{self.object_pk} @ {self.created_at}'
