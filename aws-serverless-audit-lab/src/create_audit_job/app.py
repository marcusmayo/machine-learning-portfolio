from __future__ import annotations

import base64
import binascii
import hashlib
import json
import os
import re
from datetime import UTC, datetime, timedelta
from typing import Any

import boto3
from botocore.exceptions import ClientError

from common.telemetry import emit

DDB = boto3.client("dynamodb")
S3 = boto3.client("s3")
JOBS_TABLE = os.environ.get("JOBS_TABLE", "AuditJobs")
SUBMISSION_BUCKET = os.environ.get("SUBMISSION_BUCKET", "audit-submissions")
MAX_TEMPLATE_BYTES = int(os.environ.get("MAX_TEMPLATE_BYTES", "524288"))
ALLOWED_FIELDS = {"name", "template_format"}
SAFE_NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9 ._-]{0,79}$")


def _response(status: int, body: dict[str, Any]) -> dict[str, Any]:
    return {
        "statusCode": status,
        "headers": {
            "content-type": "application/json",
            "cache-control": "no-store",
        },
        "body": json.dumps(body, separators=(",", ":"), sort_keys=True),
    }


def _header(event: dict[str, Any], name: str) -> str:
    target = name.lower()
    for key, value in (event.get("headers") or {}).items():
        if key.lower() == target:
            return str(value).strip()
    return ""


def _body(event: dict[str, Any]) -> dict[str, Any]:
    raw = event.get("body") or "{}"
    if event.get("isBase64Encoded"):
        raw = base64.b64decode(raw, validate=True).decode("utf-8")
    parsed = json.loads(raw)
    if not isinstance(parsed, dict):
        raise ValueError("body must be a JSON object")
    unknown = sorted(set(parsed) - ALLOWED_FIELDS)
    if unknown:
        raise ValueError(f"unknown fields: {', '.join(unknown)}")
    name = str(parsed.get("name", "IaC audit task")).strip()
    template_format = str(parsed.get("template_format", "sam")).lower()
    if not SAFE_NAME.fullmatch(name):
        raise ValueError("name must be 1-80 safe display characters")
    if template_format not in {"sam", "cloudformation"}:
        raise ValueError("template_format must be sam or cloudformation")
    return {"name": name, "template_format": template_format}


def _presigned_upload(job_id: str) -> dict[str, Any]:
    key = f"submissions/{job_id}/template.yaml"
    fields = {"Content-Type": "application/x-yaml"}
    conditions: list[Any] = [
        {"Content-Type": "application/x-yaml"},
        ["content-length-range", 1, MAX_TEMPLATE_BYTES],
    ]
    upload = S3.generate_presigned_post(
        Bucket=SUBMISSION_BUCKET,
        Key=key,
        Fields=fields,
        Conditions=conditions,
        ExpiresIn=900,
    )
    return {
        "method": "POST",
        "url": upload["url"],
        "fields": upload["fields"],
        "expires_in_seconds": 900,
        "max_bytes": MAX_TEMPLATE_BYTES,
        "content_type": "application/x-yaml",
        "object_key": key,
    }


def handler(event: dict[str, Any], _context: Any) -> dict[str, Any]:
    idempotency_key = _header(event, "idempotency-key")
    if not 8 <= len(idempotency_key) <= 200:
        return _response(400, {"error": "idempotency-key must be 8-200 characters"})
    try:
        request = _body(event)
    except (ValueError, json.JSONDecodeError, UnicodeDecodeError, binascii.Error) as exc:
        return _response(400, {"error": str(exc)})

    canonical = json.dumps(request, separators=(",", ":"), sort_keys=True)
    request_hash = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    job_id = hashlib.sha256(idempotency_key.encode("utf-8")).hexdigest()[:24]
    now = datetime.now(UTC)
    item = {
        "job_id": {"S": job_id},
        "request_hash": {"S": request_hash},
        "name": {"S": request["name"]},
        "template_format": {"S": request["template_format"]},
        "status": {"S": "PENDING_UPLOAD"},
        "version": {"N": "1"},
        "created_at": {"S": now.isoformat()},
        "updated_at": {"S": now.isoformat()},
        "expires_at": {"N": str(int((now + timedelta(days=30)).timestamp()))},
    }
    created = True
    try:
        DDB.put_item(
            TableName=JOBS_TABLE,
            Item=item,
            ConditionExpression="attribute_not_exists(job_id)",
        )
    except ClientError as exc:
        if exc.response.get("Error", {}).get("Code") != "ConditionalCheckFailedException":
            raise
        created = False
        existing = DDB.get_item(
            TableName=JOBS_TABLE,
            Key={"job_id": {"S": job_id}},
            ConsistentRead=True,
        ).get("Item", {})
        if existing.get("request_hash", {}).get("S") != request_hash:
            emit("idempotency_conflict", job_id=job_id)
            return _response(409, {"error": "idempotency-key was already used for different input"})

    emit("audit_job_created" if created else "audit_job_reused", job_id=job_id)
    return _response(
        201 if created else 200,
        {
            "job_id": job_id,
            "status": "PENDING_UPLOAD",
            "idempotent_replay": not created,
            "upload": _presigned_upload(job_id),
        },
    )
