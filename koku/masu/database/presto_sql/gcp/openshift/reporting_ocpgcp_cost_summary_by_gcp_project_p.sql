-- Clear out old entries first
DELETE FROM postgres.{{schema | sqlsafe}}.reporting_ocpgcp_cost_summary_by_gcp_project_p
WHERE usage_start >= date('{{start_date | sqlsafe}}')
    AND usage_start <= date('{{end_date | sqlsafe}}')
    AND invoice_month = '{{year | sqlsafe}}{{month | sqlsafe}}'
    AND report_period_id = {{report_period_id | sqlsafe}}
;

-- Populate the daily aggregate line item data
INSERT INTO postgres.{{schema | sqlsafe}}.reporting_ocpgcp_cost_summary_by_gcp_project_p (
    uuid,
    report_period_id,
    cluster_id,
    cluster_alias,
    node,
    usage_start,
    usage_end,
    project_id,
    project_name,
    unblended_cost,
    markup_cost,
    currency,
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
        project_id,
        project_name,
        sum(unblended_cost) as unblended_cost,
        sum(markup_cost) as markup_cost,
        max(currency) as currency,
        source_uuid,
        sum(credit_amount) as credit_amount,
        invoice_month
    FROM postgres.{{schema | sqlsafe}}.reporting_ocpgcpcostlineitem_daily_summary
    WHERE report_period_id = {{report_period_id | sqlsafe}}
        AND usage_start >= date('{{start_date | sqlsafe}}')
        AND usage_start <= date('{{end_date | sqlsafe}}')
        AND invoice_month = '{{year | sqlsafe}}{{month | sqlsafe}}'
    GROUP BY report_period_id,
        cluster_id,
        cluster_alias,
        node,
        usage_start,
        usage_end,
        project_id,
        project_name,
        source_uuid,
        invoice_month
;
