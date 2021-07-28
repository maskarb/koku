# Generated by Django 3.1.12 on 2021-06-14 18:04
import pkgutil

from django.db import connection
from django.db import migrations


def add_ocp_cost_views(apps, schema_editor):
    """Create the OCP Materialized views from files."""
    version = "_20210615"
    views = {f"sql/views/{version}/reporting_ocp_cost_summary": ["_by_project"]}
    for base_path, view_tuple in views.items():
        for view in view_tuple:
            view_sql = pkgutil.get_data("reporting.provider.ocp", f"{base_path}{view}{version}.sql")
            view_sql = view_sql.decode("utf-8")
            with connection.cursor() as cursor:
                cursor.execute(view_sql)


class Migration(migrations.Migration):
    dependencies = [("reporting", "0186_partition_ocp_on_x_tables")]
    operations = [migrations.RunPython(add_ocp_cost_views)]
