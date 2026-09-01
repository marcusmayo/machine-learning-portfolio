from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any

import yaml

from .cfn import load_template
from .models import SEVERITY_RANK, Finding, sort_findings

SECRET_NAME = re.compile(r"(?:secret|password|passwd|token|api.?key|private.?key)", re.I)
ALLOWED_STAR_ACTIONS = {
    "logs:CreateLogDelivery",
    "logs:GetLogDelivery",
    "logs:UpdateLogDelivery",
    "logs:DeleteLogDelivery",
    "logs:ListLogDeliveries",
    "logs:PutResourcePolicy",
    "logs:DescribeResourcePolicies",
    "logs:DescribeLogGroups",
}
TRANSIENT_LAMBDA_ERRORS = {
    "Lambda.ServiceException",
    "Lambda.AWSLambdaException",
    "Lambda.SdkClientException",
    "Lambda.TooManyRequestsException",
}


def _items(value: Any) -> list[Any]:
    return value if isinstance(value, list) else [value]


def _finding(
    rule_id: str,
    severity: str,
    title: str,
    path: str,
    evidence: str,
    aws_behavior: str,
    impact: str,
    remediation: str,
    verification: str,
) -> Finding:
    return Finding(
        rule_id,
        severity,
        title,
        path,
        evidence,
        aws_behavior,
        impact,
        remediation,
        verification,
    )


def _policy_statements(properties: dict[str, Any]) -> list[tuple[str, dict[str, Any]]]:
    statements: list[tuple[str, dict[str, Any]]] = []
    policies = properties.get("Policies", [])
    for policy_index, policy in enumerate(_items(policies)):
        if not isinstance(policy, dict):
            continue
        candidates: Any = policy.get("Statement")
        if candidates is None and isinstance(policy.get("PolicyDocument"), dict):
            candidates = policy["PolicyDocument"].get("Statement")
        for statement_index, statement in enumerate(_items(candidates or [])):
            if isinstance(statement, dict):
                statements.append((f"Policies[{policy_index}].Statement[{statement_index}]", statement))

    document = properties.get("PolicyDocument")
    if isinstance(document, dict):
        for statement_index, statement in enumerate(_items(document.get("Statement", []))):
            if isinstance(statement, dict):
                statements.append((f"PolicyDocument.Statement[{statement_index}]", statement))
    return statements


def _logical_id_from_getatt(value: Any) -> str | None:
    if not isinstance(value, dict):
        return None
    raw = value.get("Fn::GetAtt")
    if isinstance(raw, list) and raw:
        return str(raw[0])
    if isinstance(raw, str):
        return raw.split(".", 1)[0]
    return None


def _audit_iam(resources: dict[str, Any]) -> list[Finding]:
    findings: list[Finding] = []
    for logical_id, resource in resources.items():
        if not isinstance(resource, dict):
            continue
        props = resource.get("Properties") or {}
        if not isinstance(props, dict):
            continue
        for suffix, statement in _policy_statements(props):
            if statement.get("Effect", "Allow") != "Allow":
                continue
            actions = {str(action) for action in _items(statement.get("Action", []))}
            resource_values = _items(statement.get("Resource", []))
            path = f"Resources.{logical_id}.Properties.{suffix}"
            if "*" in actions:
                findings.append(
                    _finding(
                        "IAM001",
                        "CRITICAL",
                        "Wildcard IAM action",
                        path,
                        'Action contains "*".',
                        "An Allow statement with Action '*' grants every API action permitted by its resource and conditions.",
                        "A compromised function or task can perform unrelated control-plane and data-plane operations.",
                        "Replace the wildcard with the exact API actions exercised by the handler.",
                        "Deploy to an isolated AWS account and run positive and negative IAM canaries; LocalStack is not authoritative.",
                    )
                )
            unsupported_wildcard = any(value == "*" for value in resource_values) and not actions.issubset(
                ALLOWED_STAR_ACTIONS
            )
            if unsupported_wildcard:
                findings.append(
                    _finding(
                        "IAM002",
                        "HIGH",
                        "Unbounded IAM resource",
                        path,
                        'Resource contains "*" for an action that supports resource scoping.',
                        "Most data-plane AWS actions can be constrained to table, queue, state machine, topic, or object-prefix ARNs.",
                        "The principal can act on unrelated resources in the account.",
                        "Scope Resource to exact ARNs and use SourceArn/SourceAccount conditions on resource policies.",
                        "Use IAM Access Analyzer plus a real-AWS expected-deny canary; report local IAM as UNVERIFIED.",
                    )
                )
    return findings


