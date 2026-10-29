"""
Rule catalog for tfscan.
Registers and provides access to all 12 AWS security misconfiguration rules.
"""
from typing import Dict, List, Type

from tfscan.rules.base import Rule
from tfscan.rules.s3_01 import S301PublicAccessBlock
from tfscan.rules.s3_02 import S302PublicAcl
from tfscan.rules.s3_03 import S303ExplicitEncryption
from tfscan.rules.sg_01 import SG01SshIngress
from tfscan.rules.sg_02 import SG02RdpIngress
from tfscan.rules.rds_01 import RDS01PubliclyAccessible
from tfscan.rules.rds_02 import RDS02StorageEncrypted
from tfscan.rules.ebs_01 import EBS01Encrypted
from tfscan.rules.ct_01 import CT01MultiRegionAndLogValidation
from tfscan.rules.iam_01 import IAM01WildcardAdmin
from tfscan.rules.kms_01 import KMS01KeyRotation
from tfscan.rules.sec_01 import SEC01HardcodedSecrets

RULE_CLASSES: List[Type[Rule]] = [
    S301PublicAccessBlock,
    S302PublicAcl,
    S303ExplicitEncryption,
    SG01SshIngress,
    SG02RdpIngress,
    RDS01PubliclyAccessible,
    RDS02StorageEncrypted,
    EBS01Encrypted,
    CT01MultiRegionAndLogValidation,
    IAM01WildcardAdmin,
    KMS01KeyRotation,
    SEC01HardcodedSecrets,
]

ALL_RULES: List[Rule] = [cls() for cls in RULE_CLASSES]
RULE_REGISTRY: Dict[str, Rule] = {rule.id: rule for rule in ALL_RULES}


def get_all_rules() -> List[Rule]:
    return ALL_RULES


def get_rule_by_id(rule_id: str) -> Rule | None:
    return RULE_REGISTRY.get(rule_id)
