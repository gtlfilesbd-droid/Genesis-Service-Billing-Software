from django.db import migrations, models
import django.db.models.deletion


def assign_banks_to_first_company(apps, schema_editor):
    BillingBank = apps.get_model('billing', 'BillingBank')
    Company = apps.get_model('clients', 'Company')
    first = Company.objects.order_by('pk').first()
    if not first:
        return
    BillingBank.objects.filter(company__isnull=True).update(company_id=first.pk)


class Migration(migrations.Migration):

    dependencies = [
        ('clients', '0007_agreementtitlepreset'),
        ('billing', '0013_alter_bill_ait_amount_alter_bill_excluding_vat_ait_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='billingbank',
            name='company',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name='billing_banks',
                to='clients.company',
                help_text='Issuing company whose invoices use this profile. Default applies to bills for agreements with this company.',
            ),
        ),
        migrations.AlterModelOptions(
            name='billingbank',
            options={
                'ordering': ['company_id', '-is_default', 'label'],
                'verbose_name': 'Billing bank',
                'verbose_name_plural': 'Billing banks',
            },
        ),
        migrations.AlterField(
            model_name='billingbank',
            name='is_default',
            field=models.BooleanField(
                default=False,
                verbose_name='Default for new bills (this company)',
            ),
        ),
        migrations.RunPython(assign_banks_to_first_company, migrations.RunPython.noop),
    ]