def _audit_secrets(document: dict[str, Any], resources: dict[str, Any]) -> list[Finding]:
    findings: list[Finding] = []
    for name, parameter in (document.get("Parameters") or {}).items():
        if not isinstance(parameter, dict) or not SECRET_NAME.search(str(name)):
            continue
        default = parameter.get("Default")
        if default not in (None, ""):
            findings.append(
                _finding(
                    "SEC001",
                    "CRITICAL",
                    "Credential-like parameter has a default",
                    f"Parameters.{name}.Default",
                    "A secret-shaped parameter contains a committed default value.",
                    "CloudFormation parameters and templates are not secret stores; NoEcho also does not protect every downstream surface.",
                    "The credential can leak through source, stack metadata, environment variables, or logs.",
                    "Remove the default and resolve a Secrets Manager or SSM SecureString ARN at runtime.",
                    "Scan git history and CloudFormation events, rotate the credential, then deploy with a secret reference.",
                )
            )

    for logical_id, resource in resources.items():
        if not isinstance(resource, dict) or resource.get("Type") != "AWS::Serverless::Function":
            continue
        variables = ((resource.get("Properties") or {}).get("Environment") or {}).get("Variables", {})
        for name, value in variables.items():
            is_literal = isinstance(value, str) and not value.startswith("{{resolve:")
            if SECRET_NAME.search(str(name)) and is_literal and value:
                findings.append(
                    _finding(
                        "SEC002",
                        "HIGH",
                        "Plaintext secret in Lambda environment",
                        f"Resources.{logical_id}.Properties.Environment.Variables.{name}",
                        "A secret-shaped environment variable contains a literal value.",
                        "Lambda environment configuration is visible to principals with function configuration access.",
                        "Source exposure or overbroad read permissions can disclose the credential.",
                        "Store the value in Secrets Manager and grant only secretsmanager:GetSecretValue on its ARN.",
                        "Deploy to AWS, confirm the environment contains only a reference, and run a secret scanner over the repository.",
                    )
                )
    return findings


