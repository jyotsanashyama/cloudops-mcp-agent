"""AWS client factory and thin boto3 wrappers.

TODO: Provide functions to create and configure boto3 clients for EC2, Cost Explorer,
and CloudWatch with standardized retry and error handling behavior.
"""

from dotenv import load_dotenv

load_dotenv()

import os
from typing import Optional

import boto3


def get_default_region() -> str:
    """Resolve the default AWS region for v0/v1 usage."""

    return (
        os.getenv("AWS_DEFAULT_REGION")
        or os.getenv("AWS_REGION")
        or "us-east-1"
    )


def get_ec2_client(region: Optional[str] = None):
    """Create a boto3 EC2 client."""

    resolved_region = region or get_default_region()
    session = boto3.session.Session()
    return session.client("ec2", region_name=resolved_region)


def get_ce_client(region: Optional[str] = None):
    """Create a boto3 Cost Explorer client.

    NOTE: Cost Explorer is a global service and only operates in us-east-1.
    Any provided region parameter is ignored; the client always uses us-east-1.
    """

    session = boto3.session.Session()
    return session.client("ce", region_name="us-east-1")


def get_cw_client(region: Optional[str] = None):
    """Create a boto3 CloudWatch client for the given region.

    CloudWatch is regional and should match the region of the EC2 resources
    being monitored. If no region is provided, fall back to the default.
    """

    resolved_region = region or get_default_region()
    session = boto3.session.Session()
    return session.client("cloudwatch", region_name=resolved_region)



