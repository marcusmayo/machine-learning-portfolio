# LocalStack vs real AWS: evidence matrix

An emulator is useful for fast contract checks, but green emulator tests are not equivalent to AWS evidence. This project records unsupported or materially different behaviors as `NOT_RUN/UNVERIFIED`.

| Behavior | Unit/static | LocalStack | Real AWS canary | Audit disposition |
|---|---:|---:|---:|---|
| Handler request/response shape | Strong | Strong | Spot-check | Unit/local evidence accepted |
| SAM/CloudFormation syntax | Strong | Partial | Strong | Require `sam validate --lint` and AWS change set for deployment evidence |
| IAM allow/deny evaluation | Policy shape only | Not authoritative; enforcement is off by default and licensed when enabled | Authoritative | Never mark PASS from community LocalStack |
| API Gateway AWS_IAM authorization | Static config | Partial | Authoritative | Negative canary must receive 403 when unsigned |
| DynamoDB Streams ordering/batching | Logic only | Approximation | Authoritative | Verify per-shard behavior and event-source metrics in AWS |
| Lambda retry timing and destinations | Logic/config | Approximation | Authoritative | Verify retry count, age limit, and destination artifact in AWS |
| SQS visibility and redrive timing | Arithmetic/config | Useful approximation | Authoritative | AWS canary measures duplicate window and DLQ arrival |
| EventBridge target retries / DLQ | Config | Approximation | Authoritative | Inject a failing target in the canary |
| Step Functions service integration errors | ASL validation | Partial | Authoritative | Verify named error matching and compensation path in AWS |
| CloudWatch alarms / X-Ray traces | Static only | Incomplete | Authoritative | Require alarm state and trace IDs in AWS evidence |

## Why IAM stays unverified locally

LocalStack's community path does not provide an authoritative AWS IAM policy engine. A local request succeeding therefore proves only that the emulator accepted the request. It does **not** prove the deployed role can perform the action, nor that a forbidden action is denied. The manual canary must test both a permitted action and an expected denial using the deployed function role.

## Canary evidence contract

A real-AWS run should emit a redacted manifest containing stack ID, template SHA-256, region, start/end timestamps, test IDs, CloudWatch log references, and a result for each parity row. Credentials, account numbers, customer payloads, presigned URLs, and raw tokens must not be committed.

## Primary references

- [AWS SAM: local invoke limitations](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/using-sam-cli-local-invoke.html)
- [AWS Lambda testing guide](https://docs.aws.amazon.com/lambda/latest/dg/testing-guide.html)
- [LocalStack IAM policy enforcement](https://docs.localstack.cloud/aws/developer-tools/security-testing/iam-policy-enforcement/)
