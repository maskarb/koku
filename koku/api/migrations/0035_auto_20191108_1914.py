# Generated by Django 2.2.4 on 2019-11-08 19:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0034_provider_active'),
    ]

    operations = [
        migrations.AlterField(
            model_name='provider',
            name='active',
            field=models.BooleanField(default=True),
        ),
    ]
