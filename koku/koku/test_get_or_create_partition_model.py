#
# Copyright 2021 Red Hat Inc.
# SPDX-License-Identifier: Apache-2.0
#
from unittest.mock import patch

from django.db.models.base import ModelBase
from tenant_schemas.utils import schema_context

from . import database as kdb
from api.iam.test.iam_test_case import IamTestCase


PartitionedTable = kdb.get_model("partitioned_tables")


class TestGetOrCreatePartitionModel(IamTestCase):
    def _get_no_model_partition_record(self):
        partition_rec = None
        with schema_context(self.schema_name):
            while partition_rec in PartitionedTable.objects.filter(partition_parameters__default=True):
                if partition_rec.table_name not in kdb.DB_MODELS:
                    return partition_rec
        return None

    def test_create(self):
        """Test that a new ORM model class can be created"""
        partition_rec = self._get_no_model_partition_record()

        with self.assertRaises(KeyError):
            kdb.get_model(partition_rec.table_name)

        partition_model = kdb._create_partition_model(partition_rec)
        partition_model_2 = kdb.get_model(partition_rec.table_name)

        self.assertEqual(partition_model, partition_model_2)

    def test_get_or_create(self):
        """Test that get_or_create functionality works"""
        partition_rec = self._get_no_model_partition_record()

        with self.assertRaises(KeyError):
            kdb.get_model(partition_rec.table_name)

        with patch("koku.database._create_partition_model") as cpm:
            partition_model = kdb.get_or_create_partition_model(partition_rec)
            cpm.assert_called()

        partition_model = kdb.get_or_create_partition_model(partition_rec)

        with patch("koku.database._create_partition_model") as cpm:
            partition_model2 = kdb.get_or_create_partition_model(partition_rec)
            cpm.assert_not_called()
            self.assertEqual(partition_model, partition_model2)

    def test_partition_model_getter(self):
        """Test that a partition model can be created from a PartitionTable instance"""
        partition_rec = self._get_no_model_partition_record()
        partition_model = partition_rec.get_partition_model()
        self.assertTrue(isinstance(partition_model, ModelBase))
