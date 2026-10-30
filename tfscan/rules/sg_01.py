"""
Rule SG-01: Security group allows ingress from 0.0.0.0/0 or ::/0 on port 22 (SSH).
Evaluates inline ingress blocks in aws_security_group and standalone aws_security_group_rule resources.
"""
from typing import Any, Dict, List, Tuple

from tfscan.models import Finding, Resource, Severity, Status
from tfscan.parser import ScanContext
from tfscan.rules.base import Rule


class SG01SshIngress(Rule):
    id = "SG-01"
    title = "Security group allows ingress from 0.0.0.0/0 or ::/0 on port 22"
    severity = Severity.HIGH
    resource_types = ["aws_security_group", "aws_security_group_rule"]
    cis_controls = ["5.2", "5.3"]
    aws_controls = ["[EC2.53]", "[EC2.54]"]

    TARGET_PORT = 22

    def _eval_ingress_rule(
        self, rule_data: Dict[str, Any], context: ScanContext
    ) -> Tuple[str, str]:
        """
        Evaluates a single ingress rule definition.
        Returns ("FAIL", reason), ("UNKNOWN", reason), or ("PASS", ok_message).
        """
        # Ports first: if the port range cannot cover the target port, the CIDR is irrelevant.
        from_port = rule_data.get("from_port")
        to_port = rule_data.get("to_port")
        protocol = rule_data.get("protocol", "tcp")

        res_from, is_from_res = context.resolve_attribute(from_port)
        res_to, is_to_res = context.resolve_attribute(to_port)
        res_proto, is_proto_res = context.resolve_attribute(protocol)

        if not is_from_res or not is_to_res or not is_proto_res:
            exposes = None  # unknown
            port_reason = "Ingress port/protocol expression cannot be resolved statically."
        elif str(res_proto).lower() in ["-1", "all"]:
            exposes = True
            port_reason = f"all protocols/ports (includes port {self.TARGET_PORT})"
        else:
            try:
                fp = int(res_from) if res_from is not None else 0
                tp = int(res_to) if res_to is not None else 0
            except (ValueError, TypeError):
                exposes = None
                port_reason = f"Could not parse port range integers ({res_from}-{res_to})."
            else:
                exposes = (fp == 0 and tp == 0) or (fp <= self.TARGET_PORT <= tp)
                port_reason = f"range {fp}-{tp}"

        if exposes is False:
            return "PASS", "Port range does not expose target administrative port."

        cidrs = rule_data.get("cidr_blocks") or []
        ipv6_cidrs = rule_data.get("ipv6_cidr_blocks") or []
        resolved_cidrs, is_cidrs_res = context.resolve_attribute(cidrs)
        resolved_ipv6, is_ipv6_res = context.resolve_attribute(ipv6_cidrs)

        if not is_cidrs_res or not is_ipv6_res:
            return "UNKNOWN", "Ingress CIDR block expression cannot be resolved statically."

        cidr_list = resolved_cidrs if isinstance(resolved_cidrs, list) else [resolved_cidrs]
        ipv6_list = resolved_ipv6 if isinstance(resolved_ipv6, list) else [resolved_ipv6]
        is_open = any(c == "0.0.0.0/0" for c in cidr_list if c is not None) or any(
            c == "::/0" for c in ipv6_list if c is not None
        )

        if not is_open:
            return "PASS", "No public 0.0.0.0/0 or ::/0 CIDR in ingress rule."
        if exposes is None:
            return "UNKNOWN", port_reason
        return "FAIL", f"Ingress rule allows unrestricted access to port {self.TARGET_PORT} ({port_reason})."


    def evaluate(self, resource: Resource, context: ScanContext) -> Finding:
        if resource.resource_type == "aws_security_group_rule":
            rule_type = resource.get_attr("type")
            res_type, is_type_res = context.resolve_attribute(rule_type)
            if not is_type_res:
                return self.make_finding(
                    resource, Status.UNKNOWN, "Rule type expression cannot be resolved statically."
                )
            if str(res_type).lower() != "ingress":
                return self.make_finding(
                    resource, Status.PASS, "Security group rule is not an ingress rule."
                )

            status_str, reason = self._eval_ingress_rule(resource.attributes, context)
            return self.make_finding(resource, Status[status_str], reason)

        # For aws_security_group, inspect inline ingress rules
        raw_ingress = resource.get_attr("ingress")
        if not raw_ingress:
            return self.make_finding(
                resource, Status.PASS, "Security group defines no inline ingress rules."
            )

        ingress_blocks = raw_ingress if isinstance(raw_ingress, list) else [raw_ingress]
        has_unknown = False
        unknown_msg = ""

        for block in ingress_blocks:
            if not isinstance(block, dict):
                continue
            status_str, reason = self._eval_ingress_rule(block, context)
            if status_str == "FAIL":
                return self.make_finding(resource, Status.FAIL, reason)
            elif status_str == "UNKNOWN":
                has_unknown = True
                unknown_msg = reason

        if has_unknown:
            return self.make_finding(resource, Status.UNKNOWN, unknown_msg)

        return self.make_finding(
            resource,
            Status.PASS,
            f"Security group does not allow unrestricted ingress to port {self.TARGET_PORT}.",
        )
