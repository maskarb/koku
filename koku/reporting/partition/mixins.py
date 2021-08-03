import datetime
import logging

from dateutil.relativedelta import relativedelta

from koku.database import get_model


LOG = logging.getLogger(__name__)


class PartitionMixin:
    def _handle_partitions(self, table_names, start_date, end_date):
        if isinstance(start_date, datetime.datetime):
            start_date = start_date.date()
        if isinstance(end_date, datetime.datetime):
            end_date = end_date.date()

        PartitionedTable = get_model("PartitionedTable")
        month_interval = relativedelta(months=1)

        for table_name in table_names:
            tmplpart = PartitionedTable.objects.filter(
                schema_name=self._schema, partition_of_table_name=table_name, partition_type=PartitionedTable.RANGE
            ).first()
            if tmplpart:
                partition_start = start_date.replace(day=1)
                needed_partition = None
                partition_col = tmplpart.partition_col
                newpart_vals = dict(
                    schema_name=self._schema,
                    table_name=None,
                    partition_of_table_name=table_name,
                    partition_type=PartitionedTable.RANGE,
                    partition_col=partition_col,
                    partition_parameters={"default": False, "from": None, "to": None},
                    active=True,
                )
                for _ in range(relativedelta(end_date.replace(day=1), partition_start).months + 1):
                    if needed_partition is None:
                        needed_partition = partition_start
                    else:
                        needed_partition = needed_partition + month_interval

                    partition_name = f"{table_name}_{needed_partition.strftime('%Y_%m')}"
                    newpart_vals["table_name"] = partition_name
                    newpart_vals["partition_parameters"]["from"] = str(needed_partition)
                    newpart_vals["partition_parameters"]["to"] = str(needed_partition + month_interval)
                    # Successfully creating a new record will also create the partition
                    res = PartitionedTable.objects.get_or_create(
                        defaults=newpart_vals,
                        schema_name=self._schema,
                        partition_of_table_name=table_name,
                        table_name=partition_name,
                    )
                    if res[1]:
                        LOG.info(f"Created partition {self._schema}.{partition_name}")
            else:
                LOG.error(
                    f"Expecting at least 1 tracking record for partitioned table {table_name} "
                    + "but found none. Cannot create partitions."
                )
