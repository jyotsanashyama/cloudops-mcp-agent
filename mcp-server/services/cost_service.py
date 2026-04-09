"""Service layer for AWS cost and usage logic.

Implements helper functions that wrap AWS Cost Explorer via boto3. These
functions are called by MCP tools defined in `mcp_entrypoint.py`.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List

from services.aws_clients import get_ce_client


def _resolve_time_range(time_range: str) -> Dict[str, str]:
    """Convert a logical time_range string into Start/End date strings."""

    now = datetime.now(timezone.utc)
    if time_range == "last_7_days":
        delta = 7
    elif time_range == "last_30_days":
        delta = 30
    elif time_range == "last_90_days":
        delta = 90
    else:
        # Default to last 7 days if an unknown value is provided
        delta = 7

    start = now - timedelta(days=delta)
    return {
        "Start": start.date().isoformat(),
        "End": now.date().isoformat(),
    }


def get_cost_summary(time_range: str, granularity: str) -> Dict[str, Any]:
    """Get a summarized view of AWS costs over a time range.

    Uses Cost Explorer `get_cost_and_usage` with the UnblendedCost metric.
    """

    try:
        ce = get_ce_client()
        time_period = _resolve_time_range(time_range)

        resp = ce.get_cost_and_usage(
            TimePeriod=time_period,
            Granularity=granularity,
            Metrics=["UnblendedCost"],
        )

        periods: List[Dict[str, Any]] = []
        total_cost = 0.0
        currency = "USD"

        for result in resp.get("ResultsByTime", []):
            amount_str = (
                result.get("Total", {})
                .get("UnblendedCost", {})
                .get("Amount", "0")
            )
            unit = (
                result.get("Total", {})
                .get("UnblendedCost", {})
                .get("Unit", currency)
            )
            try:
                amount = float(amount_str)
            except (TypeError, ValueError):
                amount = 0.0

            total_cost += amount
            currency = unit or currency

            periods.append(
                {
                    "start": result.get("TimePeriod", {}).get("Start"),
                    "end": result.get("TimePeriod", {}).get("End"),
                    "cost": amount,
                }
            )

        return {
            "time_range": time_range,
            "granularity": granularity,
            "total_cost": round(total_cost, 4),
            "currency": currency,
            "periods": periods,
        }
    except Exception as e:
        return {"error": str(e)}


def get_costly_instances(time_range: str, top_n: int) -> Dict[str, Any]:
    """Get the most costly EC2 instances over a time range.

    Uses Cost Explorer `get_cost_and_usage` grouped by RESOURCE_ID and filtered
    to EC2 compute service.
    """

    try:
        ce = get_ce_client()
        time_period = _resolve_time_range(time_range)

        resp = ce.get_cost_and_usage(
            TimePeriod=time_period,
            Granularity="MONTHLY",
            Metrics=["UnblendedCost"],
            GroupBy=[
                {"Type": "DIMENSION", "Key": "RESOURCE_ID"},
            ],
            Filter={
                "Dimensions": {
                    "Key": "SERVICE",
                    "Values": ["Amazon Elastic Compute Cloud - Compute"],
                }
            },
        )

        costs: Dict[str, Dict[str, Any]] = {}
        currency = "USD"

        for result in resp.get("ResultsByTime", []):
            for group in result.get("Groups", []):
                keys = group.get("Keys", [])
                if not keys:
                    continue
                resource_id = keys[0]
                amount_str = (
                    group.get("Metrics", {})
                    .get("UnblendedCost", {})
                    .get("Amount", "0")
                )
                unit = (
                    group.get("Metrics", {})
                    .get("UnblendedCost", {})
                    .get("Unit", currency)
                )
                try:
                    amount = float(amount_str)
                except (TypeError, ValueError):
                    amount = 0.0

                currency = unit or currency

                entry = costs.setdefault(
                    resource_id,
                    {"resource_id": resource_id, "total_cost": 0.0},
                )
                entry["total_cost"] += amount

        # Sort by total_cost descending and take top_n
        sorted_instances = sorted(
            costs.values(),
            key=lambda x: x.get("total_cost", 0.0),
            reverse=True,
        )[:top_n]

        # Round costs for readability
        for inst in sorted_instances:
            inst["total_cost"] = round(float(inst.get("total_cost", 0.0)), 4)
            inst["currency"] = currency

        return {
            "time_range": time_range,
            "top_n": top_n,
            "instances": sorted_instances,
        }
    except Exception as e:
        return {"error": str(e)}



