# Generated manually for AgreementTitlePreset

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('clients', '0006_agreement_agreement_with'),
    ]

    operations = [
        migrations.CreateModel(
            name='AgreementTitlePreset',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=255)),
                ('sort_order', models.PositiveIntegerField(default=0, help_text='Lower numbers appear first in the dropdown.')),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Agreement title (preset)',
                'verbose_name_plural': 'Agreement title presets',
                'ordering': ['sort_order', 'title'],
            },
        ),
    ]
