# Generated by Django 3.1.10 on 2021-06-03 16:31
from django.db import migrations
from django.db import models


class Migration(migrations.Migration):

    dependencies = [("reporting", "0181_partition_ocp_on_x_tables")]

    operations = [
        migrations.AlterModelOptions(name="ocpazurecostlineitemdailysummary", options={"managed": False}),
        migrations.AddField(model_name="partitionedtable", name="subpartition_col", field=models.TextField(null=True)),
        migrations.AddField(
            model_name="partitionedtable", name="subpartition_type", field=models.TextField(null=True)
        ),
    ]