def _audit_sqs_and_functions(document: dict[str, Any], resources: dict[str, Any]) -> list[Finding]:
    findings: list[Finding] = []
    queues = {
        name: resource
        for name, resource in resources.items()
        if isinstance(resource, dict) and resource.get("Type") == "AWS::SQS::Queue"
    }
    global_function = ((document.get("Globals") or {}).get("Function") or {})
    for logical_id, resource in resources.items():
        if not isinstance(resource, dict) or resource.get("Type") != "AWS::Serverless::Function":
            continue
        props = resource.get("Properties") or {}
        timeout = int(props.get("Timeout", global_function.get("Timeout", 3)))
        if "ReservedConcurrentExecutions" not in props:
            findings.append(
                _finding(
                    "COST001",
                    "MEDIUM",
                    "Lambda concurrency is unbounded at the function level",
                    f"Resources.{logical_id}.Properties",
                    "ReservedConcurrentExecutions is absent.",
                    "Lambda may scale until account or downstream limits are reached.",
                    "A traffic spike can amplify DynamoDB, S3, Step Functions, and logging cost or throttle sibling workloads.",
                    "Set and load-test a workload-specific concurrency cap; monitor throttles and age-of-oldest-message.",
                    "Run a bounded load test in AWS and inspect concurrency, throttles, backlog age, and downstream capacity.",
                )
            )
        for event_name, event in (props.get("Events") or {}).items():
            if not isinstance(event, dict) or event.get("Type") != "SQS":
                continue
            event_props = event.get("Properties") or {}
            path = f"Resources.{logical_id}.Properties.Events.{event_name}.Properties"
            response_types = event_props.get("FunctionResponseTypes", [])
            if "ReportBatchItemFailures" not in response_types:
                findings.append(
                    _finding(
                        "SQS001",
                        "HIGH",
                        "SQS consumer replays the entire failed batch",
                        path,
                        "FunctionResponseTypes omits ReportBatchItemFailures.",
                        "Without partial-batch reporting, one failed record returns every message in the batch to the queue.",
                        "Already-completed side effects can repeat and poison messages can block healthy work.",
                        "Enable ReportBatchItemFailures and return only failed messageId values; keep side effects idempotent.",
                        "Inject one poison and one healthy message and confirm only the poison message is retried.",
                    )
                )
            queue_id = _logical_id_from_getatt(event_props.get("Queue"))
            queue_props = (queues.get(queue_id or "") or {}).get("Properties", {})
            if queue_id and not queue_props.get("RedrivePolicy"):
                findings.append(
                    _finding(
                        "SQS002",
                        "HIGH",
                        "Consumed SQS queue has no redrive policy",
                        f"Resources.{queue_id}.Properties",
                        "RedrivePolicy is absent on a Lambda event-source queue.",
                        "A poison message can be retried until retention expiry and repeatedly consume concurrency.",
                        "Bad input can stall or inflate the cost of healthy processing without a quarantine path.",
                        "Attach a DLQ with a bounded maxReceiveCount and define a reviewed replay procedure.",
                        "In AWS, inject a poison message and verify bounded receipt count, DLQ arrival, and alarm state.",
                    )
                )
            if queue_id:
                visibility = int(queue_props.get("VisibilityTimeout", 30))
                batch_window = int(event_props.get("MaximumBatchingWindowInSeconds", 0))
                required = (6 * timeout) + batch_window
                if visibility < required:
                    findings.append(
                        _finding(
                            "SQS003",
                            "HIGH",
                            "SQS visibility timeout is shorter than the Lambda retry window",
                            f"Resources.{queue_id}.Properties.VisibilityTimeout",
                            f"VisibilityTimeout={visibility}; required baseline is at least {required} seconds for this consumer.",
                            "AWS recommends at least six times the function timeout plus the batch window for Lambda SQS sources.",
                            "A message can become visible during processing, producing concurrent duplicates.",
                            "Increase visibility timeout or reduce the function timeout, then retain idempotent effects.",
                            "Measure processing duration and duplicate receipt behavior with a slow-message AWS canary.",
                        )
                    )
    return findings


def _audit_streams(resources: dict[str, Any]) -> list[Finding]:
    findings: list[Finding] = []
    required = {
        "BisectBatchOnFunctionError",
        "MaximumRetryAttempts",
        "MaximumRecordAgeInSeconds",
        "DestinationConfig",
    }
    for logical_id, resource in resources.items():
        if not isinstance(resource, dict) or resource.get("Type") != "AWS::Serverless::Function":
            continue
        for event_name, event in ((resource.get("Properties") or {}).get("Events") or {}).items():
            if not isinstance(event, dict) or event.get("Type") != "DynamoDB":
                continue
            props = event.get("Properties") or {}
            path = f"Resources.{logical_id}.Properties.Events.{event_name}.Properties"
            missing = sorted(required - props.keys())
            partial = "ReportBatchItemFailures" in props.get("FunctionResponseTypes", [])
            retry_count = props.get("MaximumRetryAttempts", -1)
            if missing or not partial or retry_count == -1:
                findings.append(
                    _finding(
                        "DDB001",
                        "HIGH",
                        "DynamoDB Streams poison-record handling is incomplete",
                        path,
                        f"Missing={missing}; partial_batch={partial}; MaximumRetryAttempts={retry_count!r}.",
                        "An unbounded failing record can block progress on its shard until the stream record expires.",
                        "Healthy later records are delayed and failure payload recovery becomes time-bounded.",
                        "Use partial-batch responses, bisection, bounded retry/record age, and an on-failure destination.",
                        "Inject a poison stream record in AWS and verify checkpoint progress, retry bounds, quarantine, and alarm state.",
                    )
                )
    return findings


