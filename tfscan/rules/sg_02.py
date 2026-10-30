"""
Rule SG-02: Security group allows ingress from 0.0.0.0/0 or ::/0 on port 3389 (RDP).
Evaluates inline ingress blocks in aws_security_group and standalone aws_security_group_rule resources.
"""
from tfscan.models import Severity
from tfscan.rules.sg_01 import SG01SshIngress


class SG02RdpIngress(SG01SshIngress):
    id = "SG-02"
    title = "Security group allows ingress from 0.0.0.0/0 or ::/0 on port 3389"
    severity = Severity.HIGH
    resource_types = ["aws_security_group", "aws_security_group_rule"]
    cis_controls = ["5.2", "5.3"]
    aws_controls = ["[EC2.53]", "[EC2.54]"]

    TARGET_PORT = 3389
