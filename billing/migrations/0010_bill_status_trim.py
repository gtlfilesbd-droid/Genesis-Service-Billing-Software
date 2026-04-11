from django.db import migrations, models


def forwards(apps, schema_editor):
    Bill = apps.get_model('billing', 'Bill')
    Bill.objects.filter(status__in=['draft', 'cancelled']).update(status='pending')


class Migration(migrations.Migration):

    dependencies = [
        ('billing', '0009_bill_workflow_status'),
    ]

    operations = [
        migrations.RunPython(forwards, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='bill',
            name='status',
            field=models.CharField(
                choices=[
                    ('pending', 'Pending'),
                    ('submitted', 'Submitted'),
                    ('paid', 'Paid'),
                ],
                default='pending',
                max_length=20,
            ),
        ),
    ]
