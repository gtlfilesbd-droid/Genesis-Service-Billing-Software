from decimal import Decimal

from django.db import migrations, models


def seed_tax_settings(apps, schema_editor):
    BillingTaxSettings = apps.get_model('billing', 'BillingTaxSettings')
    BillingTaxSettings.objects.get_or_create(
        pk=1,
        defaults={'vat_percent': Decimal('10.00'), 'ait_percent': Decimal('5.00')},
    )


class Migration(migrations.Migration):

    dependencies = [
        ('billing', '0005_bill_vat_ait_amounts'),
    ]

    operations = [
        migrations.CreateModel(
            name='BillingTaxSettings',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                (
                    'vat_percent',
                    models.DecimalField(
                        decimal_places=2,
                        default=Decimal('10'),
                        help_text='Percent of base amount, e.g. 10 for 10%.',
                        max_digits=6,
                    ),
                ),
                (
                    'ait_percent',
                    models.DecimalField(
                        decimal_places=2,
                        default=Decimal('5'),
                        help_text='Percent of base amount, e.g. 5 for 5%.',
                        max_digits=6,
                    ),
                ),
            ],
            options={
                'verbose_name': 'Billing tax rates',
                'verbose_name_plural': 'Billing tax rates',
            },
        ),
        migrations.RunPython(seed_tax_settings, migrations.RunPython.noop),
        migrations.AddField(
            model_name='bill',
            name='vat_rate_percent',
            field=models.DecimalField(
                decimal_places=2, default=Decimal('10'), max_digits=6, verbose_name='VAT rate applied (%)'
            ),
        ),
        migrations.AddField(
            model_name='bill',
            name='ait_rate_percent',
            field=models.DecimalField(
                decimal_places=2, default=Decimal('5'), max_digits=6, verbose_name='AIT rate applied (%)'
            ),
        ),
    ]
