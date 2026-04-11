from django.db import migrations, models


def migrate_legacy_statuses(apps, schema_editor):
    Bill = apps.get_model('billing', 'Bill')
    Bill.objects.filter(status='unpaid').update(status='submitted')
    Bill.objects.filter(status='overdue').update(status='submitted')


class Migration(migrations.Migration):

    dependencies = [
        ('billing', '0008_billing_bank_profiles'),
    ]

    operations = [
        migrations.RunPython(migrate_legacy_statuses, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='bill',
            name='status',
            field=models.CharField(
                choices=[
                    ('draft', 'Draft'),
                    ('pending', 'Pending'),
                    ('submitted', 'Submitted'),
                    ('paid', 'Paid'),
                    ('cancelled', 'Cancelled'),
                ],
                default='draft',
                max_length=20,
            ),
        ),
    ]
