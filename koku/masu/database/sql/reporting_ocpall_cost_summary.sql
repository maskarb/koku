DELETE
  FROM {{schema | sqlsafe}}.reporting_ocpall_cost_summary
 WHERE usage_start >= {{start_date}}::date
   AND usage_end <= {{end_date}}::date
   AND source_uuid = {{source_uuid}}::uuid;

INSERT
  INTO {{schema | sqlsafe}}.reporting_ocpall_cost_summary
       (
           usage_start,
           usage_end,
           cluster_id,
           cluster_alias,
           unblended_cost,
           markup_cost,
           currency_code,
           source_uuid
       )
SELECT usage_start as usage_start,
       usage_start as usage_end,
       cluster_id,
       max(cluster_alias) as cluster_alias,
       sum(unblended_cost) as unblended_cost,
       sum(markup_cost) as markup_cost,
       max(currency_code) as currency_code,
       {{source_uuid}}::uuid
  FROM {{schema | sqlsafe}}.reporting_ocpallcostlineitem_daily_summary
 WHERE usage_start >= {{start_date}}::date
   AND usage_end <= {{end_date}}::date
   AND source_uuid = {{source_uuid}}::uuid
 GROUP
    BY usage_start,
       cluster_id,
       cluster_alias
)
;
