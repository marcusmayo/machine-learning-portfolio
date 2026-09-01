from __future__ import annotations

import argparse
import json
import urllib.error
import urllib.request
from datetime import UTC, datetime
from typing import Any

import boto3


def _outputs(cloudformation: Any, stack_name: str) -> dict[str, str]:
    stack = cloudformation.describe_stacks(StackName=stack_name)["Stacks"][0]
    return {item["OutputKey"]: item["OutputValue"] for item in stack.get("Outputs", [])}


def main() -> int:
    parser = argparse.ArgumentParser(description="Run non-destructive real-AWS parity checks")
    parser.add_argument("--stack-name", required=True)
    parser.add_argument("--region", required=True)
    args = parser.parse_args()

    session = boto3.Session(region_name=args.region)
    cf = session.client("cloudformation")
    ddb = session.client("dynamodb")
    sfn = session.client("stepfunctions")
    cloudwatch = session.client("cloudwatch")
    outputs = _outputs(cf, args.stack_name)
    checks: list[dict[str, Any]] = []

    table = ddb.describe_table(TableName=outputs["AuditJobsTableName"])["Table"]
    checks.append(
        {
            "id": "ddb-stream-enabled",
            "result": "PASS" if table.get("LatestStreamArn") else "FAIL",
        }
    )

    state_machine = sfn.describe_state_machine(stateMachineArn=outputs["AuditStateMachineArn"])
    checks.append(
        {
            "id": "sfn-standard",
            "result": "PASS" if state_machine["type"] == "STANDARD" else "FAIL",
        }
    )

    alarms = cloudwatch.describe_alarms(AlarmNamePrefix=args.stack_name)["MetricAlarms"]
    checks.append({"id": "alarms-created", "result": "PASS" if len(alarms) >= 3 else "FAIL"})

    request = urllib.request.Request(  # noqa: S310 - CloudFormation HTTPS output
        outputs["AuditJobsUrl"], method="POST", data=b"{}"
    )
    request.add_header("content-type", "application/json")
    request.add_header("idempotency-key", "unsigned-canary-request")
    try:
        urllib.request.urlopen(request, timeout=10)  # noqa: S310 - CloudFormation HTTPS output
        unsigned_result = "FAIL"
    except urllib.error.HTTPError as exc:
        unsigned_result = "PASS" if exc.code in {401, 403} else "FAIL"
    checks.append({"id": "unsigned-api-denied", "result": unsigned_result})

    manifest = {
        "schema_version": "1.0.0",
        "lane": "real-aws",
        "stack_name": args.stack_name,
        "region": args.region,
        "timestamp": datetime.now(UTC).isoformat(),
        "checks": checks,
        "localstack_iam": "UNVERIFIED",
    }
    print(json.dumps(manifest, indent=2, sort_keys=True))
    return 1 if any(item["result"] != "PASS" for item in checks) else 0


if __name__ == "__main__":
    raise SystemExit(main())
