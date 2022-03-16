# Generated by Django 3.2.12 on 2022-03-16 23:28
from django.db import migrations
from django.db import models


class Migration(migrations.Migration):

    dependencies = [("reporting", "0251_update_storageclass_charfields")]

    operations = [
        migrations.AlterField(
            model_name="ocpusagelineitemdailysummary",
            name="monthly_cost_type",
            field=models.TextField(
                choices=[("Node", "Node"), ("Cluster", "Cluster"), ("PVC", "PVC"), ("Tag", "Tag")], null=True
            ),
        ),
        migrations.RenameField(
            model_name="ocpusagelineitemdailysummary", old_name="monthly_cost_type", new_name="cost_type"
        ),
    ]