def _load_asl(definition: Any, base_dir: Path) -> dict[str, Any] | None:
    if isinstance(definition, dict):
        return definition
    if isinstance(definition, str):
        candidate = (base_dir / definition).resolve()
        if not candidate.is_relative_to(base_dir.resolve()) or not candidate.exists():
            return None
        return json.loads(candidate.read_text(encoding="utf-8"))
    return None


def _audit_state_machines(resources: dict[str, Any], base_dir: Path) -> list[Finding]:
    findings: list[Finding] = []
    for logical_id, resource in resources.items():
        if not isinstance(resource, dict) or resource.get("Type") != "AWS::Serverless::StateMachine":
            continue
        props = resource.get("Properties") or {}
        path = f"Resources.{logical_id}.Properties"
        if props.get("Type", "STANDARD") != "STANDARD":
            findings.append(
                _finding(
                    "SFN001",
                    "HIGH",
                    "Audit workflow is not Standard",
                    f"{path}.Type",
                    f"Type={props.get('Type')!r}.",
                    "Express workflows have different execution, history, and delivery semantics from Standard workflows.",
                    "The evaluator can lose durable per-execution evidence or reason from the wrong retry model.",
                    "Use STANDARD for this evidence-oriented workflow and document upstream at-least-once delivery.",
                    "Run failure and duplicate-notification canaries against the deployed Standard workflow.",
                )
            )
        definition = props.get("Definition") or props.get("DefinitionUri")
        try:
            asl = _load_asl(definition, base_dir)
        except (OSError, json.JSONDecodeError):
            asl = None
        if asl is None:
            findings.append(
                _finding(
                    "SFN002",
                    "MEDIUM",
                    "State-machine definition could not be inspected",
                    path,
                    "Definition/DefinitionUri did not resolve to inspectable ASL.",
                    "Template-only review cannot verify task timeouts, retries, or catches without the ASL artifact.",
                    "Failure-path conclusions remain unsupported.",
                    "Include the ASL file in the task bundle and keep DefinitionUri repository-relative.",
                    "Validate the resolved ASL and run one transient-error and one permanent-error execution in AWS.",
                )
            )
            continue
        for state_name, state in (asl.get("States") or {}).items():
            if not isinstance(state, dict) or state.get("Type") != "Task":
                continue
            state_path = f"{path}.Definition.States.{state_name}"
            retries = state.get("Retry", [])
            catches = state.get("Catch", [])
            retry_errors = {
                error
                for retry in retries
                if isinstance(retry, dict)
                for error in retry.get("ErrorEquals", [])
            }
            if "States.ALL" in retry_errors or not retry_errors:
                findings.append(
                    _finding(
                        "SFN003",
                        "HIGH",
                        "Step Functions task has unsafe retry coverage",
                        f"{state_path}.Retry",
                        f"Retry errors={sorted(retry_errors)}.",
                        "Permanent validation/policy failures should not be retried; transient service errors should be bounded.",
                        "A malformed task can waste transitions or repeat side effects.",
                        f"Retry only transient errors such as {sorted(TRANSIENT_LAMBDA_ERRORS)} with bounded backoff.",
                        "Inject a throttling error and a malformed template; only the transient error should retry.",
                    )
                )
            if not catches:
                findings.append(
                    _finding(
                        "SFN004",
                        "HIGH",
                        "Step Functions task has no catch path",
                        f"{state_path}.Catch",
                        "Catch is absent.",
                        "An unhandled terminal error fails the execution without updating the audit-job record.",
                        "Callers can see a job stuck in a nonterminal state and operators lose bounded failure context.",
                        "Catch terminal errors, persist a bounded failure code, then fail the execution explicitly.",
                        "Inject a permanent task failure and verify DynamoDB status, execution state, and redacted logs.",
                    )
                )
    return findings


