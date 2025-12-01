# Migration to change BeneficiaryDocument beneficiary_id column from UUID to CharField

from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):

    dependencies = [
        ('api', '0006_fix_beneficiary_document_fk'),
    ]

    operations = [
        # Remove foreign key constraint
        migrations.RemoveConstraint(
            model_name='beneficiarydocument',
            name=None,
        ) if False else migrations.RunSQL(
            sql="ALTER TABLE api_beneficiarydocument DROP CONSTRAINT IF EXISTS api_beneficiarydocument_beneficiary_id_fkey",
            reverse_sql="SELECT 1"  # No-op for reverse
        ),
        
        # Alter the column type from uuid to varchar
        migrations.RunSQL(
            sql="ALTER TABLE api_beneficiarydocument ALTER COLUMN beneficiary_id TYPE varchar(20) USING beneficiary_id::text",
            reverse_sql="ALTER TABLE api_beneficiarydocument ALTER COLUMN beneficiary_id TYPE uuid USING beneficiary_id::uuid"
        ),
        
        # Re-add the foreign key
        migrations.RunSQL(
            sql="ALTER TABLE api_beneficiarydocument ADD CONSTRAINT api_beneficiarydocument_beneficiary_id_fkey FOREIGN KEY (beneficiary_id) REFERENCES api_beneficiary(id) ON DELETE CASCADE",
            reverse_sql="ALTER TABLE api_beneficiarydocument DROP CONSTRAINT IF EXISTS api_beneficiarydocument_beneficiary_id_fkey"
        ),
    ]
