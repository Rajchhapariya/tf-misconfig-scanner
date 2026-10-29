"""
Data models for tfscan.
"""
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional


class Status(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    UNKNOWN = "UNKNOWN"
    SKIPPED = "SKIPPED"


class Severity(str, Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INFORMATIONAL = "INFORMATIONAL"


@dataclass
class Resource:
    file_path: Path
    line_number: int
    resource_type: str
    resource_name: str
    address: str
    attributes: Dict[str, Any] = field(default_factory=dict)
    raw_block: Dict[str, Any] = field(default_factory=dict)

    def get_attr(self, name: str, default: Any = None) -> Any:
        return self.attributes.get(name, default)


@dataclass
class Finding:
    rule_id: str
    rule_title: str
    severity: Severity
    resource_address: str
    resource_type: str
    file_path: str
    line_number: int
    status: Status
    message: str
    cis_controls: List[str] = field(default_factory=list)
    aws_controls: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "rule_id": self.rule_id,
            "rule_title": self.rule_title,
            "severity": self.severity.value,
            "resource_address": self.resource_address,
            "resource_type": self.resource_type,
            "file_path": self.file_path,
            "line_number": self.line_number,
            "status": self.status.value,
            "message": self.message,
            "cis_controls": self.cis_controls,
            "aws_controls": self.aws_controls,
        }


@dataclass
class ScanResult:
    target_path: str
    files_scanned: int
    resources_evaluated: int
    findings: List[Finding] = field(default_factory=list)
    scan_duration_ms: float = 0.0

    @property
    def has_failures(self) -> bool:
        return any(f.status == Status.FAIL for f in self.findings)

    @property
    def summary(self) -> Dict[str, int]:
        counts = {"PASS": 0, "FAIL": 0, "UNKNOWN": 0, "TOTAL": len(self.findings)}
        for f in self.findings:
            if f.status.value in counts:
                counts[f.status.value] += 1
        return counts

    def to_dict(self) -> Dict[str, Any]:
        return {
            "target_path": self.target_path,
            "files_scanned": self.files_scanned,
            "resources_evaluated": self.resources_evaluated,
            "scan_duration_ms": self.scan_duration_ms,
            "summary": self.summary,
            "findings": [f.to_dict() for f in self.findings],
        }
