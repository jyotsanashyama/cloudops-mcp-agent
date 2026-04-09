"""Service layer for EC2-related business logic.

TODO: Implement EC2 operations such as listing instances, resolving IPs, detecting idle instances,
and stopping instances, delegating AWS calls to the aws_clients module.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from services.aws_clients import get_ec2_client
from concurrent.futures import ThreadPoolExecutor, as_completed

def _normalize_tags(raw_tags: Optional[List[Dict[str, Any]]]) -> Dict[str, str]:
    """Convert AWS tag list to a simple dict."""

    if not raw_tags:
        return {}
    out: Dict[str, str] = {}
    for t in raw_tags:
        k = t.get("Key")
        v = t.get("Value")
        if isinstance(k, str) and isinstance(v, str):
            out[k] = v
    return out


def _to_iso(dt: Optional[datetime]) -> Optional[str]:
    """Convert datetime to ISO string (JSON-safe)."""

    if dt is None:
        return None
    return dt.isoformat()


def list_instances(region: Optional[str] = None) -> List[Dict[str, Any]]:
    """List EC2 instances in the specified region.

    LEVEL 0: minimal happy-path implementation.
    - No auth, caching, rate limiting, error normalization, or tool registry.
    - Returns a JSON-serializable list of instance summaries.
    """

    ec2 = get_ec2_client(region=region)
    resp = ec2.describe_instances()

    instances: List[Dict[str, Any]] = []

    for reservation in resp.get("Reservations", []):
        for inst in reservation.get("Instances", []):
            instances.append(
                {
                    "instance_id": inst.get("InstanceId"),
                    "region": region or ec2.meta.region_name,
                    "state": (inst.get("State") or {}).get("Name"),
                    "instance_type": inst.get("InstanceType"),
                    "public_ip": inst.get("PublicIpAddress"),
                    "private_ip": inst.get("PrivateIpAddress"),
                    "launch_time": _to_iso(inst.get("LaunchTime")),
                    "tags": _normalize_tags(inst.get("Tags")),
                }
            )

    return instances


def list_all_regions() -> list:
    """Fetch all enabled AWS regions dynamically."""
    ec2 = get_ec2_client()  # uses default region just to make the API call
    resp = ec2.describe_regions(Filters=[{"Name": "opt-in-status", "Values": ["opt-in-not-required", "opted-in"]}])
    return [r["RegionName"] for r in resp.get("Regions", [])]


def list_instances_all_regions() -> list:
    """Scan all AWS regions  in parallel and return instances found in any of them."""
    regions = list_all_regions()
    all_instances = []
     # Run all region scans concurrently using threads
    # boto3 is not async-native, so ThreadPoolExecutor is the right tool
    with ThreadPoolExecutor(max_workers=10) as executor:
        future_to_region = {
            executor.submit(list_instances, region): region
            for region in regions
        }
        for future in as_completed(future_to_region):
            try:
                instances = future.result()
                all_instances.extend(instances)
            except Exception:
                continue  # skip failed regions silently

    return all_instances