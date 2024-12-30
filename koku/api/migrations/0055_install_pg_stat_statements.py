# Generated by Django 3.2.12 on 2022-03-22 14:33
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [("api", "0054_adding_oci_provider")]

    operations = [
        migrations.RunSQL(
            sql="create extension if not exists pg_stat_statements schema public;",
            reverse_sql="drop extension if exists pg_stat_statements",
        )
    ]
