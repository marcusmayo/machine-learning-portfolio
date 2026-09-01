# Architecture and invariants

## Data flow

1. An AWS_IAM-authorized caller posts only job metadata and an `Idempotency-Key` to `/audit-jobs`.
2. The create Lambda conditionally writes a DynamoDB job record and returns a 15-minute presigned S3 POST restricted by exact key, content type, and size range.
3. S3 sends `Object Created` to EventBridge. An exact bucket/prefix rule sends the event to an encrypted SQS queue with target retry policy and a DLQ.
4. The SQS Lambda validates the event contract and starts a deterministic Standard Step Functions execution. Duplicate notifications resolve to `ExecutionAlreadyExists` and are acknowledged.
5. Step Functions validates the immutable S3 version, parses the template as data, applies deterministic rules, and persists JSON, Markdown, and SARIF artifacts under a content-addressed report prefix.
6. A conditional DynamoDB status update emits a stream record. The stream Lambda inspects `FailedEntryCount` from EventBridge and publishes a versioned status event to a custom bus.
7. EventBridge publishes status changes to an encrypted SNS topic; an SQS subscriber demonstrates a durable notification consumer boundary.

## Invariants

- Submitted code is never imported, executed, shelled out, or passed to CloudFormation.
- A job is identified by `job_id`; an input artifact is identified by bucket, key, version, and SHA-256—not by notification ID.
- The same idempotency key plus the same metadata reuses a job; the same key plus different metadata returns `409`.
- All asynchronous delivery is treated as at least once.
- `batchItemFailures` contains SQS `messageId` values or DynamoDB Streams `SequenceNumber` values, as appropriate.
- Permanent template findings are results, not exceptions. Only transient service failures are retried.
- Reports are deterministic, capped at 100 detailed findings for the Step Functions payload boundary, and content-addressed in S3.
- Templates, authorization headers, presigned fields, and raw failure causes are not logged.
