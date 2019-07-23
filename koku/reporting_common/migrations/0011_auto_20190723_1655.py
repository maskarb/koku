# Generated by Django 2.2.1 on 2019-07-23 16:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('reporting_common', '0010_remove_costusagereportstatus_history'),
    ]

    operations = [
        migrations.AlterField(
            model_name='costusagereportstatus',
            name='report_name',
            field=models.CharField(max_length=128),
        ),
        migrations.AlterUniqueTogether(
            name='costusagereportstatus',
            unique_together={('manifest', 'report_name')},
        ),
    ]
