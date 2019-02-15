# Generated by Django 2.1.7 on 2019-02-15 18:22

import django.contrib.postgres.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('reporting', '0033_auto_20190214_1637'),
    ]

    operations = [
        migrations.CreateModel(
            name='OCPStorageVolumeClaimLabelSummary',
            fields=[
                ('key', models.CharField(max_length=253, primary_key=True, serialize=False)),
                ('values', django.contrib.postgres.fields.ArrayField(base_field=models.CharField(max_length=253), size=None)),
            ],
            options={
                'db_table': 'reporting_ocpstoragevolumeclaimlabel_summary',
            },
        ),
        migrations.CreateModel(
            name='OCPStorageVolumeLabelSummary',
            fields=[
                ('key', models.CharField(max_length=253, primary_key=True, serialize=False)),
                ('values', django.contrib.postgres.fields.ArrayField(base_field=models.CharField(max_length=253), size=None)),
            ],
            options={
                'db_table': 'reporting_ocpstoragevolumelabel_summary',
            },
        ),
    ]
