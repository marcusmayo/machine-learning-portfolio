# Cost model

This is a low-idle-cost sandbox pattern, not a zero-cost promise.

- DynamoDB uses `PAY_PER_REQUEST` and point-in-time recovery.
- Lambda concurrency is bounded per function; reserved concurrency can also reserve account capacity, so values should be tuned before shared-account deployment.
- Step Functions is Standard because execution history and durable retry semantics matter more than the lowest per-transition price for this audit lab.
- CloudWatch log groups retain data for 14 days.
- Submission and report objects transition to cheaper storage and expire after 90 days; quarantine evidence must be exported before expiration when policy requires longer retention.
- EventBridge, SQS, SNS, API Gateway, and Lambda remain request-priced. Alarms, traces, NAT gateways, KMS customer-managed keys, and high-volume logs can dominate a small demo's bill.

The manual AWS workflow must deploy into an isolated tagged stack and execute teardown even after test failure.
