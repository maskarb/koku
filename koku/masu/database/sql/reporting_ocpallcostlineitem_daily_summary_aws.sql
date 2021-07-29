DELETE
  FROM {{schema | sqlsafe}}.reporting_ocpallcostlineitem_daily_summary
 WHERE usage_start >= {{start_date}}
   AND usage_start <= {{end_date}}
   AND source_type = {{source_type}}
   AND source_uuid = {{source_uuid}};


INSERT
  INTO {{schema | sqlsafe}}.reporting_ocpallcostlineitem_daily_summary
       (
           source_type,
           cluster_id,
           cluster_alias,
           namespace,
           node,
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
           source_uuid,
           tags_hash,
           namespace_hash
       )
SELECT {{source_type}}::text AS source_type,
       aws.cluster_id,
       aws.cluster_alias,
       aws.namespace,
       aws.node,
       aws.resource_id,
       aws.usage_start,
       aws.usage_end,
       aws.usage_account_id,
       aws.account_alias_id,
       aws.product_code,
       aws.product_family,
       aws.instance_type,
       aws.region,
       aws.availability_zone,
       aws.tags,
       aws.usage_amount,
       aws.unit,
       aws.unblended_cost,
       aws.markup_cost,
       aws.currency_code,
       aws.shared_projects,
       aws.source_uuid,
       public.jsonb_sha256_text(aws.tags) as tags_hash,
       encode(sha256(decode(array_to_string(aws.namespace, '|'), 'escape')), 'hex') as namespace_hash
  FROM {{schema | sqlsafe}}.reporting_ocpawscostlineitem_daily_summary AS aws
 WHERE aws.usage_start >= {{start_date}}
   AND aws.usage_start <= {{end_date}}
   AND aws.source_uuid = {{source_uuid}};
