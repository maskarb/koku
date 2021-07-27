#
# Copyright 2021 Red Hat Inc.
# SPDX-License-Identifier: Apache-2.0
#
"""Test utilities."""
import random
from datetime import timedelta
from functools import partial

from django.test.utils import override_settings
from faker import Faker
from model_bakery import baker
from tenant_schemas.utils import schema_context

from api.models import Provider
from api.report.test.util import constants
from api.report.test.util.data_loader import DataLoader
from masu.database.aws_report_db_accessor import AWSReportDBAccessor
from masu.database.azure_report_db_accessor import AzureReportDBAccessor
from masu.database.gcp_report_db_accessor import GCPReportDBAccessor
from masu.database.ocp_report_db_accessor import OCPReportDBAccessor
from masu.processor.tasks import refresh_materialized_views


class ModelBakeryDataLoader(DataLoader):
    """Loads model bakery generated test data for different source types."""

    def __init__(self, schema, customer, num_days=10):
        super().__init__(schema, customer, num_days=num_days)
        self.faker = Faker()
        self.tags = [{self.faker.slug(): self.faker.slug()} for _ in range(10)]

    def _get_bill_model(self, provider_type):
        """Return the correct model for a provider type."""
        if provider_type in (Provider.PROVIDER_AWS, Provider.PROVIDER_AWS_LOCAL):
            return "AWSCostEntryBill"
        elif provider_type in (Provider.PROVIDER_AZURE, Provider.PROVIDER_AZURE_LOCAL):
            return "AzureCostEntryBill"
        elif provider_type in (Provider.PROVIDER_GCP, Provider.PROVIDER_GCP_LOCAL):
            return "GCPCostEntryBill"
        if provider_type == Provider.PROVIDER_OCP:
            return "OCPUsageReportPeriod"

    def create_provider(self, provider_type, credentials, billing_source):
        """Create a Provider record"""
        with override_settings(AUTO_DATA_INGEST=False):
            # ocp_billing_source, _ = ProviderBillingSource.objects.get_or_create(data_source={})
            return baker.make(
                "Provider",
                type=provider_type,
                authentication__credentials=credentials,
                billing_source__data_source=billing_source,
                customer=self.customer,
            )

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

    def create_bill(self, provider_type, provider, bill_date):
        """Create a bill object for the provider"""
        with schema_context(self.schema):
            model_str = self._get_bill_model(provider_type)
            if provider_type == Provider.PROVIDER_OCP:
                return baker.make(model_str, provider=provider, report_period_start=bill_date, _fill_optional=True)
            else:
                return baker.make(model_str, provider=provider, billing_period_start=bill_date, _fill_optional=True)

    def load_aws_data(self):
        """Load AWS data for tests."""
        bills = []
        provider_type = Provider.PROVIDER_AWS_LOCAL
        role_arn = "arn:aws:iam::999999999999:role/CostManagement"
        credentials = {"role_arn": role_arn}
        billing_source = {"bucket": "test-bucket"}

        provider = self.create_provider(provider_type, credentials, billing_source)
        for start_date, end_date, bill_date in self.dates:
            self.create_manifest(provider, bill_date)
            bill = self.create_bill(provider_type, provider, bill_date)
            bills.append(bill)
            with schema_context(self.schema):
                alias = baker.make("AWSAccountAlias", account_id=bill.payer_account_id, account_alias="Test Account")
                org_unit = baker.make("AWSOrganizationalUnit", account_alias=alias, provider=provider)
                days = (end_date - start_date).days
                for i in range(days):
                    baker.make(
                        "AWSCostEntryLineItemDailySummary",
                        cost_entry_bill=bill,
                        usage_account_id=bill.payer_account_id,
                        account_alias=alias,
                        organizational_unit=org_unit,
                        usage_start=start_date + timedelta(i),
                        usage_end=start_date + timedelta(i),
                        product_code=random.choice(constants.AWS_PRODUCT_CODES),
                        instance_type=random.choice(constants.AWS_INSTANCE_TYPES),
                        tags=random.choice(self.tags),
                        source_uuid=provider.uuid,
                        _fill_optional=True,
                    )
            AWSReportDBAccessor(self.schema).populate_tags_summary_table([bill.id], start_date, end_date)
        refresh_materialized_views.s(self.schema, provider_type, provider_uuid=provider.uuid, synchronous=True).apply()

        return bills

    def load_azure_data(self):
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

        provider = self.create_provider(provider_type, credentials, billing_source)
        for start_date, end_date, bill_date in self.dates:
            self.create_manifest(provider, bill_date)
            bill = self.create_bill(provider_type, provider, bill_date)
            bills.append(bill)
            sub_guid = self.faker.uuid4()
            with schema_context(self.schema):
                days = (end_date - start_date).days
                for i in range(days):
                    baker.make(
                        "AzureCostEntryLineItemDailySummary",
                        cost_entry_bill=bill,
                        subscription_guid=sub_guid,
                        usage_start=start_date + timedelta(i),
                        usage_end=start_date + timedelta(i),
                        service_name=random.choice(constants.AZURE_SERVICE_NAMES),
                        instance_type=random.choice(constants.AZURE_INSTANCE_TYPES),
                        unit_of_measure=random.choice(constants.AZURE_UNITS_OF_MEASURE),
                        tags=random.choice(self.tags),
                        source_uuid=provider.uuid,
                        _fill_optional=True,
                    )
            AzureReportDBAccessor(self.schema).populate_tags_summary_table([bill.id], start_date, end_date)
        refresh_materialized_views.s(self.schema, provider_type, provider_uuid=provider.uuid, synchronous=True).apply()
        return bills

    def load_gcp_data(self):
        """Load Azure data for tests."""
        bills = []
        provider_type = Provider.PROVIDER_GCP_LOCAL
        credentials = {"project_id": "test_project_id"}
        billing_source = {"table_id": "test_table_id", "dataset": "test_dataset"}
        account_id = "123456789"
        provider = self.create_provider(provider_type, credentials, billing_source)
        projects = [(self.faker.slug(), self.faker.slug()) for _ in range(10)]
        for start_date, end_date, bill_date in self.dates:
            self.create_manifest(provider, bill_date)
            bill = self.create_bill(provider_type, provider, bill_date)
            bills.append(bill)
            with schema_context(self.schema):
                days = (end_date - start_date).days
                for i in range(days):
                    project = random.choice(projects)
                    service = random.choice(constants.GCP_SERVICES)
                    baker.make(
                        "GCPCostEntryLineItemDailySummary",
                        cost_entry_bill=bill,
                        account_id=account_id,
                        project_id=project[0],
                        project_name=project[1],
                        usage_start=start_date + timedelta(i),
                        usage_end=start_date + timedelta(i),
                        service_id=service[0],
                        service_alias=service[1],
                        tags=random.choice(self.tags),
                        source_uuid=provider.uuid,
                        _fill_optional=True,
                    )
            GCPReportDBAccessor(self.schema).populate_tags_summary_table([bill.id], start_date, end_date)
        refresh_materialized_views.s(self.schema, provider_type, provider_uuid=provider.uuid, synchronous=True).apply()
        return bills

    def load_openshift_data(self, cluster_id):
        """Load OpenShift data for tests."""
        report_periods = []
        provider_type = Provider.PROVIDER_OCP
        credentials = {"cluster_id": cluster_id}
        billing_source = {}

        provider = self.create_provider(provider_type, credentials, billing_source)
        for start_date, end_date, bill_date in self.dates:
            self.create_manifest(provider, bill_date)
            report_period = self.create_bill(provider_type, provider, bill_date)
            report_periods.append(report_period)
            with schema_context(self.schema):
                days = (end_date - start_date).days
                for i in range(days):
                    baker.make(
                        "OCPUsageLineItemDailySummary",
                        report_period=report_period,
                        cluster_id=cluster_id,
                        cluster_alias=cluster_id,
                        data_source=random.choice(constants.OCP_DATA_SOURCES),
                        usage_start=start_date + timedelta(i),
                        usage_end=start_date + timedelta(i),
                        pod_labels=random.choice(self.tags),
                        volume_labels=random.choice(self.tags),
                        source_uuid=provider.uuid,
                        _fill_optional=True,
                    )
            OCPReportDBAccessor(self.schema).populate_pod_label_summary_table([report_period.id], start_date, end_date)
        refresh_materialized_views.s(self.schema, provider_type, provider_uuid=provider.uuid, synchronous=True).apply()
        return report_periods

    def load_openshift_on_cloud_data(self, provider_type, cluster_id, bills, report_periods):
        """Load OCP on AWS Daily Summary table."""
        if provider_type in (Provider.PROVIDER_AWS, Provider.PROVIDER_AWS_LOCAL):
            daily_summary_table = "OCPAWSCostLineItemDailySummary"
            project_summary_table = "OCPAWSCostLineItemProjectDailySummary"
            update_method = partial(AWSReportDBAccessor(self.schema).populate_ocp_on_aws_tags_summary_table)
        elif provider_type in (Provider.PROVIDER_AZURE, Provider.PROVIDER_AZURE_LOCAL):
            daily_summary_table = "OCPAzureCostLineItemDailySummary"
            project_summary_table = "OCPAzureCostLineItemProjectDailySummary"
            update_method = partial(AzureReportDBAccessor(self.schema).populate_ocp_on_azure_tags_summary_table)

        provider = Provider.objects.filter(type=provider_type).first()
        for dates, bill, report_period in zip(self.dates, bills, report_periods):
            start_date = dates[0]
            end_date = dates[1]
            with schema_context(self.schema):
                days = (end_date - start_date).days
                for i in range(days):
                    baker.make(
                        daily_summary_table,
                        report_period=report_period,
                        cluster_id=cluster_id,
                        cluster_alias=cluster_id,
                        usage_start=start_date + timedelta(i),
                        usage_end=start_date + timedelta(i),
                        cost_entry_bill=bill,
                        tags=random.choice(self.tags),
                        source_uuid=provider.uuid,
                        _fill_optional=True,
                    )
                    baker.make(
                        project_summary_table,
                        report_period=report_period,
                        cluster_id=cluster_id,
                        cluster_alias=cluster_id,
                        data_source=random.choice(constants.OCP_DATA_SOURCES),
                        usage_start=start_date + timedelta(i),
                        usage_end=start_date + timedelta(i),
                        pod_labels=random.choice(self.tags),
                        cost_entry_bill=bill,
                        tags=random.choice(self.tags),
                        source_uuid=provider.uuid,
                        _fill_optional=True,
                    )
            update_method([bill.id], start_date, end_date)

        refresh_materialized_views.s(self.schema, provider_type, provider_uuid=provider.uuid, synchronous=True).apply()
