from __future__ import annotations

import json
import os
from typing import Any

import boto3
from boto3.dynamodb.types import TypeDeserializer

from common.telemetry import emit

EVENTS = boto3.client("events")
DESERIALIZER = TypeDeserializer()
STATUS_BUS_NAME = os.environ.get("STATUS_BUS_NAME", "")


def _decode(image: dict[str, Any] | None) -> dict[str, Any]:
    return {key: DESERIALIZER.deserialize(value) for key, value in (image or {}).items()}


def handler(event: dict[str, Any], _context: Any) -> dict[str, Any]:
    failures = []
    for record in event.get("Records", []):
        sequence = str(record.get("dynamodb", {}).get("SequenceNumber", "unknown"))
        try:
            old = _decode(record.get("dynamodb", {}).get("OldImage"))
            new = _decode(record.get("dynamodb", {}).get("NewImage"))
            if not new or new.get("status") == old.get("status"):
                continue
            detail = {
                "schema_version": "1.0.0",
                "job_id": new["job_id"],
                "status": new["status"],
                "updated_at": new.get("updated_at"),
                "report_prefix": new.get("report_prefix"),
            }
            response = EVENTS.put_events(
                Entries=[
                    {
                        "EventBusName": STATUS_BUS_NAME,
                        "Source": "audit-lab.jobs",
                        "DetailType": "audit.status.changed",
                        "Detail": json.dumps(detail, separators=(",", ":"), sort_keys=True),
                    }
                ]
            )
            if response.get("FailedEntryCount", 0):
                raise RuntimeError("EventBridge rejected the status entry")
            emit("audit_status_published", job_id=new["job_id"], status=new["status"])
        except (KeyError, TypeError, ValueError, RuntimeError):
            failures.append({"itemIdentifier": sequence})
            emit("audit_status_publish_failed", sequence=sequence)
    return {"batchItemFailures": failures}
