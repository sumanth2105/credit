"""Alter api_loanhistory.beneficiary_id from uuid to varchar(20) and re-add FK."""

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0009_merge_20251130_1952'),
    ]

    operations = [
        # Drop foreign key if exists
        migrations.RunSQL(
            sql="ALTER TABLE api_loanhistory DROP CONSTRAINT IF EXISTS api_loanhistory_beneficiary_id_fkey",
            reverse_sql="SELECT 1",
        ),

        # Alter column type from uuid to varchar(20)
        migrations.RunSQL(
            sql="ALTER TABLE api_loanhistory ALTER COLUMN beneficiary_id TYPE varchar(20) USING beneficiary_id::text",
            reverse_sql="ALTER TABLE api_loanhistory ALTER COLUMN beneficiary_id TYPE uuid USING beneficiary_id::uuid",
        ),

        # Re-add foreign key constraint
        migrations.RunSQL(
            sql="ALTER TABLE api_loanhistory ADD CONSTRAINT api_loanhistory_beneficiary_id_fkey FOREIGN KEY (beneficiary_id) REFERENCES api_beneficiary(id) ON DELETE CASCADE",
            reverse_sql="ALTER TABLE api_loanhistory DROP CONSTRAINT IF EXISTS api_loanhistory_beneficiary_id_fkey",
        ),
    ]
