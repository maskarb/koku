#
# Copyright 2021 Red Hat Inc.
# SPDX-License-Identifier: Apache-2.0
#
"""View that runs queries in bigquery for continuity testing."""
import logging

from django.views.decorators.cache import never_cache
from google.cloud import bigquery
from google.cloud.exceptions import GoogleCloudError
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.decorators import permission_classes
from rest_framework.decorators import renderer_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.settings import api_settings

from api.provider.models import Provider
from api.utils import DateHelper

LOG = logging.getLogger(__name__)


def get_total(cost, credit):
    if cost and credit:
        return cost + credit
    return None


class BigQueryHelper:
    def __init__(self, table_name):
        self.table_name = table_name
        self.client = bigquery.Client()
        self.dh = DateHelper()
        self.start_date = None
        self.end_date = None

    def set_dates_from_invoice_month(self, invoice_month):
        """Calculates start & end dates from invoice month."""
        start_date = self.dh.invoice_month_start(invoice_month)
        self.start_date = self.dh.n_days_ago(start_date, 5).date()
        self.end_date = self.dh.tomorrow.date()

    def daily_sql(self, invoice_month, results):
        self.set_dates_from_invoice_month(invoice_month)
        daily_query = f"""
                SELECT DATE(usage_start_time) as usage_date,
                    sum(cost) as cost,
                    FROM {self.table_name}
                    WHERE invoice.month = @invoice_month
                    AND DATE(_PARTITIONTIME) BETWEEN @start_date AND @end_date
                    GROUP BY usage_date ORDER BY usage_date;
                """
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("invoice_month", "STRING", invoice_month),
                bigquery.ScalarQueryParameter("start_date", "DATE", self.start_date),
                bigquery.ScalarQueryParameter("end_date", "DATE", self.end_date),
            ]
        )
        LOG.info(daily_query)
        rows = self.client.query(daily_query, job_config=job_config).result()
        daily_dict = {}
        for row in rows:
            daily_dict[str(row["usage_date"])] = {"cost": row.get("cost")}
        results[invoice_month] = daily_dict
        return results

    def monthly_sql(self, invoice_month, results, key):
        self.set_dates_from_invoice_month(invoice_month)
        monthly_query = f"""
                SELECT sum(cost) as cost,
                    FROM {self.table_name}
                    WHERE DATE(_PARTITIONTIME) BETWEEN @start_date AND @end_date
                    AND invoice.month = @invoice_month
                """
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("invoice_month", "STRING", invoice_month),
                bigquery.ScalarQueryParameter("start_date", "DATE", self.start_date),
                bigquery.ScalarQueryParameter("end_date", "DATE", self.end_date),
            ]
        )
        rows = self.client.query(monthly_query, job_config=job_config).result()
        for row in rows:
            results[key] = row[0]  # TODO: Remove once bigquery is updated.
            metadata = {
                "invoice_month": invoice_month,
                "cost": row.get("cost"),
            }
            results[key + "_metadata"] = metadata
        return results


@never_cache
@api_view(http_method_names=["GET"])
@permission_classes((AllowAny,))
@renderer_classes(tuple(api_settings.DEFAULT_RENDERER_CLASSES))
def bigquery_cost(request, *args, **kwargs):  # noqa: C901
    """Returns the invoice monthly cost."""
    params = request.query_params
    provider_uuid = kwargs.get("source_uuid")
    return_daily = "daily" in params.keys()

    provider = Provider.objects.filter(
        uuid=provider_uuid, type__in=[Provider.PROVIDER_GCP, Provider.PROVIDER_GCP_LOCAL]
    ).first()
    if not provider:
        errmsg = f"The *GCP* provider_uuid {provider_uuid} does not exist."
        return Response({"Error": errmsg}, status=status.HTTP_400_BAD_REQUEST)
    credentials = provider.authentication.credentials
    data_source = provider.billing_source.data_source

    dataset = data_source.get("dataset")
    table_id = data_source.get("table_id")
    project_id = credentials.get("project_id")

    if None in [project_id, dataset, table_id]:
        errmsg = "Could not build gcp table name due to mising information."
        return Response({"Error": errmsg}, status=status.HTTP_400_BAD_REQUEST)
    table_name = ".".join([project_id, dataset, table_id])
    dh = DateHelper()
    invoice_months = dh.gcp_find_invoice_months_in_date_range(dh.last_month_start, dh.today)
    mapping = {"previous": invoice_months[0], "current": invoice_months[1]}

    results = {}
    try:
        bq_helper = BigQueryHelper(table_name)
        for key, invoice_month in mapping.items():
            if return_daily:
                results = bq_helper.daily_sql(invoice_month, results)
                resp_key = "daily_invoice_cost_mapping"
            else:
                results = bq_helper.monthly_sql(invoice_month, results, key)
                resp_key = "monthly_invoice_cost_mapping"
    except GoogleCloudError as err:
        return Response({"Error": err.message}, status=status.HTTP_400_BAD_REQUEST)

    resp = {resp_key: results}
    return Response(resp)
