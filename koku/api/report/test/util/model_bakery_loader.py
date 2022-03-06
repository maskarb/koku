#
# Copyright 2021 Red Hat Inc.
# SPDX-License-Identifier: Apache-2.0
#
"""Test utilities."""
import logging
import random
from datetime import timedelta
from itertools import cycle
from itertools import product

from django.test.utils import override_settings
from django.utils import timezone
from faker import Faker
from model_bakery import baker
from tenant_schemas.utils import schema_context

from api.models import Provider
from api.provider.models import ProviderBillingSource
from api.report.test.util.constants import AWS_CONSTANTS
from api.report.test.util.constants import OCP_ON_PREM_COST_MODEL
from api.report.test.util.data_loader import DataLoader
from masu.database.aws_report_db_accessor import AWSReportDBAccessor
from masu.database.azure_report_db_accessor import AzureReportDBAccessor
from masu.database.gcp_report_db_accessor import GCPReportDBAccessor
from masu.database.ocp_report_db_accessor import OCPReportDBAccessor
from masu.processor.tasks import refresh_materialized_views
from masu.processor.tasks import update_cost_model_costs
from masu.util.aws.insert_aws_org_tree import InsertAwsOrgTree
from reporting.models import AWSAccountAlias
from reporting.models import AWSOrganizationalUnit


BILL_MODELS = {
    Provider.PROVIDER_AWS: "AWSCostEntryBill",
    Provider.PROVIDER_AWS_LOCAL: "AWSCostEntryBill",
    Provider.PROVIDER_AZURE: "AzureCostEntryBill",
    Provider.PROVIDER_AZURE_LOCAL: "AzureCostEntryBill",
    Provider.PROVIDER_GCP: "GCPCostEntryBill",
    Provider.PROVIDER_GCP_LOCAL: "GCPCostEntryBill",
    Provider.PROVIDER_OCP: "OCPUsageReportPeriod",
}
LOG = logging.getLogger(__name__)


