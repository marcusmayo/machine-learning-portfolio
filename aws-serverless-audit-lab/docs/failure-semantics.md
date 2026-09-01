# Failure semantics

## Delivery contract

Every asynchronous hop is treated as **at least once**. The system does not claim exactly-once delivery.

- API retries reuse an idempotency key. The key determines a stable audit-job ID, and a request hash rejects reuse with different content.
- S3 upload notifications identify immutable work by bucket, key, and version. The consumer uses a deterministic workflow execution name so duplicate notifications do not duplicate the audit.
- DynamoDB Streams returns `batchItemFailures` so successful status records are not replayed with a poison record. Retries are bounded by count and record age, and batches can be bisected.
- The stream on-failure SQS queue is a quarantine. For stream sources, SQS/SNS destinations contain invocation metadata rather than the complete failed source record; recovery may require reading the stream before expiry or using an S3 on-failure destination in an AWS-validated variant.
- EventBridge producers inspect `FailedEntryCount`; HTTP 200 alone is not success for every entry. Targets have a retry policy and DLQ.
- The SQS consumer uses partial-batch responses. Queue visibility is six times the Lambda timeout, and redrive is bounded.
- Step Functions uses a Standard workflow, typed transient retries, catches, and a compensating inventory release path.
- Report objects use deterministic keys and content hashes; workflow execution names are deterministic.

## Replay procedure

1. Inspect and classify the quarantined message.
2. Correct the underlying defect and record the code/template SHA.
3. Reconstruct or retrieve the original source payload when the destination stored metadata only.
4. Replay to a dedicated validation queue first.
5. Confirm the idempotency record and downstream side effects.
6. Move the approved message to the primary queue and retain the evidence manifest.

There is intentionally no automatic DLQ-to-source loop.

## Primary references

- [AWS Lambda: configure an SQS event source](https://docs.aws.amazon.com/lambda/latest/dg/services-sqs-configure.html)
- [AWS Lambda: DynamoDB partial-batch reporting](https://docs.aws.amazon.com/lambda/latest/dg/services-ddb-batchfailurereporting.html)
- [AWS Well-Architected Serverless Lens: failure management](https://docs.aws.amazon.com/wellarchitected/latest/serverless-applications-lens/failure-management.html)
