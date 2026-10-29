"""
Base rule definition for tfscan.
Each rule defines its ID, title, severity, checked resource types,
CIS control mappings, and evaluation logic.
"""
from abc import ABC, abstractmethod
from typing import List

from tfscan.models import Finding, Resource, Severity, Status
from tfscan.parser import ScanContext


class Rule(ABC):
    id: str
    title: str
    severity: Severity
    resource_types: List[str]
    cis_controls: List[str] = []
    aws_controls: List[str] = []

    def make_finding(
        self,
        resource: Resource,
        status: Status,
        message: str,
        line_number: int | None = None,
    ) -> Finding:
        return Finding(
            rule_id=self.id,
            rule_title=self.title,
            severity=self.severity,
            resource_address=resource.address,
            resource_type=resource.resource_type,
            file_path=str(resource.file_path),
            line_number=line_number or resource.line_number,
            status=status,
            message=message,
            cis_controls=list(self.cis_controls),
            aws_controls=list(self.aws_controls),
        )

    @abstractmethod
    def evaluate(self, resource: Resource, context: ScanContext) -> Finding:
        """
        Evaluate the resource against the rule.
        Returns a Finding with status FAIL, PASS, or UNKNOWN.
        """
        pass
