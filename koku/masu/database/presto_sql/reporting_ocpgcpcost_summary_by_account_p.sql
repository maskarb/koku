-- Clear out old entries first
DELETE FROM {{schema | sqlsafe}}.reporting_ocpgcpcost_summary_by_account_p
WHERE usage_start >= {{start_date}}::date
    AND usage_start <= {{end_date}}::date
    AND report_period_id = {{report_period_id | sqlsafe}}
;

-- Populate the daily aggregate line item data
INSERT INTO {{schema | sqlsafe}}.reporting_ocpgcpcost_summary_by_account_p (
    uuid,
    report_period_id,
    cluster_id,
    cluster_alias,
    namespace,
    node,
    resource_id,
    usage_start,
    usage_end,
    account_id,
    project_id,
    project_name,
    instance_type,
    service_id,
    service_alias,
    region,
    usage_amount,
    unblended_cost,
    markup_cost,
    currency,
    unit,
    shared_projects,
    source_uuid,
    credit_amount
)
    SELECT uuid_generate_v4(),
        report_period_id,
        cluster_id,
        cluster_alias,
        array_agg(DISTINCT namespace) as namespace,
        node,
        resource_id,
        usage_start,
        usage_end,
        account_id,
        project_id,
        project_name,
        instance_type,
        service_id,
        service_alias,
        region,
        sum(usage_amount) as usage_amount,
        sum(unblended_cost) as unblended_cost,
        sum(markup_cost) as markup_cost,
        max(currency) as currency,
        max(unit) as unit,
        count(DISTINCT namespace) as shared_projects,
        source_uuid,
        sum(credit_amount) as credit_amount
    FROM {{schema | sqlsafe}}.reporting_ocpgcpcostlineitem_daily_summary
    WHERE report_period_id = {{report_period_id | sqlsafe}}
        AND usage_start >= date({{start_date}})
        AND usage_start <= date({{end_date}})
    GROUP BY report_period_id,
        cluster_id,
        cluster_alias,
        node,
        resource_id,
        usage_start,
        usage_end,
        account_id,
        project_id,
        project_name,
        instance_type,
        service_id,
        service_alias,
        region,
        source_uuid
;