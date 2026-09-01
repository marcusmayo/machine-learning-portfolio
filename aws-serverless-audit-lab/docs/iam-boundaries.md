# IAM boundaries

| Principal | Allowed actions | Resource boundary |
|---|---|---|
| Create-job Lambda | `dynamodb:PutItem`, `GetItem`; `s3:PutObject` for presigning | One jobs table; `submissions/*` in one bucket |
| Audit starter Lambda | `states:StartExecution` | One state machine |
| Validation/audit Lambdas | `s3:GetObject`, `GetObjectVersion` | `submissions/*` in one bucket |
| Persist-report Lambda | `s3:PutObject`; `dynamodb:UpdateItem` | `reports/*` in one bucket; one jobs table |
| Failure Lambda | `dynamodb:UpdateItem` | One jobs table |
| Status publisher Lambda | `events:PutEvents`; failure `sqs:SendMessage` | One custom bus; one quarantine queue |
| Step Functions role | `lambda:InvokeFunction`; CloudWatch log-delivery APIs | Exact task functions; log-delivery APIs require `Resource: *` because they do not support resource-level permissions |

Every Lambda accepts an optional pre-existing permissions-boundary ARN. EventBridge-to-SQS, EventBridge-to-SNS, and SNS-to-SQS resource policies constrain the service principal with both `aws:SourceArn` and `aws:SourceAccount`.

Static policy shape is necessary but insufficient. The protected real-AWS workflow must prove both an allowed action and an expected denial. LocalStack IAM remains `UNVERIFIED` unless its licensed policy engine is enabled, and even then it is not the deployment authority.
