from django.db import migrations, models


def backfill_submitted_on(apps, schema_editor):
    Bill = apps.get_model('billing', 'Bill')
    qs = Bill.objects.filter(
        status__in=('submitted', 'paid'),
        submitted_on__isnull=True,
    )
    for row in qs.iterator():
        if row.updated_at:
            Bill.objects.filter(pk=row.pk).update(
                submitted_on=row.updated_at.date(),
            )


class Migration(migrations.Migration):

    dependencies = [
        ('billing', '0011_bill_auto_generated'),
    ]

    operations = [
        migrations.AddField(
            model_name='bill',
            name='submitted_on',
            field=models.DateField(blank=True, null=True, verbose_name='Submitted on'),
        ),
        migrations.RunPython(backfill_submitted_on, migrations.RunPython.noop),
    ]
