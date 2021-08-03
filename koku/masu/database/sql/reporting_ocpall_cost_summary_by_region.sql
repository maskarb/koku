DELETE
  FROM {{schema | sqlsafe}}.reporting_ocpall_cost_summary_by_region
 WHERE usage_start >= {{start_date}}::date
   AND usage_start <= {{end_date}}::date;


INSERT
  INTO {{schema | sqlsafe}}.reporting_ocpall_cost_summary_by_region
       (
           source_type,
           usage_start,
           usage_end,
           cluster_id,
           cluster_alias,
           usage_account_id,
           account_alias_id,
           region,
           availability_zone,
           unblended_cost,
           markup_cost,
           currency_code,
           source_uuid
       )
SELECT usage_start as usage_start,
       usage_start as usage_end,
       cluster_id,
       max(cluster_alias) as cluster_alias,
       usage_account_id,
       max(account_alias_id) as account_alias_id,
       region,
       availability_zone,
       sum(unblended_cost) as unblended_cost,
       sum(markup_cost) as markup_cost,
       max(currency_code) as currency_code,
       max(source_uuid) as source_uuid
  FROM {{schema | sqlsafe}}.reporting_ocpallcostlineitem_daily_summary
  WHERE usage_start >= {{start_date}}::date
    AND usage_end <= {{end_date}}::date
  GROUP
     BY usage_start,
        cluster_id,
        usage_account_id,
        region,
        availability_zone
;
