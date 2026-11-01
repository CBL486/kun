"""Sanitized quality findings and report models."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class Finding:
    code: str
    severity: str
    subject: str
    message: str

    def to_dict(self) -> dict[str, str]:
        return {
            "code": self.code,
            "severity": self.severity,
            "subject": self.subject,
            "message": self.message,
        }


@dataclass
class QualityReport:
    checks: list[str] = field(default_factory=list)
    findings: list[Finding] = field(default_factory=list)

    def add_check(self, name: str) -> None:
        if name not in self.checks:
            self.checks.append(name)

    def add(self, finding: Finding) -> None:
        self.findings.append(finding)

    @property
    def errors(self) -> list[Finding]:
        return [item for item in self.findings if item.severity == "error"]

    @property
    def warnings(self) -> list[Finding]:
        return [item for item in self.findings if item.severity == "warning"]

    @property
    def passed(self) -> bool:
        return not self.errors

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "rpg-quality-report-v1",
            "status": "passed" if self.passed else "blocked",
            "checks": list(self.checks),
            "error_count": len(self.errors),
            "warning_count": len(self.warnings),
            "findings": [item.to_dict() for item in self.findings],
        }
