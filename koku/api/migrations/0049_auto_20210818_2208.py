# Generated by Django 3.1.13 on 2021-08-18 22:08
from django.db import migrations
from django.db import models


class Migration(migrations.Migration):

    dependencies = [("api", "0048_new_partition_manager_func")]

    operations = [
        migrations.AddField(model_name="provider", name="paused", field=models.BooleanField(default=False)),
        migrations.AddField(model_name="sources", name="paused", field=models.BooleanField(default=False)),
    ]
