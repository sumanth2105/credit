# Generated migration to change Beneficiary ID from UUID to sequential string

from django.db import migrations, models
import api.models

def migrate_beneficiary_ids(apps, schema_editor):
    """Convert existing UUID IDs to sequential BEN format"""
    Beneficiary = apps.get_model('api', 'Beneficiary')
    
    # Get all beneficiaries ordered by creation time
    beneficiaries = Beneficiary.objects.all().order_by('created_at')
    
    counter = 100000
    for ben in beneficiaries:
        ben.id_new = f"BEN{counter:06d}"
        ben.save(update_fields=['id_new'])
        counter += 1

class Migration(migrations.Migration):

    dependencies = [
        ('api', '0004_loanapplication'),
    ]

    operations = [
        # Step 1: Create a new temporary text field
        migrations.AddField(
            model_name='beneficiary',
            name='id_new',
            field=models.CharField(max_length=20, null=True, blank=True, unique=True),
        ),
        
        # Step 2: Data migration - generate new IDs for existing beneficiaries
        migrations.RunPython(
            code=migrate_beneficiary_ids,
            reverse_code=migrations.RunPython.noop,
        ),
        
        # Step 3: Make id_new non-nullable
        migrations.AlterField(
            model_name='beneficiary',
            name='id_new',
            field=models.CharField(max_length=20, unique=True),
        ),
        
        # Step 4: Remove old UUID id field and rename id_new to id
        migrations.RemoveField(
            model_name='beneficiary',
            name='id',
        ),
        
        migrations.RenameField(
            model_name='beneficiary',
            old_name='id_new',
            new_name='id',
        ),
        
        migrations.AlterField(
            model_name='beneficiary',
            name='id',
            field=models.CharField(max_length=20, primary_key=True, default=api.models.generate_beneficiary_id, editable=False),
        ),
    ]
