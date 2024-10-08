#
# Copyright 2021 Red Hat Inc.
# SPDX-License-Identifier: Apache-2.0
#
"""Prometheus metrics."""
import logging
import time

from django.conf import settings
from django.db import connection
from django.db import InterfaceError
from django.db import OperationalError
from prometheus_client import CollectorRegistry
from prometheus_client import Counter
from prometheus_client import Gauge
from prometheus_client import multiprocess
from prometheus_client import push_to_gateway

from . import celery_app

LOG = logging.getLogger(__name__)
REGISTRY = CollectorRegistry()
multiprocess.MultiProcessCollector(REGISTRY)
DB_CONNECTION_ERRORS_COUNTER = Counter("db_connection_errors", "Number of DB connection errors")
PGSQL_GAUGE = Gauge("postgresql_schema_size_bytes", "PostgreSQL DB Size (bytes)", ["schema"])

DEFAULT = "celery"


class DatabaseStatus:
    """Database status information."""

    def connection_check(self):
        """Check DB connection."""
        try:
            connection.cursor()
            LOG.debug("DatabaseStatus.connection_check: DB connected!")
        except OperationalError as error:
            LOG.error("DatabaseStatus.connection_check: No connection to DB: %s", str(error))
            DB_CONNECTION_ERRORS_COUNTER.inc()

    def query(self, query, query_tag):
        """Execute a SQL query, format the results.

        Returns:
            [
                {col_1: <value>, col_2: value, ...},
                {col_1: <value>, col_2: value, ...},
                {col_1: <value>, col_2: value, ...},
            ]

        """
        rows = None
        for _ in range(3):
            try:
                with connection.cursor() as cursor:
                    cursor.execute(query)
                    rows = cursor.fetchall()
            except (OperationalError, InterfaceError) as exc:
                LOG.warning("DatabaseStatus.query exception: %s", exc)
                time.sleep(2)
            else:
                break
        else:
            LOG.error("DatabaseStatus.query (query: %s): Query failed to return results.", query_tag)
            return []

        if not rows:
            LOG.info("DatabaseStatus.query (query: %s): Query returned no results.", query_tag)
            return []

        # get column names
        names = [desc[0] for desc in cursor.description]

        # transform list-of-lists into list-of-dicts including column names.
        result = [dict(zip(names, row)) for row in rows if len(row) == 2]

        LOG.info("DatabaseStatus.query (query: %s): query returned.", query_tag)

        return result

    def collect(self):
        """Collect stats and report using Prometheus objects."""
        stats = self.schema_size()
        LOG.debug("Collected stats: %s", stats)
        for item in stats:
            schema = item.get("schema")
            size = item.get("size")
            if schema is not None and size is not None:
                PGSQL_GAUGE.labels(schema).set(size)

    def schema_size(self):
        """Show DB storage consumption.

        Returns:
            [
                {schema: <string>, size: <bigint> },
                {schema: <string>, size: <bigint> },
                {schema: <string>, size: <bigint> },
            ]

        """
        # sample query output:
        #
        #   schema   |   size
        # -----------+----------
        #  org1234567 | 51011584
        #
        query = """
            SELECT schema_name as schema,
                   sum(table_size)::bigint as size
            FROM (
              SELECT pg_catalog.pg_namespace.nspname as schema_name,
                     pg_relation_size(pg_catalog.pg_class.oid) as table_size
              FROM   pg_catalog.pg_class
                 JOIN pg_catalog.pg_namespace ON relnamespace = pg_catalog.pg_namespace.oid
              WHERE pg_catalog.pg_namespace.nspname NOT IN ('public', 'pg_catalog', 'pg_toast', 'information_schema')
            ) t
            GROUP BY schema_name
            ORDER BY schema_name;
        """
        return self.query(query, "DB storage consumption")


@celery_app.task(name="koku.metrics.collect_metrics", bind=True, queue=DEFAULT)
def collect_metrics(self):
    """Collect DB metrics with scheduled celery task."""
    db_status = DatabaseStatus()
    db_status.connection_check()
    db_status.collect()
    LOG.debug("Pushing stats to gateway: %s", settings.PROMETHEUS_PUSHGATEWAY)
    try:
        push_to_gateway(gateway=settings.PROMETHEUS_PUSHGATEWAY, job="koku.metrics.collect_metrics", registry=REGISTRY)
    except OSError as exc:
        LOG.error("Problem reaching pushgateway: %s", exc)
        self.update_state(state="FAILURE", meta={"result": str(exc), "traceback": str(exc.__traceback__)})
