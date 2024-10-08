# Generated by Django 4.2.13 on 2024-06-05 14:10
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("cost_models", "0006_add_distribution_info"),
    ]

    operations = [
        migrations.RunSQL(
            sql="UPDATE cost_model SET distribution_info = to_jsonb(distribution_info) || jsonb '{\"network_unattributed\":true, \"storage_unattributed\":true}' WHERE source_type='OCP';",
            reverse_sql="UPDATE cost_model SET distribution_info = to_jsonb(distribution_info)  - '{network_unattributed,storage_unattributed}'::text[] WHERE source_type='OCP';",
        ),
    ]
