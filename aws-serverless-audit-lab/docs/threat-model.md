# Threat model

| Threat | Control | Residual evidence needed |
|---|---|---|
| Submitted template executes code | Safe YAML loader; no imports, subprocesses, macros, CloudFormation deployment, or dynamic plugins | Mutation tests for Python tags and path traversal |
| Oversized payload / parser exhaustion | Presigned POST size condition; S3 metadata check; bounded read; 100-finding report cap | AWS upload-boundary canary and parser resource metrics |
| Cross-job object overwrite | Deterministic key, S3 versioning, immutable version passed into workflow | Duplicate and overwrite canary |
| Duplicate asynchronous delivery | Deterministic Step Functions name, conditional DDB updates, conditional S3 report writes | Duplicate S3 notification and SQS redelivery canary |
| Poison record stalls healthy work | Partial-batch reporting, bisection, bounded retry/age, DLQs and alarms | Real-AWS shard/queue injection |
| Privilege escalation | Per-function policies, exact resource policies, optional permission boundary | IAM Access Analyzer plus expected-deny AWS canary |
| Sensitive data in logs/evidence | Metadata-only structured logs; no template, URL, auth header, account ID, or raw cause in committed report | Log scan in protected canary |
| False confidence from emulator | Evidence matrix marks unsupported behavior `UNVERIFIED` | Protected disposable AWS parity lane |
