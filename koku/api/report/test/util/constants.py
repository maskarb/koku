#
# Copyright 2021 Red Hat Inc.
# SPDX-License-Identifier: Apache-2.0
#
AWS_INSTANCE_TYPES = ("db.t3.medium", "db.r5.2xlarge", "m5.large", "r4.large", "t2.micro", None)
AWS_PRODUCT_CODES = ("AmazonRDS", "AmazonElastiCache", "AmazonS3", "AmazonVPC", "AmazonEC2")

AZURE_SERVICES = (
    ("SQL Database", {"type": None, "id": None}, "Hrs"),
    ("Virtual Machines", {"type": "Standard_A0", "id": "id1"}, "Hrs"),
    ("Virtual Machines", {"type": "Standard_B2s", "id": "id2"}, "Hrs"),
    ("Virtual Network", {"type": None, "id": None}, ""),
    ("DNS", {"type": None, "id": None}, ""),
    ("Load Balancer", {"type": None, "id": None}, ""),
    ("General Block Blob", {"type": None, "id": None}, "GB-Mo"),
    ("Blob Storage", {"type": None, "id": None}, "GB-Mo"),
    ("Standard SSD Managed Disks", {"type": None, "id": None}, "GB-Mo"),
)

GCP_INSTANCE_TYPES = ()
GCP_SERVICES = (
    ("6F81-5844-456A", "Compute Engine", "Instance Core running", "hour"),
    ("1111-581D-38E5", "SQL Database", "Storage PD Snapshot", "gibibyte month"),
    ("95FF-2EF5-5EA1", "Cloud Storage", "Standard Storage US Regional", "gibibyte month"),
    ("12B3-1234-JK3C", "Network", "ManagedZone", "seconds"),
    ("23C3-JS3K-SDL3", "VPC", "ManagedZone", "seconds"),
)

OCP_DATA_SOURCES = ("Pod", "Storage")
# Node tuple ex ((node name, resource id, cpu, memory, volume tuple))
OCP_NODES = (
    ("node_1", "i-00000001", 4, 16),
    ("node_2", "i-00000002", 8, 32),
    ("node_3", "i-00000003", 8, 32),
    ("node_4", "i-00000004", 4, 16),
    ("node_5", "i-00000005", 8, 32),
    ("node_6", "i-00000006", 8, 32),
)
OCP_PVCS = (
    ("pvc_1", "volume_1", "bronze", 512),
    ("pvc_2", "volume_2", "silver", 128),
    ("pvc_3", "volume_3", "gold", 256),
    ("pvc_4", "volume_4", "platinum", 1024),
    ("pvc_5", "volume_5", "adamantium", 512),
    ("pvc_6", "volume_6", "vibranium", 1024),
)
