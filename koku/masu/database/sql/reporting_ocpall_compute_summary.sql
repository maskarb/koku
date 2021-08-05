DELETE
  FROM {{schema | sqlsafe}}.reporting_ocpall_compute_summary;
 WHERE usage_start >= {{start_date}}::date
   AND usage_end <= {{start_date}}::date;


INSERT
  INTO {{schema | sqlsafe}}.reporting_ocpall_compute_summary
       (
           usage_start,
           usage_end,
           cluster_id,
           cluster_alias,
           usage_account_id,
           account_alias_id,
           product_code,
           instance_type,
           resource_id,
           usage_amount,
           unit,
           unblended_cost,
           markup_cost,
           currency_code,
           source_uuid
       )
SELECT lids.usage_start,
       lids.usage_start as usage_end,
       lids.cluster_id,
       max(lids.cluster_alias) as cluster_alias,
       lids.usage_account_id,
       max(lids.account_alias_id) as account_alias_id,
       lids.product_code,
       lids.instance_type,
       lids.resource_id,
       sum(lids.usage_amount) as usage_amount,
       max(lids.unit) as unit,
       sum(lids.unblended_cost) as unblended_cost,
       sum(lids.markup_cost) as markup_cost,
       max(lids.currency_code) as currency_code,
       max(lids.source_uuid::text)::uuid as source_uuid
  FROM reporting_ocpallcostlineitem_daily_summary lids
 WHERE usage_start >= {{start_date}}::date
   AND usage_end <= {{start_date}}::date
   AND instance_type IS NOT NULL
 GROUP
    BY lids.usage_start,
       lids.cluster_id,
       lids.usage_account_id,
       lids.product_code,
       lids.instance_type,
       lids.resource_id
;
