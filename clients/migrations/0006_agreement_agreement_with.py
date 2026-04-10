# Generated manually for Agreement.agreement_with

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('clients', '0005_company_model'),
    ]

    operations = [
        migrations.AddField(
            model_name='agreement',
            name='agreement_with',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name='agreements',
                to='clients.company',
                verbose_name='Agreement With',
            ),
        ),
    ]
