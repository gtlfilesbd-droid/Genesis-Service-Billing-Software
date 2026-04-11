from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='can_access_dashboard',
            field=models.BooleanField(
                default=True,
                help_text='If off, user is sent to Bills after login and cannot open the dashboard.',
                verbose_name='Can access dashboard',
            ),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='dashboard_show_financial_summary',
            field=models.BooleanField(
                default=True,
                help_text='Clients count, monthly/total revenue, outstanding.',
                verbose_name='Dashboard: financial summary',
            ),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='dashboard_show_workflow_queues',
            field=models.BooleanField(
                default=True,
                help_text='Pending / Submitted / Paid shortcut cards.',
                verbose_name='Dashboard: workflow queue cards',
            ),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='dashboard_show_activity',
            field=models.BooleanField(
                default=True,
                help_text='Recent bills, submitted watch list, recent clients.',
                verbose_name='Dashboard: recent activity',
            ),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='can_submit_bill',
            field=models.BooleanField(
                default=True,
                help_text='Send mature pending bills to the client; queue and bulk submit.',
                verbose_name='Can submit bills (pending to submitted)',
            ),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='can_mark_bill_paid',
            field=models.BooleanField(
                default=True,
                help_text='Record payment on submitted bills; queue and bulk mark paid.',
                verbose_name='Can mark bills paid (submitted to paid)',
            ),
        ),
    ]
