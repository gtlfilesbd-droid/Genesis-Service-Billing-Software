from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('billing', '0010_bill_status_trim'),
    ]

    operations = [
        migrations.AddField(
            model_name='bill',
            name='auto_generated',
            field=models.BooleanField(
                default=False,
                help_text='Created by period sync; invoice date follows maturity (Bill To + 1 day).',
            ),
        ),
    ]
