# Generated by Django 2.2.10 on 2020-02-28 17:34
import django.contrib.postgres.indexes
from django.db import migrations
from django.db import models


class Migration(migrations.Migration):

    dependencies = [("reporting", "0099_ocp_performance")]

    operations = [
        migrations.RunSQL(
            # Got to drop these views as we are changing the type of a selected column
            # They will be recreated below
            sql="""
DROP INDEX IF EXISTS aws_cost_summary;
DROP MATERIALIZED VIEW IF EXISTS reporting_aws_cost_summary;

DROP INDEX IF EXISTS aws_cost_summary_service;
DROP MATERIALIZED VIEW IF EXISTS reporting_aws_cost_summary_by_service;

DROP INDEX IF EXISTS aws_cost_summary_account;
DROP MATERIALIZED VIEW IF EXISTS reporting_aws_cost_summary_by_account;

DROP INDEX IF EXISTS aws_cost_summary_region;
DROP MATERIALIZED VIEW IF EXISTS reporting_aws_cost_summary_by_region;

DROP INDEX IF EXISTS aws_storage_summary;
DROP MATERIALIZED VIEW IF EXISTS reporting_aws_storage_summary;

DROP INDEX IF EXISTS aws_storage_summary_service;
DROP MATERIALIZED VIEW IF EXISTS reporting_aws_storage_summary_by_service;

DROP INDEX IF EXISTS aws_storage_summary_account;
DROP MATERIALIZED VIEW IF EXISTS reporting_aws_storage_summary_by_account;

DROP INDEX IF EXISTS aws_storage_summary_region;
DROP MATERIALIZED VIEW IF EXISTS reporting_aws_storage_summary_by_region;

DROP INDEX IF EXISTS aws_network_summary;
DROP MATERIALIZED VIEW IF EXISTS reporting_aws_network_summary;

DROP INDEX IF EXISTS aws_database_summary;
DROP MATERIALIZED VIEW IF EXISTS reporting_aws_database_summary;

DROP INDEX IF EXISTS ocpallcstdlysumm_node;
DROP INDEX IF EXISTS ocpallcstdlysumm_node_like;
DROP INDEX IF EXISTS ocpallcstdlysumm_nsp;
DROP MATERIALIZED VIEW IF EXISTS reporting_ocpallcostlineitem_daily_summary;

DROP INDEX IF EXISTS ocpallcstprjdlysumm_node;
DROP INDEX IF EXISTS ocpallcstprjdlysumm_nsp;
DROP INDEX IF EXISTS ocpallcstprjdlysumm_node_like;
DROP INDEX IF EXISTS ocpallcstprjdlysumm_nsp_like;
DROP MATERIALIZED VIEW IF EXISTS reporting_ocpallcostlineitem_project_daily_summary;

DROP INDEX IF EXISTS aws_compute_summary;
DROP MATERIALIZED VIEW IF EXISTS reporting_aws_compute_summary;

DROP INDEX IF EXISTS aws_compute_summary_service;
DROP MATERIALIZED VIEW IF EXISTS reporting_aws_compute_summary_by_service;

DROP INDEX IF EXISTS aws_compute_summary_region;
DROP MATERIALIZED VIEW IF EXISTS reporting_aws_compute_summary_by_region;

DROP INDEX IF EXISTS aws_compute_summary_account;
DROP MATERIALIZED VIEW IF EXISTS reporting_aws_compute_summary_by_account;
            """
        ),
        migrations.AlterField(
            model_name="awscostentrylineitemdaily", name="usage_end", field=models.DateField(null=True)
        ),
        migrations.AlterField(model_name="awscostentrylineitemdaily", name="usage_start", field=models.DateField()),
        migrations.AlterField(
            model_name="awscostentrylineitemdailysummary", name="usage_end", field=models.DateField(null=True)
        ),
        migrations.AlterField(
            model_name="awscostentrylineitemdailysummary", name="usage_start", field=models.DateField()
        ),
        migrations.AlterField(
            model_name="azurecostentrylineitemdailysummary", name="usage_end", field=models.DateField(null=True)
        ),
        migrations.AlterField(
            model_name="azurecostentrylineitemdailysummary", name="usage_start", field=models.DateField()
        ),
        migrations.AlterField(model_name="ocpawscostlineitemdailysummary", name="usage_end", field=models.DateField()),
        migrations.AlterField(
            model_name="ocpawscostlineitemdailysummary", name="usage_start", field=models.DateField()
        ),
        migrations.AlterField(model_name="ocpnodelabellineitemdaily", name="usage_end", field=models.DateField()),
        migrations.AlterField(model_name="ocpnodelabellineitemdaily", name="usage_start", field=models.DateField()),
        migrations.AddIndex(
            model_name="awscostentrylineitemdaily",
            index=django.contrib.postgres.indexes.GinIndex(fields=["tags"], name="aws_cost_entry"),
        ),
        migrations.AddIndex(
            model_name="awscostentrylineitemdaily",
            index=django.contrib.postgres.indexes.GinIndex(
                fields=["product_code"], name="aws_cost_pcode_like", opclasses=["gin_trgm_ops"]
            ),
        ),
        migrations.AddIndex(
            model_name="awscostentrylineitemdailysummary",
            index=django.contrib.postgres.indexes.GinIndex(
                fields=["product_code"], name="aws_summ_usage_pcode_like", opclasses=["gin_trgm_ops"]
            ),
        ),
        migrations.AddIndex(
            model_name="awscostentrylineitemdailysummary",
            index=django.contrib.postgres.indexes.GinIndex(
                fields=["product_family"], name="aws_summ_usage_pfam_like", opclasses=["gin_trgm_ops"]
            ),
        ),
        migrations.AddIndex(
            model_name="ocpnodelabellineitemdaily",
            index=models.Index(fields=["usage_start"], name="ocplblnitdly_usage_start"),
        ),
        migrations.AddIndex(
            model_name="ocpnodelabellineitemdaily",
            index=django.contrib.postgres.indexes.GinIndex(fields=["node_labels"], name="ocplblnitdly_node_labels"),
        ),
        migrations.AlterField(
            model_name="azurecostentrylineitemdaily", name="usage_date_time", field=models.DateField(null=False)
        ),
        migrations.RenameField(
            model_name="azurecostentrylineitemdaily", old_name="usage_date_time", new_name="usage_date"
        ),
        migrations.RunSQL(
            sql="""
CREATE MATERIALIZED VIEW reporting_aws_cost_summary AS(
    SELECT row_number() OVER(ORDER BY date(usage_start)) as id,
        date(usage_start) as usage_start,
        date(usage_start) as usage_end,
        sum(unblended_cost) as unblended_cost,
        sum(markup_cost) as markup_cost,
        max(currency_code) as currency_code
    FROM reporting_awscostentrylineitem_daily_summary
    -- Get data for this month or last month
    WHERE usage_start >= DATE_TRUNC('month', NOW() - '1 month'::interval)::date
    GROUP BY date(usage_start)
)
;

CREATE UNIQUE INDEX aws_cost_summary
ON reporting_aws_cost_summary (usage_start)
;

CREATE MATERIALIZED VIEW reporting_aws_cost_summary_by_service AS(
    SELECT row_number() OVER(ORDER BY date(usage_start), product_code, product_family) as id,
        date(usage_start) as usage_start,
        date(usage_start) as usage_end,
        product_code,
        product_family,
        sum(unblended_cost) as unblended_cost,
        sum(markup_cost) as markup_cost,
        max(currency_code) as currency_code
    FROM reporting_awscostentrylineitem_daily_summary
    -- Get data for this month or last month
    WHERE usage_start >= DATE_TRUNC('month', NOW() - '1 month'::interval)::date
    GROUP BY date(usage_start), product_code, product_family
)
;

CREATE UNIQUE INDEX aws_cost_summary_service
ON reporting_aws_cost_summary_by_service (usage_start, product_code, product_family)
;

CREATE MATERIALIZED VIEW reporting_aws_cost_summary_by_account AS(
    SELECT row_number() OVER(ORDER BY date(usage_start), usage_account_id, account_alias_id) as id,
        date(usage_start) as usage_start,
        date(usage_start) as usage_end,
        usage_account_id,
        account_alias_id,
        sum(unblended_cost) as unblended_cost,
        sum(markup_cost) as markup_cost,
        max(currency_code) as currency_code
    FROM reporting_awscostentrylineitem_daily_summary
    -- Get data for this month or last month
    WHERE usage_start >= DATE_TRUNC('month', NOW() - '1 month'::interval)::date
    GROUP BY date(usage_start), usage_account_id, account_alias_id
)
;

CREATE UNIQUE INDEX aws_cost_summary_account
ON reporting_aws_cost_summary_by_account (usage_start, usage_account_id, account_alias_id)
;

CREATE MATERIALIZED VIEW reporting_aws_cost_summary_by_region AS(
    SELECT row_number() OVER(ORDER BY date(usage_start), region, availability_zone) as id,
        date(usage_start) as usage_start,
        date(usage_start) as usage_end,
        region,
        availability_zone,
        sum(unblended_cost) as unblended_cost,
        sum(markup_cost) as markup_cost,
        max(currency_code) as currency_code
    FROM reporting_awscostentrylineitem_daily_summary
    -- Get data for this month or last month
    WHERE usage_start >= DATE_TRUNC('month', NOW() - '1 month'::interval)::date
    GROUP BY date(usage_start), region, availability_zone
)
;

CREATE UNIQUE INDEX aws_cost_summary_region
ON reporting_aws_cost_summary_by_region (usage_start, region, availability_zone)
;

CREATE MATERIALIZED VIEW reporting_aws_storage_summary AS(
    SELECT row_number() OVER(ORDER BY date(usage_start), product_family) as id,
        date(usage_start) as usage_start,
        date(usage_start) as usage_end,
        product_family,
        sum(usage_amount) as usage_amount,
        max(unit) as unit,
        sum(unblended_cost) as unblended_cost,
        sum(markup_cost) as markup_cost,
        max(currency_code) as currency_code
    FROM reporting_awscostentrylineitem_daily_summary
    -- Get data for this month or last month
    WHERE product_family LIKE '%Storage%'
        AND unit = 'GB-Mo'
        AND usage_start >= DATE_TRUNC('month', NOW() - '1 month'::interval)::date
    GROUP BY date(usage_start), product_family
)
;

CREATE UNIQUE INDEX aws_storage_summary
ON reporting_aws_storage_summary (usage_start, product_family)
;

CREATE MATERIALIZED VIEW reporting_aws_storage_summary_by_service AS(
    SELECT row_number() OVER(ORDER BY date(usage_start), product_code, product_family) as id,
        date(usage_start) as usage_start,
        date(usage_start) as usage_end,
        product_code,
        product_family,
        sum(usage_amount) as usage_amount,
        max(unit) as unit,
        sum(unblended_cost) as unblended_cost,
        sum(markup_cost) as markup_cost,
        max(currency_code) as currency_code
    FROM reporting_awscostentrylineitem_daily_summary
    -- Get data for this month or last month
    WHERE product_family LIKE '%Storage%'
        AND unit = 'GB-Mo'
        AND usage_start >= DATE_TRUNC('month', NOW() - '1 month'::interval)::date
    GROUP BY date(usage_start), product_code, product_family
)
;

CREATE UNIQUE INDEX aws_storage_summary_service
ON reporting_aws_storage_summary_by_service (usage_start, product_code, product_family)
;

CREATE MATERIALIZED VIEW reporting_aws_storage_summary_by_account AS(
    SELECT row_number() OVER(ORDER BY date(usage_start), usage_account_id, account_alias_id, product_family) as id,
        date(usage_start) as usage_start,
        date(usage_start) as usage_end,
        usage_account_id,
        account_alias_id,
        product_family,
        sum(usage_amount) as usage_amount,
        max(unit) as unit,
        sum(unblended_cost) as unblended_cost,
        sum(markup_cost) as markup_cost,
        max(currency_code) as currency_code
    FROM reporting_awscostentrylineitem_daily_summary
    -- Get data for this month or last month
    WHERE product_family LIKE '%Storage%'
        AND unit = 'GB-Mo'
        AND usage_start >= DATE_TRUNC('month', NOW() - '1 month'::interval)::date
    GROUP BY date(usage_start), usage_account_id, account_alias_id, product_family
)
;

CREATE UNIQUE INDEX aws_storage_summary_account
ON reporting_aws_storage_summary_by_account (usage_start, usage_account_id, account_alias_id, product_family)
;

CREATE MATERIALIZED VIEW reporting_aws_storage_summary_by_region AS(
    SELECT row_number() OVER(ORDER BY date(usage_start), region, availability_zone, product_family) as id,
        date(usage_start) as usage_start,
        date(usage_start) as usage_end,
        region,
        availability_zone,
        product_family,
        sum(usage_amount) as usage_amount,
        max(unit) as unit,
        sum(unblended_cost) as unblended_cost,
        sum(markup_cost) as markup_cost,
        max(currency_code) as currency_code
    FROM reporting_awscostentrylineitem_daily_summary
    -- Get data for this month or last month
    WHERE product_family LIKE '%Storage%'
        AND unit = 'GB-Mo'
        AND usage_start >= DATE_TRUNC('month', NOW() - '1 month'::interval)::date
    GROUP BY date(usage_start), region, availability_zone, product_family
)
;

CREATE UNIQUE INDEX aws_storage_summary_region
ON reporting_aws_storage_summary_by_region (usage_start, region, availability_zone, product_family)
;

CREATE MATERIALIZED VIEW reporting_aws_network_summary AS(
    SELECT row_number() OVER(ORDER BY date(usage_start), product_code) as id,
        date(usage_start) as usage_start,
        date(usage_start) as usage_end,
        product_code,
        sum(usage_amount) as usage_amount,
        max(unit) as unit,
        sum(unblended_cost) as unblended_cost,
        sum(markup_cost) as markup_cost,
        max(currency_code) as currency_code
    FROM reporting_awscostentrylineitem_daily_summary
    -- Get data for this month or last month
    WHERE product_code IN ('AmazonVPC','AmazonCloudFront','AmazonRoute53','AmazonAPIGateway')
        AND usage_start >= DATE_TRUNC('month', NOW() - '1 month'::interval)::date
    GROUP BY date(usage_start), product_code
)
;

CREATE UNIQUE INDEX aws_network_summary
ON reporting_aws_network_summary (usage_start, product_code)
;

CREATE MATERIALIZED VIEW reporting_aws_database_summary AS(
    SELECT row_number() OVER(ORDER BY date(usage_start), product_code) as id,
        date(usage_start) as usage_start,
        date(usage_start) as usage_end,
        product_code,
        sum(usage_amount) as usage_amount,
        max(unit) as unit,
        sum(unblended_cost) as unblended_cost,
        sum(markup_cost) as markup_cost,
        max(currency_code) as currency_code
    FROM reporting_awscostentrylineitem_daily_summary
    -- Get data for this month or last month
    WHERE product_code IN ('AmazonRDS','AmazonDynamoDB','AmazonElastiCache','AmazonNeptune','AmazonRedshift','AmazonDocumentDB')
        AND usage_start >= DATE_TRUNC('month', NOW() - '1 month'::interval)::date
    GROUP BY date(usage_start), product_code
)
;

CREATE UNIQUE INDEX aws_database_summary
ON reporting_aws_database_summary (usage_start, product_code)
;

CREATE MATERIALIZED VIEW reporting_ocpallcostlineitem_daily_summary AS (
    SELECT row_number() OVER () as id,
        lids.*
    FROM (
        SELECT 'AWS' as source_type,
            cluster_id,
            cluster_alias,
            namespace,
            node::text as node,
            resource_id,
            usage_start,
            usage_end,
            usage_account_id,
            account_alias_id,
            product_code,
            product_family,
            instance_type,
            region,
            availability_zone,
            tags,
            usage_amount,
            unit,
            unblended_cost,
            markup_cost,
            currency_code,
            shared_projects,
            project_costs
        FROM reporting_ocpawscostlineitem_daily_summary
        WHERE usage_start >= DATE_TRUNC('month', NOW() - '1 month'::interval)::date

        UNION

        SELECT 'Azure' as source_type,
            cluster_id,
            cluster_alias,
            namespace,
            node::text as node,
            resource_id,
            usage_start,
            usage_end,
            subscription_guid as usage_account_id,
            NULL::int as account_alias_id,
            service_name as product_code,
            NULL as product_family,
            instance_type,
            resource_location as region,
            NULL as availability_zone,
            tags,
            usage_quantity as usage_amount,
            unit_of_measure as unit,
            pretax_cost as unblended_cost,
            markup_cost,
            currency as currency_code,
            shared_projects,
            project_costs
        FROM reporting_ocpazurecostlineitem_daily_summary
        WHERE usage_start >= DATE_TRUNC('month', NOW() - '1 month'::interval)::date
    ) AS lids
)
;

CREATE INDEX ocpallcstdlysumm_node on reporting_ocpallcostlineitem_daily_summary (node text_pattern_ops);
CREATE INDEX ocpallcstdlysumm_node_like on reporting_ocpallcostlineitem_daily_summary USING GIN (node gin_trgm_ops);
CREATE index ocpallcstdlysumm_nsp on reporting_ocpallcostlineitem_daily_summary USING GIN (namespace);

CREATE MATERIALIZED VIEW reporting_ocpallcostlineitem_project_daily_summary AS (
    SELECT row_number() OVER () as id,
        lids.*
    FROM (
        SELECT 'AWS' as source_type,
            cluster_id,
            cluster_alias,
            data_source,
            namespace::text as namespace,
            node::text as node,
            pod_labels,
            resource_id,
            usage_start,
            usage_end,
            usage_account_id,
            account_alias_id,
            product_code,
            product_family,
            instance_type,
            region,
            availability_zone,
            usage_amount,
            unit,
            unblended_cost,
            project_markup_cost,
            pod_cost,
            currency_code
        FROM reporting_ocpawscostlineitem_project_daily_summary
        WHERE usage_start >= DATE_TRUNC('month', NOW() - '1 month'::interval)::date

        UNION

        SELECT 'Azure' as source_type,
            cluster_id,
            cluster_alias,
            data_source,
            namespace::text as namespace,
            node::text as node,
            pod_labels,
            resource_id,
            usage_start,
            usage_end,
            subscription_guid as usage_account_id,
            NULL::int as account_alias_id,
            service_name as product_code,
            NULL as product_family,
            instance_type,
            resource_location as region,
            NULL as availability_zone,
            usage_quantity as usage_amount,
            unit_of_measure as unit,
            pretax_cost as unblended_cost,
            project_markup_cost,
            pod_cost,
            currency as currency_code
        FROM reporting_ocpazurecostlineitem_project_daily_summary
        WHERE usage_start >= DATE_TRUNC('month', NOW() - '1 month'::interval)::date
    ) AS lids
)
;

CREATE INDEX ocpallcstprjdlysumm_node on reporting_ocpallcostlineitem_project_daily_summary (node text_pattern_ops);
CREATE index ocpallcstprjdlysumm_nsp on reporting_ocpallcostlineitem_project_daily_summary (namespace text_pattern_ops);
CREATE INDEX ocpallcstprjdlysumm_node_like on reporting_ocpallcostlineitem_project_daily_summary USING GIN (node gin_trgm_ops);
CREATE index ocpallcstprjdlysumm_nsp_like on reporting_ocpallcostlineitem_project_daily_summary USING GIN (namespace gin_trgm_ops);

CREATE MATERIALIZED VIEW reporting_aws_compute_summary AS(
SELECT ROW_NUMBER() OVER(ORDER BY c.usage_start, c.instance_type) AS id,
       c.usage_start,
       c.usage_start as usage_end,
       c.instance_type,
       r.resource_ids,
       CARDINALITY(r.resource_ids) AS resource_count,
       c.usage_amount,
       c.unit,
       c.unblended_cost,
       c.markup_cost,
       c.currency_code
  FROM (
        -- this group by gets the counts
         SELECT usage_start,
                instance_type,
                SUM(usage_amount) AS usage_amount,
                MAX(unit) AS unit,
                SUM(unblended_cost) AS unblended_cost,
                SUM(markup_cost) AS markup_cost,
                MAX(currency_code) AS currency_code
           FROM reporting_awscostentrylineitem_daily_summary
          WHERE usage_start >= DATE_TRUNC('month', NOW() - '1 month'::interval)::date
            AND instance_type IS NOT NULL
          GROUP
             BY usage_start,
                instance_type
       ) AS c
  JOIN (
        -- this group by gets the distinct resources running by day
         SELECT usage_start,
                instance_type,
                ARRAY_AGG(DISTINCT resource_id ORDER BY resource_id) as resource_ids
           FROM (
                  SELECT usage_start,
                         instance_type,
                         UNNEST(resource_ids) AS resource_id
                    FROM reporting_awscostentrylineitem_daily_summary
                   WHERE usage_start >= DATE_TRUNC('month', NOW() - '1 month'::interval)::date
                     AND instance_type IS NOT NULL
                ) AS x
          GROUP
             BY usage_start,
                instance_type
       ) AS r
    ON c.usage_start = r.usage_start
   AND c.instance_type = r.instance_type
       )
  WITH DATA
       ;

CREATE UNIQUE INDEX aws_compute_summary
    ON reporting_aws_compute_summary (usage_start, instance_type)
;

CREATE MATERIALIZED VIEW reporting_aws_compute_summary_by_service AS(
SELECT ROW_NUMBER() OVER(ORDER BY c.usage_start, c.product_code, c.product_family, c.instance_type) AS id,
       c.usage_start,
       c.usage_start as usage_end,
       c.product_code,
       c.product_family,
       c.instance_type,
       r.resource_ids,
       CARDINALITY(r.resource_ids) AS resource_count,
       c.usage_amount,
       c.unit,
       c.unblended_cost,
       c.markup_cost,
       c.currency_code
  FROM (
        -- this group by gets the counts
         SELECT usage_start,
                product_code,
                product_family,
                instance_type,
                SUM(usage_amount) AS usage_amount,
                MAX(unit) AS unit,
                SUM(unblended_cost) AS unblended_cost,
                SUM(markup_cost) AS markup_cost,
                MAX(currency_code) AS currency_code
           FROM reporting_awscostentrylineitem_daily_summary
          WHERE usage_start >= DATE_TRUNC('month', NOW() - '1 month'::interval)::date
            AND instance_type IS NOT NULL
          GROUP
             BY usage_start,
                product_code,
                product_family,
                instance_type
       ) AS c
  JOIN (
        -- this group by gets the distinct resources running by day
         SELECT usage_start,
                product_code,
                product_family,
                instance_type,
                ARRAY_AGG(DISTINCT resource_id ORDER BY resource_id) as resource_ids
           from (
                  SELECT usage_start,
                         product_code,
                         product_family,
                         instance_type,
                         UNNEST(resource_ids) AS resource_id
                    FROM reporting_awscostentrylineitem_daily_summary
                   WHERE usage_start >= DATE_TRUNC('month', NOW() - '1 month'::interval)::date
                     AND instance_type IS NOT NULL
                ) AS x
          GROUP
             BY usage_start,
                product_code,
                product_family,
                instance_type
       ) AS r
    ON c.usage_start = r.usage_start
   AND c.product_code = r.product_code
   AND c.product_family = r.product_family
   AND c.instance_type = r.instance_type
       )
  WITH DATA
       ;

CREATE UNIQUE INDEX aws_compute_summary_service
    ON reporting_aws_compute_summary_by_service (usage_start, product_code, product_family, instance_type)
;

CREATE MATERIALIZED VIEW reporting_aws_compute_summary_by_region AS(
SELECT ROW_NUMBER() OVER(ORDER BY c.usage_start, c.region, c.availability_zone, c.instance_type) AS id,
       c.usage_start,
       c.usage_start AS usage_end,
       c.region,
       c.availability_zone,
       c.instance_type,
       r.resource_ids,
       CARDINALITY(r.resource_ids) AS resource_count,
       c.usage_amount,
       c.unit,
       c.unblended_cost,
       c.markup_cost,
       c.currency_code
  FROM (
        -- this group by gets the counts
         SELECT usage_start,
                region,
                availability_zone,
                instance_type,
                SUM(usage_amount) AS usage_amount,
                MAX(unit) AS unit,
                SUM(unblended_cost) AS unblended_cost,
                SUM(markup_cost) AS markup_cost,
                MAX(currency_code) AS currency_code
           FROM reporting_awscostentrylineitem_daily_summary
          WHERE usage_start >= DATE_TRUNC('month', NOW() - '1 month'::interval)::date
            AND instance_type IS NOT NULL
          GROUP
             BY usage_start,
                region,
                availability_zone,
                instance_type
       ) AS c
  JOIN (
        -- this group by gets the distinct resources running by day
         SELECT usage_start,
                region,
                availability_zone,
                instance_type,
                ARRAY_AGG(DISTINCT resource_id ORDER BY resource_id) AS resource_ids
           from (
                  SELECT usage_start,
                         region,
                         availability_zone,
                         instance_type,
                         UNNEST(resource_ids) AS resource_id
                    FROM reporting_awscostentrylineitem_daily_summary
                   WHERE usage_start >= DATE_TRUNC('month', NOW() - '1 month'::interval)::date
                     AND instance_type IS NOT NULL
                ) AS x
          GROUP
             BY usage_start,
                region,
                availability_zone,
                instance_type
       ) AS r
    ON c.usage_start = r.usage_start
   AND c.region = r.region
   AND c.availability_zone = r.availability_zone
   AND c.instance_type = r.instance_type
       )
  WITH DATA
       ;

CREATE UNIQUE INDEX aws_compute_summary_region
    ON reporting_aws_compute_summary_by_region (usage_start, region, availability_zone, instance_type)
;

CREATE MATERIALIZED VIEW reporting_aws_compute_summary_by_account AS (
SELECT ROW_NUMBER() OVER (ORDER BY c.usage_start, c.usage_account_id, c.account_alias_id, c.instance_type) as id,
       c.usage_start,
       c.usage_start AS usage_end,
       c.usage_account_id,
       c.account_alias_id,
       c.instance_type,
       r.resource_ids,
       CARDINALITY(r.resource_ids) AS resource_count,
       c.usage_amount,
       c.unit,
       c.unblended_cost,
       c.markup_cost,
       c.currency_code
  FROM (
         -- this group by gets the counts
         SELECT usage_start,
                usage_account_id,
                account_alias_id,
                instance_type,
                SUM(usage_amount) AS usage_amount,
                MAX(unit) AS unit,
                SUM(unblended_cost) AS unblended_cost,
                SUM(markup_cost) AS markup_cost,
                MAX(currency_code) AS currency_code
           FROM reporting_awscostentrylineitem_daily_summary
          WHERE usage_start >= DATE_TRUNC('month', NOW() - '1 month'::interval)::date
            AND instance_type IS NOT NULL
          GROUP
             BY usage_start,
                usage_account_id,
                account_alias_id,
                instance_type
       ) AS c
  JOIN (
         -- this group by gets the distinct resources running by day
         SELECT usage_start,
                usage_account_id,
                account_alias_id,
                instance_type,
                array_agg(distinct resource_id order by resource_id) as resource_ids
           FROM (
                  SELECT usage_start,
                         usage_account_id,
                         account_alias_id,
                         instance_type,
                         UNNEST(resource_ids) as resource_id
                    FROM reporting_awscostentrylineitem_daily_summary
                   WHERE usage_start >= date_trunc('month', NOW() - '1 month'::interval)::date
                     AND instance_type IS NOT NULL
                ) AS x
          GROUP
             BY usage_start,
               usage_account_id,
               account_alias_id,
               instance_type
       ) AS r
    ON c.usage_start = r.usage_start
   AND c.instance_type = r.instance_type
   AND (
         (c.usage_account_id = r.usage_account_id) OR
         (c.account_alias_id = r.account_alias_id)
       )
     )
  WITH DATA
    ;

CREATE UNIQUE INDEX aws_compute_summary_account
    ON reporting_aws_compute_summary_by_account (usage_start, usage_account_id, account_alias_id, instance_type)
;
            """
        ),
    ]
