from __future__ import annotations

import io

from src.workflow_tasks import app

GOOD_TEMPLATE = b"""AWSTemplateFormatVersion: '2010-09-09'\nResources:\n  Bucket:\n    Type: AWS::S3::Bucket\n"""


class FakeS3:
    def __init__(self):
        self.objects = {}

    def head_object(self, Bucket, Key, **_kwargs):
        if Bucket == "submission-bucket":
            return {"ContentLength": len(GOOD_TEMPLATE), "ContentType": "application/x-yaml"}
        body, _content_type, digest = self.objects[(Bucket, Key)]
        return {"Metadata": {"sha256": digest}, "ContentLength": len(body)}

    def get_object(self, **_kwargs):
        return {"Body": io.BytesIO(GOOD_TEMPLATE)}

    def put_object(self, Bucket, Key, Body, ContentType, Metadata, **_kwargs):
        self.objects[(Bucket, Key)] = (Body, ContentType, Metadata["sha256"])
        return {}


class FakeDDB:
    def __init__(self):
        self.calls = []

    def update_item(self, **kwargs):
        self.calls.append(kwargs)
        return {}


def _event():
    return {
        "job_id": "abc123abc123abc123abc123",
        "bucket": "submission-bucket",
        "key": "submissions/abc123abc123abc123abc123/template.yaml",
        "version_id": "v1",
    }


def test_workflow_validates_audits_and_persists_three_formats(monkeypatch) -> None:
    fake_s3 = FakeS3()
    fake_ddb = FakeDDB()
    monkeypatch.setattr(app, "S3", fake_s3)
    monkeypatch.setattr(app, "DDB", fake_ddb)
    monkeypatch.setattr(app, "SUBMISSION_BUCKET", "submission-bucket")
    monkeypatch.setattr(app, "REPORT_BUCKET", "report-bucket")
    monkeypatch.setattr(app, "JOBS_TABLE", "jobs")
    validated = app.validate_submission(_event(), None)
    audited = app.run_audit(validated, None)
    result = app.persist_report(audited, None)
    assert result["status"] == "COMPLETED"
    assert {key.rsplit(".", 1)[-1] for _, key in fake_s3.objects} == {"json", "md", "sarif"}
    assert fake_ddb.calls[0]["ConditionExpression"].startswith("attribute_exists")


def test_mark_failed_stores_bounded_error_code(monkeypatch) -> None:
    fake_ddb = FakeDDB()
    monkeypatch.setattr(app, "DDB", fake_ddb)
    monkeypatch.setattr(app, "JOBS_TABLE", "jobs")
    result = app.mark_failed(
        {"job_id": "job-1", "failure": {"Error": "ValidationError", "Cause": "do not store me"}},
        None,
    )
    assert result["status"] == "FAILED"
    values = fake_ddb.calls[0]["ExpressionAttributeValues"]
    assert values[":code"] == {"S": "ValidationError"}