class ModelBakeryDataLoader(DataLoader):
    """Loads model bakery generated test data for different source types."""

    def __init__(self, schema, customer, num_days=45):
        super().__init__(schema, customer, num_days)
        self.faker = Faker()
        self.currency = "USD"  # self.faker.currency_code()
        self.num_tag_keys = 5
        self.tag_keys = [self.faker.slug() for _ in range(self.num_tag_keys)]
        self.tags = [{"app": self.faker.slug()}] + [{key: self.faker.slug()} for key in self.tag_keys]
        self.tag_test_tag_key = "app"
        self._populate_enabled_tag_key_table()

    def _populate_enabled_tag_key_table(self):
        """Insert records for our tag keys."""
        # TODO: COST-444: when transitioning AWS and Azure, these tables need to be uncommented
        # for table_name in ("AWSEnabledTagKeys", "AzureEnabledTagKeys", "GCPEnabledTagKeys",):
        for table_name in ("GCPEnabledTagKeys",):
            for dikt in self.tags:
                for key in dikt.keys():
                    with schema_context(self.schema):
                        baker.make(table_name, key=key)
        # with schema_context(self.schema):
        #     baker.make("OCPEnabledTagKeys", key=self.tag_test_tag_key)

    def create_provider(self, provider_type, credentials, billing_source, name, linked_openshift_provider=None):
        """Create a Provider record"""
        with override_settings(AUTO_DATA_INGEST=False):
            data = {
                "type": provider_type,
                "name": name,
                "authentication__credentials": credentials,
                "customer": self.customer,
                "data_updated_timestamp": timezone.now(),
            }

            if provider_type == Provider.PROVIDER_OCP:
                billing_source, _ = ProviderBillingSource.objects.get_or_create(data_source={})
                data["billing_source"] = billing_source
            else:
                data["billing_source__data_source"] = billing_source

            provider = baker.make("Provider", **data)
            if linked_openshift_provider:
                infra_map = baker.make(
                    "ProviderInfrastructureMap", infrastructure_type=provider_type, infrastructure_provider=provider
                )
                linked_openshift_provider.infrastructure = infra_map
                linked_openshift_provider.save()
            return provider

    def create_manifest(self, provider, bill_date, num_files=1):
        """Create a manifest for the provider."""
        manifest = baker.make(
            "CostUsageReportManifest",
            provider=provider,
            billing_period_start_datetime=bill_date,
            num_total_files=num_files,
            _fill_optional=True,
        )
        baker.make("CostUsageReportStatus", manifest=manifest, _fill_optional=True)
        return manifest

    def create_bill(self, provider_type, provider, bill_date, **kwargs):
        """Create a bill object for the provider"""
        with schema_context(self.schema):
            model_str = BILL_MODELS[provider_type]
            month_end = self.dh.month_end(bill_date)
            data = {"provider": provider}
            if provider_type == Provider.PROVIDER_OCP:
                data["report_period_start"] = bill_date
                data["report_period_end"] = month_end + timedelta(days=1)
            else:
                data["billing_period_start"] = bill_date
                data["billing_period_end"] = month_end
            return baker.make(model_str, **data, **kwargs, _fill_optional=False)

    def create_cost_entry(self, bill_date, bill):
        """Create a cost entry object for the provider"""
        with schema_context(self.schema):
            month_end = self.dh.month_end(bill_date)
            baker.make("AWSCostEntry", interval_start=bill_date, interval_end=month_end, bill=bill)

    def create_cost_model(self, provider):
        """Create a cost model and map entry."""
        with schema_context(self.schema):
            cost_model = baker.make(
                "CostModel",
                name=OCP_ON_PREM_COST_MODEL.get("name"),
                description=OCP_ON_PREM_COST_MODEL.get("description"),
                rates=OCP_ON_PREM_COST_MODEL.get("rates"),
                distribution=OCP_ON_PREM_COST_MODEL.get("distribution"),
                source_type=provider.type,
                currency=self.currency,
                _fill_optional=True,
            )
            baker.make("CostModelMap", provider_uuid=provider.uuid, cost_model=cost_model)

    def load_aws_data(self, linked_openshift_provider=None, day_list=None):
        """Load AWS data for tests."""
        bills = []
        provider_type = Provider.PROVIDER_AWS_LOCAL
        role_arn = "arn:aws:iam::999999999999:role/CostManagement"
        credentials = {"role_arn": role_arn}
        billing_source = {"bucket": "test-bucket"}
        payer_account_id = "9999999999999"

        provider = self.create_provider(
            provider_type, credentials, billing_source, "test-aws", linked_openshift_provider=linked_openshift_provider
        )

        if day_list:
            org_tree_obj = InsertAwsOrgTree(
                schema=self.schema, provider_uuid=provider.uuid, start_date=self.dates[0][0]
            )
            org_tree_obj.insert_tree(day_list=day_list)

        with schema_context(self.schema):
            main_alias = baker.make("AWSAccountAlias", account_id=payer_account_id, account_alias="Test Account")

        for start_date, end_date, bill_date in self.dates:
            LOG.info(f"load aws data for start: {start_date}, end: {end_date}")
            with schema_context(self.schema):
                org_units = list(AWSOrganizationalUnit.objects.filter(account_alias_id__isnull=False))
                random.shuffle(org_units)
                aliases = [main_alias] + [
                    AWSAccountAlias.objects.get(id=org_unit.account_alias_id) for org_unit in org_units
                ]
                org_units.insert(0, None)
                usage_account_ids = [alias.account_id for alias in aliases]
                self.create_manifest(provider, bill_date)
                bill = self.create_bill(provider_type, provider, bill_date, payer_account_id=payer_account_id)
                bills.append(bill)
                self.create_cost_entry(bill_date, bill)
                days = (end_date - start_date).days
                for i in range(days):
                    baker.make_recipe(  # Storage data_source
                        "api.report.test.util.aws_daily_summary",
                        cost_entry_bill=bill,
                        usage_account_id=cycle(usage_account_ids),
                        account_alias=cycle(aliases),
                        organizational_unit=cycle(org_units),
                        currency_code=self.currency,
                        usage_start=start_date + timedelta(i),
                        usage_end=start_date + timedelta(i),
                        tags=cycle(self.tags),
                        source_uuid=provider.uuid,
                        _quantity=max(AWS_CONSTANTS.length, len(aliases)),
                    )
        bill_ids = [bill.id for bill in bills]
        with AWSReportDBAccessor(self.schema) as accessor:
            accessor.populate_tags_summary_table(bill_ids, self.first_start_date, self.last_end_date)
            accessor.populate_ui_summary_tables(self.first_start_date, self.last_end_date, provider.uuid)
        return provider, bills

    def load_azure_data(self, linked_openshift_provider=None):
        """Load Azure data for tests."""
        bills = []
        provider_type = Provider.PROVIDER_AZURE_LOCAL
        credentials = {
            "subscription_id": "11111111-1111-1111-1111-11111111",
            "tenant_id": "22222222-2222-2222-2222-22222222",
            "client_id": "33333333-3333-3333-3333-33333333",
            "client_secret": "MyPassW0rd!",
        }
        billing_source = {"resource_group": "resourcegroup1", "storage_account": "storageaccount1"}

        provider = self.create_provider(
            provider_type,
            credentials,
            billing_source,
            "test-azure",
            linked_openshift_provider=linked_openshift_provider,
        )
        sub_guid = self.faker.uuid4()
        for start_date, end_date, bill_date in self.dates:
            LOG.info(f"load azure data for start: {start_date}, end: {end_date}")
            self.create_manifest(provider, bill_date)
            bill = self.create_bill(provider_type, provider, bill_date)
            bills.append(bill)
            with schema_context(self.schema):
                days = (end_date - start_date).days
                for i in range(days):
                    baker.make_recipe(
                        "api.report.test.util.azure_daily_summary",
                        cost_entry_bill=bill,
                        subscription_guid=sub_guid,
                        usage_start=start_date + timedelta(i),
                        usage_end=start_date + timedelta(i),
                        tags=cycle(self.tags),
                        currency=self.currency,
                        source_uuid=provider.uuid,
                        _quantity=len(self.tags),
                    )
        bill_ids = [bill.id for bill in bills]
        with AzureReportDBAccessor(self.schema) as accessor:
            accessor.populate_tags_summary_table(bill_ids, self.first_start_date, self.last_end_date)
            accessor.populate_ui_summary_tables(self.first_start_date, self.last_end_date, provider.uuid)
        return provider, bills

    def load_gcp_data(self, linked_openshift_provider=None):
        """Load Azure data for tests."""
        bills = []
        provider_type = Provider.PROVIDER_GCP_LOCAL
        credentials = {"project_id": "test_project_id"}
        billing_source = {"table_id": "test_table_id", "dataset": "test_dataset"}
        account_id = "123456789"
        provider = self.create_provider(
            provider_type, credentials, billing_source, "test-gcp", linked_openshift_provider=linked_openshift_provider
        )
        projects = [(self.faker.slug(), self.faker.slug()) for _ in range(3)]
        for start_date, end_date, bill_date in self.dates:
            LOG.info(f"load gcp data for start: {start_date}, end: {end_date}")
            self.create_manifest(provider, bill_date)
            bill = self.create_bill(provider_type, provider, bill_date)
            bills.append(bill)
            with schema_context(self.schema):
                days = (end_date - start_date).days
                for i, project in product(range(days), projects):
                    baker.make_recipe(
                        "api.report.test.util.gcp_daily_summary",
                        cost_entry_bill=bill,
                        invoice_month=bill_date.strftime("%Y%m"),
                        account_id=account_id,
                        project_id=project[0],
                        project_name=project[1],
                        usage_start=start_date + timedelta(i),
                        usage_end=start_date + timedelta(i),
                        tags=cycle(self.tags),
                        currency=self.currency,
                        source_uuid=provider.uuid,
                        _quantity=len(self.tags),
                    )
        bill_ids = [bill.id for bill in bills]
        with GCPReportDBAccessor(self.schema) as accessor:
            accessor.populate_tags_summary_table(bill_ids, self.first_start_date, self.last_end_date)
            accessor.populate_ui_summary_tables(self.first_start_date, self.last_end_date, provider.uuid)
        return provider, bills

    def load_openshift_data(self, cluster_id, on_cloud=False):
        """Load OpenShift data for tests."""
        report_periods = []
        provider_type = Provider.PROVIDER_OCP
        credentials = {"cluster_id": cluster_id}
        billing_source = {}

        provider = self.create_provider(provider_type, credentials, billing_source, cluster_id)
        if not on_cloud:
            self.create_cost_model(provider)
        for start_date, end_date, bill_date in self.dates:
            LOG.info(f"load ocp data for start: {start_date}, end: {end_date}")
            self.create_manifest(provider, bill_date)
            report_period = self.create_bill(
                provider_type, provider, bill_date, cluster_id=cluster_id, cluster_alias=cluster_id
            )
            report_periods.append(report_period)
            with schema_context(self.schema):
                days = (end_date - start_date).days
                for i in range(days):
                    infra_raw_cost = random.random() * 100 if on_cloud else None
                    project_infra_raw_cost = infra_raw_cost * random.random() if on_cloud else None
                    baker.make_recipe(  # Storage data_source
                        "api.report.test.util.ocp_usage_storage",
                        report_period=report_period,
                        cluster_id=cluster_id,
                        cluster_alias=cluster_id,
                        usage_start=start_date + timedelta(i),
                        usage_end=start_date + timedelta(i),
                        source_uuid=provider.uuid,
                        infrastructure_raw_cost=infra_raw_cost,
                        infrastructure_project_raw_cost=project_infra_raw_cost,
                    )
                    baker.make_recipe(  # Pod data_source
                        "api.report.test.util.ocp_usage_pod",
                        report_period=report_period,
                        cluster_id=cluster_id,
                        cluster_alias=cluster_id,
                        usage_start=start_date + timedelta(i),
                        usage_end=start_date + timedelta(i),
                        source_uuid=provider.uuid,
                        infrastructure_raw_cost=infra_raw_cost,
                        infrastructure_project_raw_cost=project_infra_raw_cost,
                    )

        report_period_ids = [report_period.id for report_period in report_periods]
        with OCPReportDBAccessor(self.schema) as accessor:
            accessor.populate_pod_label_summary_table(report_period_ids, self.first_start_date, self.last_end_date)
            accessor.populate_volume_label_summary_table(report_period_ids, self.first_start_date, self.last_end_date)
            accessor.update_line_item_daily_summary_with_enabled_tags(
                self.first_start_date, self.last_end_date, report_period_ids
            )
            accessor.populate_ui_summary_tables(self.first_start_date, self.last_end_date, provider.uuid)
        update_cost_model_costs(
            self.schema, provider.uuid, self.first_start_date, self.last_end_date, tracing_id="12345", synchronous=True
        )
        return provider, report_periods

    def load_openshift_on_cloud_data(self, provider_type, cluster_id, bills, report_periods):
        """Load OCP on AWS Daily Summary table."""
        unique_fields = {}
        if provider_type in (Provider.PROVIDER_AWS, Provider.PROVIDER_AWS_LOCAL):
            daily_summary_recipe = "api.report.test.util.ocp_on_aws_daily_summary"
            project_summary_pod_recipe = "api.report.test.util.ocp_on_aws_project_daily_summary_pod"
            project_summary_storage_recipe = "api.report.test.util.ocp_on_aws_project_daily_summary_storage"
            dbaccessor, tags_update_method, ui_update_method = (
                AWSReportDBAccessor,
                "populate_ocp_on_aws_tags_summary_table",
                "populate_ocp_on_aws_ui_summary_tables",
            )
            with schema_context(self.schema):
                account_alias = random.choice(list(AWSAccountAlias.objects.all()))
            unique_fields = {"currency_code": self.currency, "account_alias": account_alias}
        elif provider_type in (Provider.PROVIDER_AZURE, Provider.PROVIDER_AZURE_LOCAL):
            daily_summary_recipe = "api.report.test.util.ocp_on_azure_daily_summary"
            project_summary_pod_recipe = "api.report.test.util.ocp_on_azure_project_daily_summary_pod"
            project_summary_storage_recipe = "api.report.test.util.ocp_on_azure_project_daily_summary_storage"
            dbaccessor, tags_update_method, ui_update_method = (
                AzureReportDBAccessor,
                "populate_ocp_on_azure_tags_summary_table",
                "populate_ocp_on_azure_ui_summary_tables",
            )
            unique_fields = {"currency": self.currency, "subscription_guid": self.faker.uuid4()}
        elif provider_type in (Provider.PROVIDER_GCP, Provider.PROVIDER_GCP_LOCAL):
            daily_summary_recipe = "api.report.test.util.ocp_on_gcp_daily_summary"
            project_summary_pod_recipe = "api.report.test.util.ocp_on_gcp_project_daily_summary_pod"
            project_summary_storage_recipe = "api.report.test.util.ocp_on_gcp_project_daily_summary_storage"
            dbaccessor, tags_update_method, ui_update_method = (
                GCPReportDBAccessor,
                "populate_ocp_on_gcp_tags_summary_table",
                "populate_ocp_on_gcp_ui_summary_tables",
            )
            unique_fields = {
                "currency": self.currency,
                "account_id": self.faker.pystr_format(string_format="???????????????"),
            }

        provider = Provider.objects.filter(type=provider_type).first()
        for dates, bill, report_period in zip(self.dates, bills, report_periods):
            start_date, end_date, bill_date = dates
            if provider_type in (Provider.PROVIDER_GCP, Provider.PROVIDER_GCP_LOCAL):
                unique_fields["invoice_month"] = bill_date.strftime("%Y%m")
            LOG.info(f"load OCP-on-{provider.type} data for start: {start_date}, end: {end_date}")
            with schema_context(self.schema):
                days = (end_date - start_date).days
                for i in range(days):
                    baker.make_recipe(
                        daily_summary_recipe,
                        report_period=report_period,
                        cluster_id=cluster_id,
                        cluster_alias=cluster_id,
                        usage_start=start_date + timedelta(i),
                        usage_end=start_date + timedelta(i),
                        cost_entry_bill=bill,
                        tags=cycle(self.tags),
                        source_uuid=provider.uuid,
                        _quantity=len(self.tags),
                        **unique_fields,
                    )
                    baker.make_recipe(
                        project_summary_pod_recipe,
                        report_period=report_period,
                        cluster_id=cluster_id,
                        cluster_alias=cluster_id,
                        usage_start=start_date + timedelta(i),
                        usage_end=start_date + timedelta(i),
                        cost_entry_bill=bill,
                        tags=cycle(self.tags),
                        source_uuid=provider.uuid,
                        _quantity=len(self.tags),
                        **unique_fields,
                    )
                    baker.make_recipe(
                        project_summary_storage_recipe,
                        report_period=report_period,
                        cluster_id=cluster_id,
                        cluster_alias=cluster_id,
                        usage_start=start_date + timedelta(i),
                        usage_end=start_date + timedelta(i),
                        cost_entry_bill=bill,
                        tags=cycle(self.tags),
                        source_uuid=provider.uuid,
                        _quantity=len(self.tags),
                        **unique_fields,
                    )
        with dbaccessor(self.schema) as accessor:
            # update tags
            cls_method = getattr(accessor, tags_update_method)
            cls_method([bill.id for bill in bills], self.first_start_date, self.last_end_date)

            # update ui tables
            sql_params = {
                "schema_name": self.schema,
                "start_date": self.first_start_date,
                "end_date": self.last_end_date,
                "source_uuid": provider.uuid,
                "cluster_id": cluster_id,
                "cluster_alias": cluster_id,
            }
            cls_method = getattr(accessor, ui_update_method)
            cls_method(sql_params)

        refresh_materialized_views(self.schema, provider_type, provider_uuid=provider.uuid, synchronous=True)