def _audit_auth_and_observability(document: dict[str, Any], resources: dict[str, Any]) -> list[Finding]:
    findings: list[Finding] = []
    global_function = ((document.get("Globals") or {}).get("Function") or {})
    tracing_global = global_function.get("Tracing") == "Active"
    for logical_id, resource in resources.items():
        if not isinstance(resource, dict):
            continue
        props = resource.get("Properties") or {}
        if resource.get("Type") == "AWS::Serverless::HttpApi":
            auth = props.get("Auth") or {}
            default_authorizer = auth.get("DefaultAuthorizer")
            iam_authorizer_enabled = auth.get("EnableIamAuthorizer") is True
            if not default_authorizer and not iam_authorizer_enabled:
                findings.append(
                    _finding(
                        "API001",
                        "HIGH",
                        "HTTP API has no default authorizer",
                        f"Resources.{logical_id}.Properties.Auth",
                        "DefaultAuthorizer is absent.",
                        "API Gateway HTTP APIs do not become authenticated merely because a Lambda role is least-privileged.",
                        "Unauthenticated users can create audit work and presigned uploads, increasing data and cost risk.",
                        "Configure AWS_IAM or an appropriate JWT/Lambda authorizer and use a specific CORS origin.",
                        "In AWS, verify an unsigned request is denied and an authorized request is accepted.",
                    )
                )
        if resource.get("Type") == "AWS::Serverless::Function":
            if not tracing_global and props.get("Tracing") != "Active":
                findings.append(
                    _finding(
                        "OBS001",
                        "MEDIUM",
                        "Lambda tracing is disabled",
                        f"Resources.{logical_id}.Properties.Tracing",
                        "Tracing is not Active in Globals or the function.",
                        "Cross-service request correlation requires runtime trace evidence in AWS.",
                        "Diagnosing retries, duplication, and latency becomes slower.",
                        "Enable active tracing and log only identifiers and low-cardinality fields, never templates or upload URLs.",
                        "Run the AWS canary and confirm traces connect API, Lambda, and downstream SDK calls.",
                    )
                )
    return findings


def audit_text(text: str, source: str = "template.yaml", base_dir: Path | None = None) -> dict[str, Any]:
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
    try:
        document = load_template(text)
    except (yaml.YAMLError, ValueError) as exc:
        finding = _finding(
            "CFN001",
            "CRITICAL",
            "Template is not valid YAML/JSON mapping data",
            source,
            type(exc).__name__,
            "CloudFormation requires a parseable object document before transform or resource validation.",
            "The task cannot be reviewed or deployed deterministically.",
            "Correct the syntax and keep intrinsic functions as CloudFormation data tags.",
            "Run this auditor, cfn-lint, and sam validate --lint; do not execute submitted code.",
        )
        return _report(source, digest, [finding])

    resources = document.get("Resources") or {}
    if not isinstance(resources, dict):
        resources = {}
    resolved_base = base_dir or Path.cwd()
    findings = []
    findings.extend(_audit_iam(resources))
    findings.extend(_audit_secrets(document, resources))
    findings.extend(_audit_sqs_and_functions(document, resources))
    findings.extend(_audit_streams(resources))
    findings.extend(_audit_state_machines(resources, resolved_base))
    findings.extend(_audit_auth_and_observability(document, resources))
    return _report(source, digest, findings)


