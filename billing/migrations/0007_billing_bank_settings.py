from django.db import migrations, models


def seed_bank_settings(apps, schema_editor):
    BillingBankSettings = apps.get_model('billing', 'BillingBankSettings')
    BillingBankSettings.objects.get_or_create(pk=1)


class Migration(migrations.Migration):

    dependencies = [
        ('billing', '0006_billing_tax_settings'),
    ]

    operations = [
        migrations.CreateModel(
            name='BillingBankSettings',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('bank_name', models.CharField(blank=True, max_length=255, verbose_name='Bank Name')),
                ('beneficiary', models.CharField(blank=True, max_length=255, verbose_name='Beneficiary')),
                ('bank_branch', models.CharField(blank=True, max_length=255, verbose_name='Branch')),
                ('bank_address_line1', models.CharField(blank=True, max_length=255, verbose_name='Address Line 1')),
                ('bank_address_line2', models.CharField(blank=True, max_length=255, verbose_name='Address Line 2')),
                ('account_number', models.CharField(blank=True, max_length=100, verbose_name='Account Number')),
                ('swift_code', models.CharField(blank=True, max_length=50, verbose_name='Swift Code')),
                ('branch_routing_code', models.CharField(blank=True, max_length=100, verbose_name='Branch Code (Routing)')),
                ('bin_number', models.CharField(blank=True, max_length=50, verbose_name='BIN')),
                ('tin_number', models.CharField(blank=True, max_length=50, verbose_name='TIN')),
            ],
            options={
                'verbose_name': 'Billing bank information',
                'verbose_name_plural': 'Billing bank information',
            },
        ),
        migrations.RunPython(seed_bank_settings, migrations.RunPython.noop),
    ]
