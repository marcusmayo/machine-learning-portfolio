# Audit report: `task_cases/T02_retry_semantics/template.yaml`

- Decision: **FAIL**
- Score: **41/100**
- Template SHA-256: `c635a5c0ec69733ba0e8f09b7340f4af9c479b5a702be5d897bd5ed4984280c3`
- Findings: **5**
- Evidence: static VERIFIED; LocalStack IAM UNVERIFIED; real AWS NOT_RUN

## HIGH · SQS001 · SQS consumer replays the entire failed batch

**Path:** `Resources.WholeBatchConsumer.Properties.Events.Queue.Properties`

**Evidence:** FunctionResponseTypes omits ReportBatchItemFailures.

**AWS behavior:** Without partial-batch reporting, one failed record returns every message in the batch to the queue.

**Impact:** Already-completed side effects can repeat and poison messages can block healthy work.

**Remediation:** Enable ReportBatchItemFailures and return only failed messageId values; keep side effects idempotent.

**Verification:** Inject one poison and one healthy message and confirm only the poison message is retried.

## HIGH · SQS002 · Consumed SQS queue has no redrive policy

**Path:** `Resources.WorkQueue.Properties`

**Evidence:** RedrivePolicy is absent on a Lambda event-source queue.

**AWS behavior:** A poison message can be retried until retention expiry and repeatedly consume concurrency.

**Impact:** Bad input can stall or inflate the cost of healthy processing without a quarantine path.

**Remediation:** Attach a DLQ with a bounded maxReceiveCount and define a reviewed replay procedure.

**Verification:** In AWS, inject a poison message and verify bounded receipt count, DLQ arrival, and alarm state.

## HIGH · SQS003 · SQS visibility timeout is shorter than the Lambda retry window

**Path:** `Resources.WorkQueue.Properties.VisibilityTimeout`

**Evidence:** VisibilityTimeout=30; required baseline is at least 120 seconds for this consumer.

**AWS behavior:** AWS recommends at least six times the function timeout plus the batch window for Lambda SQS sources.

**Impact:** A message can become visible during processing, producing concurrent duplicates.

**Remediation:** Increase visibility timeout or reduce the function timeout, then retain idempotent effects.

**Verification:** Measure processing duration and duplicate receipt behavior with a slow-message AWS canary.

## MEDIUM · COST001 · Lambda concurrency is unbounded at the function level

**Path:** `Resources.WholeBatchConsumer.Properties`

**Evidence:** ReservedConcurrentExecutions is absent.

**AWS behavior:** Lambda may scale until account or downstream limits are reached.

**Impact:** A traffic spike can amplify DynamoDB, S3, Step Functions, and logging cost or throttle sibling workloads.

**Remediation:** Set and load-test a workload-specific concurrency cap; monitor throttles and age-of-oldest-message.

**Verification:** Run a bounded load test in AWS and inspect concurrency, throttles, backlog age, and downstream capacity.

## MEDIUM · OBS001 · Lambda tracing is disabled

**Path:** `Resources.WholeBatchConsumer.Properties.Tracing`

**Evidence:** Tracing is not Active in Globals or the function.

**AWS behavior:** Cross-service request correlation requires runtime trace evidence in AWS.

**Impact:** Diagnosing retries, duplication, and latency becomes slower.

**Remediation:** Enable active tracing and log only identifiers and low-cardinality fields, never templates or upload URLs.

**Verification:** Run the AWS canary and confirm traces connect API, Lambda, and downstream SDK calls.
