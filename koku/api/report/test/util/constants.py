#
# Copyright 2021 Red Hat Inc.
# SPDX-License-Identifier: Apache-2.0
#
AWS_INSTANCE_TYPES = ("db.t3.medium", "db.r5.2xlarge", "m5.large", "r4.large", "t2.micro", None)
AWS_PRODUCT_CODES = ("AmazonRDS", "AmazonElastiCache", "AmazonS3", "AmazonVPC", "AmazonEC2")

AZURE_INSTANCE_TYPES = ("Standard_A0", "Standard_B2s", None)
AZURE_SERVICE_NAMES = ("SQL Database", "Virtual Machines", "Virtual Network", "DNS", "Load Balancer")
AZURE_UNITS_OF_MEASURE = ("Hrs", "GB-Mo")

GCP_INSTANCE_TYPES = ()
GCP_SERVICES = (
    ("6F81-5844-456A", "Compute Engine"),
    ("24E6-581D-38E5", "Big Query"),
    ("FA26-5236-B8B5", "Cloud DNS"),
    ("1111-581D-38E5", "SQL Database"),
)

OCP_DATA_SOURCES = ("Pod", "Storage")
