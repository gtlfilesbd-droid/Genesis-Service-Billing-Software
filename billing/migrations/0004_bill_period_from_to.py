# Generated manually

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('billing', '0003_bill_invoice_number'),
    ]

    operations = [
        migrations.AddField(
            model_name='bill',
            name='bill_period_from',
            field=models.DateField(blank=True, null=True, verbose_name='Bill From'),
        ),
        migrations.AddField(
            model_name='bill',
            name='bill_period_to',
            field=models.DateField(blank=True, null=True, verbose_name='Bill To'),
        ),
    ]
