# Generated by Django 3.1.13 on 2021-07-26 14:18
import pkgutil

from django.db import connection
from django.db import migrations
from django.db import models


def add_gcp_views(apps, schema_editor):
    """Create the GCP Materialized views from files."""
    version = "_20210721"
    views = {
        f"sql/views/{version}/reporting_gcp_compute_summary": [
            "",
            "_by_account",
            "_by_project",
            "_by_region",
            "_by_service",
        ],
        f"sql/views/{version}/reporting_gcp_cost_summary": [
            "",
            "_by_account",
            "_by_project",
            "_by_region",
            "_by_service",
        ],
        f"sql/views/{version}/reporting_gcp_storage_summary": [
            "",
            "_by_account",
            "_by_project",
            "_by_region",
            "_by_service",
        ],
        f"sql/views/{version}/reporting_gcp_database_summary": [""],
        f"sql/views/{version}/reporting_gcp_network_summary": [""],
    }
    for base_path, view_tuple in views.items():
        for view in view_tuple:
            view_sql = pkgutil.get_data("reporting.provider.gcp", f"{base_path}{view}{version}.sql")
            view_sql = view_sql.decode("utf-8")
            with connection.cursor() as cursor:
                cursor.execute(view_sql)


class Migration(migrations.Migration):

    dependencies = [("reporting", "0187_project_distribution")]

    operations = [
        migrations.RunSQL(
            "ALTER TABLE reporting_gcpcostentrylineitem_daily_summary ADD COLUMN invoice_month varchar(256) NULL;",
            state_operations=[
                migrations.AddField(
                    model_name="gcpcostentrylineitemdailysummary",
                    name="invoice_month",
                    field=models.CharField(blank=True, max_length=256, null=True),
                )
            ],
        ),
        migrations.RunPython(add_gcp_views),
    ]
