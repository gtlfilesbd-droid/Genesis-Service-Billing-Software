from django.db import migrations


def ensure_total_in_bdt_column(apps, schema_editor):
    """Older DBs may have billing_bill without total_in_bdt while migration 0001 is marked applied."""
    if schema_editor.connection.vendor != 'postgresql':
        return
    with schema_editor.connection.cursor() as cursor:
        cursor.execute(
            """
            ALTER TABLE billing_bill
            ADD COLUMN IF NOT EXISTS total_in_bdt NUMERIC(14, 2) DEFAULT 0 NOT NULL;
            """
        )
        cursor.execute(
            """
            SELECT 1 FROM information_schema.columns
            WHERE table_schema = current_schema()
              AND table_name = 'billing_bill'
              AND column_name = 'total_amount'
            """
        )
        if cursor.fetchone():
            cursor.execute(
                """
                UPDATE billing_bill
                SET total_in_bdt = COALESCE(total_amount, 0)
                WHERE total_in_bdt IS NULL OR total_in_bdt = 0;
                """
            )


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('billing', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(ensure_total_in_bdt_column, noop_reverse),
    ]
