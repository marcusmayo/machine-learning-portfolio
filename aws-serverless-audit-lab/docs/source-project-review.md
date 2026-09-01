# Source-project review and enhancement record

This lab was derived from patterns already present in the portfolio and was rewritten rather than copied verbatim.

## Digital Value Chain

Useful evidence retained: AWS SAM, Lambda/API Gateway integration, two DynamoDB tables, pay-per-request billing, table-scoped SAM policy templates, environment configuration, and stack outputs.

Defects corrected here:

- removed the `sk_test_xxx` secret default and external payment dependency;
- added API authorization and a parameterized CORS origin;
- split one broad router into single-purpose functions and narrower policies;
- added input validation, idempotency, conditional writes, and conflict behavior;
- added Streams, EventBridge, SQS/DLQ, Step Functions, S3, SNS, alarms, tracing, and bounded concurrency;
- aligned documentation with actual handlers and runtime;
- distinguished screenshots/deployment history in the source project from validation of this new project.

## Edenred Invoice Assistant

Useful evidence retained: Lambda/API Gateway/S3/CloudWatch/SageMaker experience, request/report flow, latency awareness, and serverless cost motivation.

Enhancement here: the submission/report path is expressed as reproducible SAM/CloudFormation with deterministic object creation, asynchronous failure controls, and audit tests. The prior SageMaker endpoint is not included because the public handler does not invoke it and it does not add evidence for this role's serverless-IaC rubric.

## Keel, Aegis, and Fleet

Useful evidence retained: deterministic verification, explicit decision gates, provenance, adversarial failure review, and bounded claims.

Enhancement here: those governance concepts are implemented as a versioned audit rubric, stable finding schema, flawed-task regression corpus, and LocalStack/AWS evidence boundary. The audit report is fail-closed and content-addressed; this project does not copy Keel's append-only ledger implementation or inherit its concurrent-writer/torn-tail risks.
