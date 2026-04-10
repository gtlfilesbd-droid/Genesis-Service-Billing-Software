# Generated manually

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('billing', '0002_ensure_total_in_bdt_column'),
    ]

    operations = [
        migrations.AddField(
            model_name='bill',
            name='invoice_number',
            field=models.CharField(
                blank=True,
                max_length=150,
                null=True,
                unique=True,
                verbose_name='Invoice Number',
            ),
        ),
    ]
