"""MCP entrypoint for the CloudOps MCP Server.
Exposes 4 tools over stdio using the official mcp Python SDK.
All tools delegate to services/ which use boto3 to talk to AWS.
Transport: stdio — run with: python mcp_entrypoint.py
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from mcp.server.fastmcp import FastMCP

from services.ec2_service import list_instances, list_instances_all_regions
from services.cost_service import get_cost_summary as _cost_summary, get_costly_instances as _costly_instances
from services.idle_detection_service import detect_idle_instances as detect_idle


mcp = FastMCP("cloudops-mcp")


@mcp.tool()
async def list_ec2_instances(region: str = "ap-south-1") -> Dict[str, Any]:
    """List EC2 instances in the given AWS region.

    This tool delegates directly to `app.services.ec2_service.list_instances`.
    """

    instances = list_instances(region=region)
    return {"region": region, "instances": instances}


@mcp.tool()
async def list_all_ec2_instances():
    """Scan ALL AWS regions automatically and return every EC2 instance found."""
    result = list_instances_all_regions()
    return {"total": len(result), "instances": result}

@mcp.tool()
async def get_cost_summary(
    time_range: str = "last_7_days",
    granularity: str = "DAILY",
    group_by: Optional[str] = None,
    tag_key: Optional[str] = None,
) -> Dict[str, Any]:
    """Get AWS cost summary for a time range."""

    # NOTE: group_by and tag_key parameters are currently unused but kept for
    # future expansion of the underlying cost service.
    return _cost_summary(time_range=time_range, granularity=granularity)


@mcp.tool()
async def get_costly_instances(
    time_range: str = "last_30_days",
    min_monthly_cost: Optional[float] = None,
    top_n: int = 10,
) -> Dict[str, Any]:
    """Find the most costly EC2 instances over a given time range."""

    # NOTE: min_monthly_cost is currently unused; filtering is left to the client
    # or can be added later in the service layer.
    return _costly_instances(time_range=time_range, top_n=top_n)


@mcp.tool()
async def detect_idle_instances(
    region: str = "ap-south-1",
    lookback_hours: int = 24,
    cpu_threshold_percent: float = 5.0,
) -> Dict[str, Any]:
    """Detect idle EC2 instances based on basic utilization thresholds."""

    return detect_idle(
        region=region,
        lookback_hours=lookback_hours,
        cpu_threshold_percent=cpu_threshold_percent,
    )



if __name__ == "__main__":
   mcp.run(transport="stdio")