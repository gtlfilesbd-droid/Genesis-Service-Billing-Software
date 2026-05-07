from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('clients', '0007_agreementtitlepreset'),
    ]

    operations = [
        migrations.AddField(
            model_name='agreement',
            name='vat_ait_excluded',
            field=models.BooleanField(
                default=False,
                help_text='If on, all bills for this agreement use 0% VAT and 0% AIT.',
                verbose_name='VAT and AIT Exclude',
            ),
        ),
    ]
