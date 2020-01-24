# Generated by Django 2.2.9 on 2020-01-21 17:14

import django.contrib.postgres.fields
import django.contrib.postgres.fields.jsonb
import django.core.serializers.json
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    replaces = [('cost_models', '0001_initial'), ('cost_models', '0002_auto_20181205_1810'), ('cost_models', '0003_auto_20190213_2040'), ('cost_models', '0004_auto_20190301_1850'), ('cost_models', '0005_auto_20190422_1415'), ('cost_models', '0006_auto_20190531_1850'), ('cost_models', '0007_auto_20190613_0057'), ('cost_models', '0008_auto_20190812_1805'), ('cost_models', '0009_auto_20190823_1442'), ('cost_models', '0010_auto_20190827_1536'), ('cost_models', '0011_costmodelaudit'), ('cost_models', '0012_auto_20190905_1920'), ('cost_models', '0013_costmodel_markup'), ('cost_models', '0014_costmodelaudit_markup'), ('cost_models', '0015_auto_20190923_1410'), ('cost_models', '0016_auto_20190925_1545'), ('cost_models', '0017_auto_20191212_1835'), ('cost_models', '0018_auto_20200116_2048')]

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='CostModelAudit',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('operation', models.CharField(max_length=16)),
                ('audit_timestamp', models.DateTimeField()),
                ('provider_uuids', django.contrib.postgres.fields.ArrayField(base_field=models.UUIDField(), null=True, size=None)),
                ('uuid', models.UUIDField()),
                ('name', models.TextField()),
                ('description', models.TextField()),
                ('source_type', models.CharField(choices=[('AWS', 'AWS'), ('OCP', 'OCP'), ('Azure', 'Azure'), ('GCP', 'GCP'), ('AWS-local', 'AWS-local'), ('Azure-local', 'Azure-local'), ('GCP-local', 'GCP-local')], max_length=50)),
                ('created_timestamp', models.DateTimeField()),
                ('updated_timestamp', models.DateTimeField()),
                ('rates', django.contrib.postgres.fields.jsonb.JSONField(default=dict)),
                ('markup', django.contrib.postgres.fields.jsonb.JSONField(default=dict, encoder=django.core.serializers.json.DjangoJSONEncoder))
            ],
            options={
                'db_table': 'cost_model_audit',
            },
        ),


        migrations.CreateModel(
            name='CostModel',
            fields=[
                ('uuid', models.UUIDField(default=uuid.uuid4, primary_key=True, serialize=False)),
                ('name', models.TextField()),
                ('description', models.TextField()),
                ('source_type', models.CharField(choices=[('AWS', 'AWS'), ('OCP', 'OCP'), ('Azure', 'Azure'), ('GCP', 'GCP'), ('AWS-local', 'AWS-local'), ('Azure-local', 'Azure-local'), ('GCP-local', 'GCP-local')], max_length=50)),
                ('created_timestamp', models.DateTimeField(auto_now_add=True)),
                ('updated_timestamp', models.DateTimeField(auto_now=True)),
                ('rates', django.contrib.postgres.fields.jsonb.JSONField(default=dict)),
                ('markup', django.contrib.postgres.fields.jsonb.JSONField(default=dict, encoder=django.core.serializers.json.DjangoJSONEncoder)),
            ],
            options={
                'db_table': 'cost_model',
                'ordering': ['name'],
            },
        ),
        migrations.AddIndex(
            model_name='costmodel',
            index=models.Index(fields=['name'], name='name_idx'),
        ),
        migrations.AddIndex(
            model_name='costmodel',
            index=models.Index(fields=['source_type'], name='source_type_idx'),
        ),
        migrations.AddIndex(
            model_name='costmodel',
            index=models.Index(fields=['updated_timestamp'], name='updated_timestamp_idx'),
        ),


        migrations.RunSQL(
            sql="""
            CREATE OR REPLACE FUNCTION process_cost_model_audit() RETURNS TRIGGER AS $cost_model_audit$
                DECLARE
                    provider_uuids uuid[];
                BEGIN
                    --
                    -- Create a row in cost_model_audit to reflect the operation performed on cost_model,
                    -- make use of the special variable TG_OP to work out the operation.
                    --
                    IF (TG_OP = 'DELETE') THEN
                        provider_uuids := (SELECT array_agg(provider_uuid) FROM cost_model_map WHERE cost_model_id = OLD.uuid);
                        INSERT INTO cost_model_audit SELECT nextval('cost_model_audit_id_seq'), 'DELETE', now(), provider_uuids, OLD.*;
                        RETURN OLD;
                    ELSIF (TG_OP = 'UPDATE') THEN
                        provider_uuids := (SELECT array_agg(provider_uuid) FROM cost_model_map WHERE cost_model_id = NEW.uuid);
                        INSERT INTO cost_model_audit SELECT nextval('cost_model_audit_id_seq'), 'UPDATE', now(), provider_uuids, NEW.*;
                        RETURN NEW;
                    ELSIF (TG_OP = 'INSERT') THEN
                        provider_uuids := (SELECT array_agg(provider_uuid) FROM cost_model_map WHERE cost_model_id = NEW.uuid);
                        INSERT INTO cost_model_audit SELECT nextval('cost_model_audit_id_seq'), 'INSERT', now(), provider_uuids, NEW.*;
                        RETURN NEW;
                    END IF;
                    RETURN NULL; -- result is ignored since this is an AFTER trigger
                END;
            $cost_model_audit$ LANGUAGE plpgsql;

            CREATE TRIGGER cost_model_audit
            AFTER INSERT OR UPDATE OR DELETE ON cost_model
                FOR EACH ROW EXECUTE PROCEDURE process_cost_model_audit();
            """,
        ),


        migrations.CreateModel(
            name='CostModelMap',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('provider_uuid', models.UUIDField(editable=False)),
                ('cost_model', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='cost_models.CostModel')),
            ],
            options={
                'ordering': ['-id'],
                'unique_together': {('provider_uuid', 'cost_model')},
                'db_table': 'cost_model_map',
            },
        ),
    ]
