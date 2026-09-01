from __future__ import annotations

import hashlib
import json
import os
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import boto3
from botocore.exceptions import ClientError

from audit.audit_template import audit_text, render_markdown, render_sarif
from src.common.telemetry import emit

S3 = boto3.client("s3")
DDB = boto3.client("dynamodb")
MAX_TEMPLATE_BYTES = int(os.environ.get("MAX_TEMPLATE_BYTES", "524288"))
SUBMISSION_BUCKET = os.environ.get("SUBMISSION_BUCKET", "")
REPORT_BUCKET = os.environ.get("REPORT_BUCKET", "")
JOBS_TABLE = os.environ.get("JOBS_TABLE", "")


def _object_args(event: dict[str, Any]) -> dict[str, Any]:
    args: dict[str, Any] = {"Bucket": event["bucket"], "Key": event["key"]}
    if event.get("version_id"):
        args["VersionId"] = event["version_id"]
    return args


def validate_submission(event: dict[str, Any], _context: Any) -> dict[str, Any]:
    if event.get("bucket") != SUBMISSION_BUCKET:
        raise ValueError("submission bucket does not match the configured boundary")
    if event.get("key") != f"submissions/{event.get('job_id')}/template.yaml":
        raise ValueError("submission key does not match the job boundary")
    metadata = S3.head_object(**_object_args(event))
    size = int(metadata.get("ContentLength", 0))
    content_type = str(metadata.get("ContentType", "")).split(";", 1)[0].lower()
    if not 1 <= size <= MAX_TEMPLATE_BYTES:
        raise ValueError("template size is outside the allowed range")
    if content_type not in {"application/x-yaml", "application/yaml", "text/yaml"}:
        raise ValueError("template content type is not YAML")
    now = datetime.now(UTC).isoformat()
    DDB.update_item(
        TableName=JOBS_TABLE,
        Key={"job_id": {"S": event["job_id"]}},
        UpdateExpression=(
            "SET #status=:running, updated_at=:now, "
            "#version=if_not_exists(#version,:zero)+:one"
        ),
        ConditionExpression="attribute_exists(job_id) AND #status IN (:pending,:running)",
        ExpressionAttributeNames={"#status": "status", "#version": "version"},
        ExpressionAttributeValues={
            ":pending": {"S": "PENDING_UPLOAD"},
            ":running": {"S": "RUNNING"},
            ":now": {"S": now},
            ":zero": {"N": "0"},
            ":one": {"N": "1"},
        },
    )
    emit("submission_validated", job_id=event["job_id"], bytes=size)
    return {**event, "content_length": size}


def run_audit(event: dict[str, Any], _context: Any) -> dict[str, Any]:
    response = S3.get_object(**_object_args(event))
    raw = response["Body"].read(MAX_TEMPLATE_BYTES + 1)
    if len(raw) > MAX_TEMPLATE_BYTES:
        raise ValueError("template exceeded the allowed read bound")
    text = raw.decode("utf-8")
    source = f"s3://{event['bucket']}/{event['key']}"
    report = audit_text(text, source=source, base_dir=Path("/tmp/submitted-template"))
    emit(
        "template_audited",
        job_id=event["job_id"],
        decision=report["decision"],
        findings=report["finding_count"],
    )
    return {**event, "report": report}


def _put_once(key: str, body: bytes, content_type: str, digest: str) -> None:
    try:
        S3.put_object(
            Bucket=REPORT_BUCKET,
            Key=key,
            Body=body,
            ContentType=content_type,
            ServerSideEncryption="AES256",
            Metadata={"sha256": digest},
            IfNoneMatch="*",
        )
    except ClientError as exc:
        if exc.response.get("Error", {}).get("Code") not in {"PreconditionFailed", "412"}:
            raise
        existing = S3.head_object(Bucket=REPORT_BUCKET, Key=key)
        if existing.get("Metadata", {}).get("sha256") != digest:
            raise RuntimeError("existing report object failed the content-hash check") from exc


def persist_report(event: dict[str, Any], _context: Any) -> dict[str, Any]:
    report = event["report"]
    canonical = json.dumps(report, separators=(",", ":"), sort_keys=True).encode("utf-8")
    report_sha = hashlib.sha256(canonical).hexdigest()
    prefix = f"reports/{event['job_id']}/{report['template_sha256']}"
    artifacts = {
        f"{prefix}/report.json": (canonical, "application/json"),
        f"{prefix}/report.md": (render_markdown(report).encode("utf-8"), "text/markdown"),
        f"{prefix}/report.sarif": (
            json.dumps(render_sarif(report), separators=(",", ":"), sort_keys=True).encode("utf-8"),
            "application/sarif+json",
        ),
    }
    for key, (body, content_type) in artifacts.items():
        _put_once(key, body, content_type, hashlib.sha256(body).hexdigest())

    now = datetime.now(UTC).isoformat()
    DDB.update_item(
        TableName=JOBS_TABLE,
        Key={"job_id": {"S": event["job_id"]}},
        UpdateExpression=(
            "SET #status=:completed, report_prefix=:prefix, report_sha256=:digest, "
            "template_sha256=:template_digest, updated_at=:now, #version=if_not_exists(#version,:zero)+:one"
        ),
        ConditionExpression="attribute_exists(job_id) AND #status IN (:running,:completed)",
        ExpressionAttributeNames={"#status": "status", "#version": "version"},
        ExpressionAttributeValues={
            ":completed": {"S": "COMPLETED"},
            ":running": {"S": "RUNNING"},
            ":prefix": {"S": prefix},
            ":digest": {"S": report_sha},
            ":template_digest": {"S": report["template_sha256"]},
            ":now": {"S": now},
            ":zero": {"N": "0"},
            ":one": {"N": "1"},
        },
    )
    emit("audit_report_persisted", job_id=event["job_id"], decision=report["decision"])
    return {
        "job_id": event["job_id"],
        "status": "COMPLETED",
        "decision": report["decision"],
        "report_prefix": prefix,
        "report_sha256": report_sha,
    }


def mark_failed(event: dict[str, Any], _context: Any) -> dict[str, Any]:
    failure = event.get("failure") or {}
    code = str(failure.get("Error") or "AuditStageFailed")[:120]
    now = datetime.now(UTC).isoformat()
    DDB.update_item(
        TableName=JOBS_TABLE,
        Key={"job_id": {"S": event["job_id"]}},
        UpdateExpression=(
            "SET #status=:failed, failure_code=:code, updated_at=:now, "
            "#version=if_not_exists(#version,:zero)+:one"
        ),
        ConditionExpression="attribute_exists(job_id) AND #status <> :completed",
        ExpressionAttributeNames={"#status": "status", "#version": "version"},
        ExpressionAttributeValues={
            ":failed": {"S": "FAILED"},
            ":completed": {"S": "COMPLETED"},
            ":code": {"S": code},
            ":now": {"S": now},
            ":zero": {"N": "0"},
            ":one": {"N": "1"},
        },
    )
    emit("audit_job_failed", job_id=event["job_id"], failure_code=code)
    return {"job_id": event["job_id"], "status": "FAILED", "failure_code": code}
