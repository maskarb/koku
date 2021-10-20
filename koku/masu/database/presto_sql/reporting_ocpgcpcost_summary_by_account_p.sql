-- Clear out old entries first
DELETE FROM postgres.{{schema | sqlsafe}}.reporting_ocpgcpcost_summary_by_account_p
WHERE usage_start >= date('{{start_date | sqlsafe}}')
    AND usage_start <= date('{{start_date | sqlsafe}}')
    AND report_period_id = {{report_period_id | sqlsafe}}
;

-- Populate the daily aggregate line item data
INSERT INTO postgres.{{schema | sqlsafe}}.reporting_ocpgcpcost_summary_by_account_p (
    uuid,
    report_period_id,
    cluster_id,
    cluster_alias,
    node,
    usage_start,
    usage_end,
    account_id,
    project_id,
    project_name,
    service_id,
    service_alias,
    usage_amount,
    unblended_cost,
    markup_cost,
    currency,
    unit,
    source_uuid,
    credit_amount,
    invoice_month
)
    SELECT uuid(),
        report_period_id,
        cluster_id,
        cluster_alias,
        node,
        usage_start,
        usage_end,
        account_id,
        project_id,
        project_name,
        service_id,
        service_alias,
        sum(usage_amount) as usage_amount,
        sum(unblended_cost) as unblended_cost,
        sum(markup_cost) as markup_cost,
        max(currency) as currency,
        max(unit) as unit,
        source_uuid,
        sum(credit_amount) as credit_amount,
        invoice_month
    FROM postgres.{{schema | sqlsafe}}.reporting_ocpgcpcostlineitem_daily_summary
    WHERE report_period_id = {{report_period_id | sqlsafe}}
        AND usage_start >= date({{start_date}})
        AND usage_start <= date({{end_date}})
    GROUP BY report_period_id,
        cluster_id,
        cluster_alias,
        node,
        usage_start,
        usage_end,
        account_id,
        project_id,
        project_name,
        service_id,
        service_alias,
        source_uuid,
        invoice_month
;
