from __future__ import annotations

import json

from botocore.exceptions import ClientError

from src.create_audit_job import app


class FakeS3:
    def generate_presigned_post(self, **kwargs):
        assert kwargs["Key"].startswith("submissions/")
        assert ["content-length-range", 1, app.MAX_TEMPLATE_BYTES] in kwargs["Conditions"]
        return {"url": "https://upload.invalid", "fields": {"key": kwargs["Key"]}}


class FakeDDB:
    def __init__(self, conflict: bool = False, existing_hash: str = ""):
        self.conflict = conflict
        self.existing_hash = existing_hash

    def put_item(self, **_kwargs):
        if self.conflict:
            raise ClientError(
                {"Error": {"Code": "ConditionalCheckFailedException", "Message": "exists"}},
                "PutItem",
            )
        return {}

    def get_item(self, **_kwargs):
        return {"Item": {"request_hash": {"S": self.existing_hash}}}


def _event(key: str = "idempotency-key-123", name: str = "Candidate task") -> dict:
    return {
        "headers": {"Idempotency-Key": key},
        "body": json.dumps({"name": name, "template_format": "sam"}),
    }


def test_create_job_uses_conditional_record_and_bounded_presign(monkeypatch) -> None:
    monkeypatch.setattr(app, "DDB", FakeDDB())
    monkeypatch.setattr(app, "S3", FakeS3())
    response = app.handler(_event(), None)
    body = json.loads(response["body"])
    assert response["statusCode"] == 201
    assert body["status"] == "PENDING_UPLOAD"
    assert body["upload"]["expires_in_seconds"] == 900
    assert body["upload"]["max_bytes"] == app.MAX_TEMPLATE_BYTES


def test_idempotency_key_reuse_with_different_payload_is_conflict(monkeypatch) -> None:
    monkeypatch.setattr(app, "DDB", FakeDDB(conflict=True, existing_hash="different"))
    monkeypatch.setattr(app, "S3", FakeS3())
    response = app.handler(_event(), None)
    assert response["statusCode"] == 409


def test_invalid_request_is_rejected_without_aws_calls(monkeypatch) -> None:
    monkeypatch.setattr(app, "DDB", FakeDDB())
    response = app.handler({"headers": {}, "body": "{}"}, None)
    assert response["statusCode"] == 400
    response = app.handler(
        {"headers": {"idempotency-key": "long-enough"}, "body": '{"unknown": true}'},
        None,
    )
    assert response["statusCode"] == 400
