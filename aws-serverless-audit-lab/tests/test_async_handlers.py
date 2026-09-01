from __future__ import annotations

import json

from botocore.exceptions import ClientError

from src.audit_starter import app as starter
from src.status_publisher import app as publisher


class FakeSfn:
    def __init__(self, duplicate: bool = False):
        self.calls = []
        self.duplicate = duplicate

    def start_execution(self, **kwargs):
        self.calls.append(kwargs)
        if self.duplicate:
            raise ClientError(
                {"Error": {"Code": "ExecutionAlreadyExists", "Message": "duplicate"}},
                "StartExecution",
            )
        return {"executionArn": "arn:execution"}


def _sqs_record(message_id: str = "m1", key: str = "submissions/abc123abc123abc123abc123/template.yaml"):
    event = {
        "detail": {
            "bucket": {"name": "submission-bucket"},
            "object": {"key": key, "version-id": "v1"},
        }
    }
    return {"messageId": message_id, "body": json.dumps(event)}


def test_sqs_starter_is_deterministic_and_partial_batch(monkeypatch) -> None:
    fake = FakeSfn()
    monkeypatch.setattr(starter, "SFN", fake)
    monkeypatch.setattr(starter, "STATE_MACHINE_ARN", "arn:state-machine")
    monkeypatch.setattr(starter, "SUBMISSION_BUCKET", "submission-bucket")
    result = starter.handler({"Records": [_sqs_record(), _sqs_record("bad", "elsewhere.yaml")]}, None)
    assert result == {"batchItemFailures": [{"itemIdentifier": "bad"}]}
    assert fake.calls[0]["name"].startswith("audit-abc123abc123abc123abc123-")


def test_duplicate_execution_is_success(monkeypatch) -> None:
    monkeypatch.setattr(starter, "SFN", FakeSfn(duplicate=True))
    monkeypatch.setattr(starter, "STATE_MACHINE_ARN", "arn:state-machine")
    monkeypatch.setattr(starter, "SUBMISSION_BUCKET", "submission-bucket")
    assert starter.handler({"Records": [_sqs_record()]}, None) == {"batchItemFailures": []}


class FakeEvents:
    def __init__(self, fail: bool = False):
        self.fail = fail
        self.entries = []

    def put_events(self, Entries):
        self.entries.extend(Entries)
        return {"FailedEntryCount": 1 if self.fail else 0}


def _ddb_record(sequence: str = "42", old_status: str = "PENDING_UPLOAD", new_status: str = "COMPLETED"):
    return {
        "dynamodb": {
            "SequenceNumber": sequence,
            "OldImage": {"job_id": {"S": "job-1"}, "status": {"S": old_status}},
            "NewImage": {
                "job_id": {"S": "job-1"},
                "status": {"S": new_status},
                "updated_at": {"S": "2026-01-01T00:00:00+00:00"},
            },
        }
    }


def test_stream_publisher_uses_sequence_number_for_partial_failure(monkeypatch) -> None:
    fake = FakeEvents(fail=True)
    monkeypatch.setattr(publisher, "EVENTS", fake)
    monkeypatch.setattr(publisher, "STATUS_BUS_NAME", "status-bus")
    result = publisher.handler({"Records": [_ddb_record("sequence-9")]}, None)
    assert result == {"batchItemFailures": [{"itemIdentifier": "sequence-9"}]}


def test_unchanged_status_is_not_published(monkeypatch) -> None:
    fake = FakeEvents()
    monkeypatch.setattr(publisher, "EVENTS", fake)
    result = publisher.handler({"Records": [_ddb_record(old_status="COMPLETED")]}, None)
    assert result == {"batchItemFailures": []}
    assert fake.entries == []
