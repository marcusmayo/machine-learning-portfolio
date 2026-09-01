from __future__ import annotations

import hashlib
import json
import os
import re
from typing import Any
from urllib.parse import unquote_plus

import boto3
from botocore.exceptions import ClientError

from common.telemetry import emit

SFN = boto3.client("stepfunctions")
STATE_MACHINE_ARN = os.environ.get("STATE_MACHINE_ARN", "")
SUBMISSION_BUCKET = os.environ.get("SUBMISSION_BUCKET", "")
KEY_PATTERN = re.compile(r"^submissions/([a-f0-9]{24})/template\.yaml$")


def _submission(record: dict[str, Any]) -> dict[str, str]:
    envelope = json.loads(record["body"])
    detail = envelope["detail"]
    bucket = detail["bucket"]["name"]
    key = unquote_plus(detail["object"]["key"])
    version = str(detail["object"].get("version-id") or "")
    match = KEY_PATTERN.fullmatch(key)
    if bucket != SUBMISSION_BUCKET or not match:
        raise ValueError("event is outside the exact submission bucket/key contract")
    return {"job_id": match.group(1), "bucket": bucket, "key": key, "version_id": version}


def handler(event: dict[str, Any], _context: Any) -> dict[str, Any]:
    failures = []
    for record in event.get("Records", []):
        message_id = str(record.get("messageId", "unknown"))
        try:
            submission = _submission(record)
            identity = "|".join(
                [submission["bucket"], submission["key"], submission["version_id"]]
            )
            suffix = hashlib.sha256(identity.encode("utf-8")).hexdigest()[:12]
            execution_name = f"audit-{submission['job_id']}-{suffix}"
            SFN.start_execution(
                stateMachineArn=STATE_MACHINE_ARN,
                name=execution_name,
                input=json.dumps(submission, separators=(",", ":"), sort_keys=True),
            )
            emit("audit_execution_started", job_id=submission["job_id"], execution=execution_name)
        except ClientError as exc:
            if exc.response.get("Error", {}).get("Code") == "ExecutionAlreadyExists":
                emit("audit_execution_duplicate", message_id=message_id)
                continue
            failures.append({"itemIdentifier": message_id})
            emit("audit_execution_start_failed", message_id=message_id, error_code="AWS_CLIENT_ERROR")
        except (KeyError, TypeError, ValueError, json.JSONDecodeError):
            failures.append({"itemIdentifier": message_id})
            emit("audit_event_rejected", message_id=message_id, error_code="INVALID_EVENT")
    return {"batchItemFailures": failures}
