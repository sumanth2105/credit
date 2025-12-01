# Migration to fix BeneficiaryDocument foreign key column type

from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):

    dependencies = [
        ('api', '0005_change_beneficiary_id_to_sequential'),
    ]

    operations = [
        # Recreate the foreign key to match the new Beneficiary id type
        migrations.AlterField(
            model_name='beneficiarydocument',
            name='beneficiary',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='documents', to='api.beneficiary'),
        ),
    ]
