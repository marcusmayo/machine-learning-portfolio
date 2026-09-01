# Audit methodology

## Rubric

| Dimension | Weight | Blocking examples |
|---|---:|---|
| Service integration correctness | 25 | Wrong ARN, incompatible payload, missing queue policy, ignored EventBridge failed entries |
| Failure handling and idempotency | 25 | Infinite poison retry, whole-batch replay after side effects, missing DLQ, false exactly-once claim |
| IAM and secret boundaries | 20 | `Action: "*"`, `Resource: "*"` without a documented service requirement, plaintext credential |
| IaC and environment fidelity | 15 | Invalid SAM, emulator-only assertion presented as AWS proof, unpinned infrastructure dependency |
| Observability and cost controls | 10 | No alarm on quarantine depth, unbounded concurrency, infinite retention |
| Evidence and written feedback | 5 | Conclusion without a path/resource, AWS behavior, reproduction, remediation, and verification |

## Finding contract

Each finding includes:

- stable rule ID and severity;
- exact file path and CloudFormation/ASL resource path;
- the actual AWS behavior involved;
- operational or security impact;
- a deterministic reproduction or inspection step;
- a concrete remediation;
- a verification step that states whether LocalStack is sufficient.

The CLI deliberately favors high-signal structural checks over pretending to simulate AWS. Static checks can reject known-dangerous shapes. They cannot certify runtime IAM or retry behavior.
