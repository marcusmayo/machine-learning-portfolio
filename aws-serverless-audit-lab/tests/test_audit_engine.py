from __future__ import annotations

import json
from pathlib import Path

import yaml

from audit.audit_template import audit_text, render_markdown, render_sarif, run_audit

ROOT = Path(__file__).parents[1]


def _ids(report: dict) -> set[str]:
    return {finding["rule_id"] for finding in report["findings"]}


def test_reference_template_has_no_blocking_findings() -> None:
    report = run_audit(ROOT / "template.yaml")
    assert report["decision"] != "FAIL", json.dumps(report["findings"], indent=2)
    assert report["evidence_boundary"]["localstack_iam"] == "UNVERIFIED"
    assert len(report["template_sha256"]) == 64


def test_each_corpus_case_contains_expected_findings() -> None:
    for case in sorted((ROOT / "task_cases").iterdir()):
        expected = yaml.safe_load((case / "expected.yaml").read_text(encoding="utf-8"))
        report = run_audit(case / "template.yaml")
        assert report["decision"] == expected["decision"]
        assert set(expected["required_rule_ids"]).issubset(_ids(report))


def test_invalid_template_fails_closed() -> None:
    report = audit_text("Resources: [", source="broken.yaml")
    assert report["decision"] == "FAIL"
    assert _ids(report) == {"CFN001"}


def test_report_formats_are_deterministic_and_redacted() -> None:
    report = run_audit(ROOT / "task_cases/T01_iam_secret/template.yaml")
    markdown = render_markdown(report)
    sarif = render_sarif(report)
    assert "IAM001" in markdown
    assert sarif["version"] == "2.1.0"
    assert {result["ruleId"] for result in sarif["runs"][0]["results"]} == _ids(report)
    assert "sk_live_committed_example" not in markdown
