from decimal import Decimal, ROUND_HALF_UP

from django.db import migrations, models


def forwards_recalc_vat_ait(apps, schema_editor):
    Bill = apps.get_model('billing', 'Bill')
    q = Decimal('0.01')
    for b in Bill.objects.iterator():
        base = Decimal(str(b.subtotal or 0))
        vat = (base * Decimal('0.10')).quantize(q, ROUND_HALF_UP)
        ait = (base * Decimal('0.05')).quantize(q, ROUND_HALF_UP)
        tax = vat + ait
        Bill.objects.filter(pk=b.pk).update(
            project_base_value=base,
            vat_amount=vat,
            ait_amount=ait,
            excluding_vat_ait=tax,
            total_in_bdt=base + tax,
        )


class Migration(migrations.Migration):

    dependencies = [
        ('billing', '0004_bill_period_from_to'),
    ]

    operations = [
        migrations.AddField(
            model_name='bill',
            name='vat_amount',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=14, verbose_name='VAT (10%)'),
        ),
        migrations.AddField(
            model_name='bill',
            name='ait_amount',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=14, verbose_name='AIT (5%)'),
        ),
        migrations.AlterField(
            model_name='bill',
            name='excluding_vat_ait',
            field=models.DecimalField(
                decimal_places=2,
                default=0,
                help_text='VAT + AIT (15% of base)',
                max_digits=14,
                verbose_name='Total VAT & AIT',
            ),
        ),
        migrations.AlterField(
            model_name='bill',
            name='project_base_value',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=14, verbose_name='Base Value (BDT)'),
        ),
        migrations.RunPython(forwards_recalc_vat_ait, migrations.RunPython.noop),
    ]
