from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

SEVERITY_RANK = {"CRITICAL": 4, "HIGH": 3, "MEDIUM": 2, "LOW": 1, "INFO": 0}


@dataclass(frozen=True)
class Finding:
    rule_id: str
    severity: str
    title: str
    path: str
    evidence: str
    aws_behavior: str
    impact: str
    remediation: str
    verification: str

    def __post_init__(self) -> None:
        if self.severity not in SEVERITY_RANK:
            raise ValueError(f"unsupported severity: {self.severity}")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def sort_findings(findings: list[Finding]) -> list[Finding]:
    return sorted(
        findings,
        key=lambda item: (-SEVERITY_RANK[item.severity], item.rule_id, item.path),
    )
