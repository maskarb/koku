# Generated by Django 2.2.15 on 2020-08-31 23:03
import django.utils.timezone
from django.db import migrations
from django.db import models


class Migration(migrations.Migration):

    dependencies = [("api", "0026_provider_data_updated_timestamp")]

    operations = [
        migrations.AddField(
            model_name="customer",
            name="date_updated",
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        )
    ]