def _report(source: str, digest: str, findings: list[Finding]) -> dict[str, Any]:
    ordered = sort_findings(findings)
    total_findings = len(ordered)
    ordered = ordered[:100]
    penalty = {"CRITICAL": 25, "HIGH": 15, "MEDIUM": 7, "LOW": 2, "INFO": 0}
    score = max(0, 100 - sum(penalty[item.severity] for item in ordered))
    blocking = any(SEVERITY_RANK[item.severity] >= SEVERITY_RANK["HIGH"] for item in ordered)
    return {
        "schema_version": "1.0.0",
        "engine": "aws-serverless-audit-lab",
        "source": source,
        "template_sha256": digest,
        "score": score,
        "decision": "FAIL" if blocking else "PASS_WITH_NOTES" if ordered else "PASS",
        "evidence_boundary": {
            "static": "VERIFIED",
            "localstack_iam": "UNVERIFIED",
            "real_aws": "NOT_RUN",
        },
        "finding_count": total_findings,
        "findings_truncated": total_findings > len(ordered),
        "findings": [finding.to_dict() for finding in ordered],
    }


def run_audit(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    return audit_text(text, str(path), path.parent)


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        f"# Audit report: `{report['source']}`",
        "",
        f"- Decision: **{report['decision']}**",
        f"- Score: **{report['score']}/100**",
        f"- Template SHA-256: `{report['template_sha256']}`",
        f"- Findings: **{report['finding_count']}**",
        "- Evidence: static VERIFIED; LocalStack IAM UNVERIFIED; real AWS NOT_RUN",
        "",
    ]
    for finding in report["findings"]:
        lines.extend(
            [
                f"## {finding['severity']} · {finding['rule_id']} · {finding['title']}",
                "",
                f"**Path:** `{finding['path']}`",
                "",
                f"**Evidence:** {finding['evidence']}",
                "",
                f"**AWS behavior:** {finding['aws_behavior']}",
                "",
                f"**Impact:** {finding['impact']}",
                "",
                f"**Remediation:** {finding['remediation']}",
                "",
                f"**Verification:** {finding['verification']}",
                "",
            ]
        )
    return "\n".join(lines).rstrip() + "\n"


def render_sarif(report: dict[str, Any]) -> dict[str, Any]:
    levels = {"CRITICAL": "error", "HIGH": "error", "MEDIUM": "warning", "LOW": "note", "INFO": "note"}
    rules: dict[str, dict[str, Any]] = {}
    results = []
    for finding in report["findings"]:
        rules.setdefault(
            finding["rule_id"],
            {
                "id": finding["rule_id"],
                "shortDescription": {"text": finding["title"]},
                "help": {"text": finding["remediation"]},
            },
        )
        results.append(
            {
                "ruleId": finding["rule_id"],
                "level": levels[finding["severity"]],
                "message": {"text": f"{finding['evidence']} {finding['impact']}"},
                "locations": [
                    {
                        "physicalLocation": {
                            "artifactLocation": {"uri": report["source"]},
                            "region": {"snippet": {"text": finding["path"]}},
                        }
                    }
                ],
            }
        )
    return {
        "$schema": "https://json.schemastore.org/sarif-2.1.0.json",
        "version": "2.1.0",
        "runs": [
            {
                "tool": {
                    "driver": {
                        "name": "aws-serverless-audit-lab",
                        "informationUri": "https://github.com/marcusmayo/machine-learning-portfolio",
                        "rules": list(rules.values()),
                    }
                },
                "results": results,
            }
        ],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Audit a SAM/CloudFormation template without executing it")
    parser.add_argument("template", type=Path)
    parser.add_argument("--format", choices=("json", "markdown", "sarif"), default="markdown")
    args = parser.parse_args(argv)
    report = run_audit(args.template)
    if args.format == "markdown":
        print(render_markdown(report), end="")
    elif args.format == "sarif":
        print(json.dumps(render_sarif(report), indent=2, sort_keys=True))
    else:
        print(json.dumps(report, indent=2, sort_keys=True))
    return 1 if report["decision"] == "FAIL" else 0


if __name__ == "__main__":
    raise SystemExit(main())
