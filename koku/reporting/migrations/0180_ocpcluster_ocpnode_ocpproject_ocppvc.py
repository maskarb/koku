# Generated by Django 3.1.7 on 2021-05-18 12:49
import uuid

import django.db.models.deletion
from django.db import migrations
from django.db import models


class Migration(migrations.Migration):

    dependencies = [("api", "0045_update_django_migration_sequences"), ("reporting", "0179_matview_tags_hash")]

    operations = [
        migrations.CreateModel(
            name="OCPCluster",
            fields=[
                ("uuid", models.UUIDField(default=uuid.uuid4, primary_key=True, serialize=False)),
                ("cluster_id", models.TextField()),
                ("cluster_alias", models.TextField(null=True)),
                ("provider", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to="api.provider")),
            ],
            options={"db_table": "reporting_ocp_clusters"},
        ),
        migrations.CreateModel(
            name="OCPPVC",
            fields=[
                ("uuid", models.UUIDField(default=uuid.uuid4, primary_key=True, serialize=False)),
                ("persistent_volume", models.TextField()),
                ("persistent_volume_claim", models.TextField()),
                ("cluster", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to="reporting.ocpcluster")),
            ],
            options={"db_table": "reporting_ocp_pvcs"},
        ),
        migrations.CreateModel(
            name="OCPProject",
            fields=[
                ("uuid", models.UUIDField(default=uuid.uuid4, primary_key=True, serialize=False)),
                ("project", models.TextField()),
                ("cluster", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to="reporting.ocpcluster")),
            ],
            options={"db_table": "reporting_ocp_projects"},
        ),
        migrations.CreateModel(
            name="OCPNode",
            fields=[
                ("uuid", models.UUIDField(default=uuid.uuid4, primary_key=True, serialize=False)),
                ("node", models.TextField()),
                ("resource_id", models.TextField(null=True)),
                ("node_capacity_cpu_cores", models.DecimalField(decimal_places=2, max_digits=18, null=True)),
                ("cluster", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to="reporting.ocpcluster")),
            ],
            options={"db_table": "reporting_ocp_nodes"},
        ),
    ]
