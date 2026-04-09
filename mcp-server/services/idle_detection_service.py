"""Service layer for idle EC2 instance detection.

Implements heuristics using CloudWatch CPU metrics and EC2 metadata.
These functions are called from MCP tools defined in `mcp_entrypoint.py`.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List

from services.aws_clients import get_cw_client, get_ec2_client


def detect_idle_instances(
    region: str,
    lookback_hours: int,
    cpu_threshold_percent: float,
) -> Dict[str, Any]:
    """Detect idle EC2 instances based on average CPU utilization.

    An instance is considered idle if:
    - Average CPU < cpu_threshold_percent over the lookback window, OR
    - No CloudWatch datapoints are returned at all.
    """

    try:
        ec2 = get_ec2_client(region=region)
        cw = get_cw_client(region=region)

        # 1. Discover running instances
        resp = ec2.describe_instances()
        running_instances: List[Dict[str, Any]] = []

        for reservation in resp.get("Reservations", []):
            for inst in reservation.get("Instances", []):
                state = (inst.get("State") or {}).get("Name")
                if state != "running":
                    continue

                instance_id = inst.get("InstanceId")
                instance_type = inst.get("InstanceType")

                name = None
                for tag in inst.get("Tags", []) or []:
                    if tag.get("Key") == "Name":
                        name = tag.get("Value")
                        break

                running_instances.append(
                    {
                        "instance_id": instance_id,
                        "instance_type": instance_type,
                        "name": name,
                    }
                )

        total_running = len(running_instances)

        # 2. For each running instance, query CloudWatch CPUUtilization
        end_time = datetime.now(timezone.utc)
        start_time = end_time - timedelta(hours=lookback_hours)
        period = lookback_hours * 3600

        idle_instances: List[Dict[str, Any]] = []

        for inst in running_instances:
            instance_id = inst["instance_id"]

            cw_resp = cw.get_metric_statistics(
                Namespace="AWS/EC2",
                MetricName="CPUUtilization",
                Dimensions=[
                    {"Name": "InstanceId", "Value": instance_id},
                ],
                StartTime=start_time,
                EndTime=end_time,
                Period=period,
                Statistics=["Average"],
            )

            datapoints = cw_resp.get("Datapoints", [])
            if not datapoints:
                idle_instances.append(
                    {
                        "instance_id": instance_id,
                        "instance_type": inst["instance_type"],
                        "name": inst["name"],
                        "avg_cpu": None,
                        "reason": "no_metrics",
                    }
                )
                continue

            # There should be at most one datapoint for this window; take the first.
            avg_cpu = float(datapoints[0].get("Average", 0.0))

            if avg_cpu < cpu_threshold_percent:
                idle_instances.append(
                    {
                        "instance_id": instance_id,
                        "instance_type": inst["instance_type"],
                        "name": inst["name"],
                        "avg_cpu": avg_cpu,
                        "reason": "below_threshold",
                    }
                )

        return {
            "region": region,
            "lookback_hours": lookback_hours,
            "cpu_threshold_percent": cpu_threshold_percent,
            "total_running": total_running,
            "idle_count": len(idle_instances),
            "idle_instances": idle_instances,
        }
    except Exception as e:
        return {"error": str(e)}

