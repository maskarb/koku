# Generated by Django 3.1.13 on 2021-12-03 16:40
from django.db import migrations
from django.db import models


class Migration(migrations.Migration):

    dependencies = [("reporting", "0211_ocpaz_partables")]

    operations = [
        migrations.AlterField(
            model_name="azuremeter", name="meter_id", field=models.TextField(editable=False, unique=True)
        )
    ]
