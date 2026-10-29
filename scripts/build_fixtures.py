"""
Generator for comprehensive hand-crafted test fixtures across all 12 rules.
Produces >= 3 FAIL, >= 3 PASS, and >= 2 UNKNOWN cases per rule.
Emits fixtures/<rule_id>/{fail,pass,unknown}/*.tf and labels/fixture_labels.csv.
"""
import csv
import os
from pathlib import Path

FIXTURES_ROOT = Path(__file__).resolve().parent.parent / "fixtures"
LABELS_CSV = Path(__file__).resolve().parent.parent / "labels" / "fixture_labels.csv"

# Map of rule_id -> dict with fail, pass, unknown definitions
FIXTURE_DEFS = {
    "S3-01": {
        "fail": [
            ("case1_v3_no_pab.tf", """
resource "aws_s3_bucket" "b" {
  bucket = "test-no-pab-bucket"
}
"""),
            ("case2_v4_pab_partial.tf", """
resource "aws_s3_bucket" "b" {
  bucket = "test-partial-pab-bucket"
}

resource "aws_s3_bucket_public_access_block" "pab" {
  bucket                  = aws_s3_bucket.b.id
  block_public_acls       = true
  block_public_policy     = false
  ignore_public_acls      = true
  restrict_public_buckets = true
}
"""),
            ("case3_v4_pab_all_false.tf", """
resource "aws_s3_bucket" "b" {
  bucket = "test-all-false-pab-bucket"
}

resource "aws_s3_bucket_public_access_block" "pab" {
  bucket                  = aws_s3_bucket.b.id
  block_public_acls       = false
  block_public_policy     = false
  ignore_public_acls      = false
  restrict_public_buckets = false
}
"""),
        ],
        "pass": [
            ("case1_v4_pab_all_true.tf", """
resource "aws_s3_bucket" "b" {
  bucket = "test-pab-compliant-bucket"
}

resource "aws_s3_bucket_public_access_block" "pab" {
  bucket                  = aws_s3_bucket.b.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}
"""),
            ("case2_v4_pab_linked_by_bucket_attr.tf", """
resource "aws_s3_bucket" "b" {
  bucket = "test-pab-attr-bucket"
}

resource "aws_s3_bucket_public_access_block" "pab" {
  bucket                  = aws_s3_bucket.b.bucket
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}
"""),
            ("case3_v4_pab_linked_by_name.tf", """
resource "aws_s3_bucket" "b" {
  bucket = "secure-corporate-logs"
}

resource "aws_s3_bucket_public_access_block" "pab" {
  bucket                  = "secure-corporate-logs"
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}
"""),
        ],
        "unknown": [
            ("case1_var_unresolved.tf", """
variable "unresolved_block_flag" {
  type = bool
}

resource "aws_s3_bucket" "b" {
  bucket = "test-unknown-pab-bucket"
}

resource "aws_s3_bucket_public_access_block" "pab" {
  bucket                  = aws_s3_bucket.b.id
  block_public_acls       = var.unresolved_block_flag
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}
"""),
            ("case2_data_source.tf", """
data "aws_ssm_parameter" "block_policy" {
  name = "/infra/s3/block_policy"
}

resource "aws_s3_bucket" "b" {
  bucket = "test-unknown-data-pab-bucket"
}

resource "aws_s3_bucket_public_access_block" "pab" {
  bucket                  = aws_s3_bucket.b.id
  block_public_acls       = true
  block_public_policy     = data.aws_ssm_parameter.block_policy.value
  ignore_public_acls      = true
  restrict_public_buckets = true
}
"""),
        ],
    },
    "S3-02": {
        "fail": [
            ("case1_v3_public_read.tf", """
resource "aws_s3_bucket" "b" {
  bucket = "public-read-bucket"
  acl    = "public-read"
}
"""),
            ("case2_v3_public_read_write.tf", """
resource "aws_s3_bucket" "b" {
  bucket = "public-read-write-bucket"
  acl    = "public-read-write"
}
"""),
            ("case3_v4_acl_public_read.tf", """
resource "aws_s3_bucket" "b" {
  bucket = "v4-public-read-bucket"
}

resource "aws_s3_bucket_acl" "b_acl" {
  bucket = aws_s3_bucket.b.id
  acl    = "public-read"
}
"""),
        ],
        "pass": [
            ("case1_v3_private.tf", """
resource "aws_s3_bucket" "b" {
  bucket = "private-bucket"
  acl    = "private"
}
"""),
            ("case2_v4_acl_private.tf", """
resource "aws_s3_bucket" "b" {
  bucket = "v4-private-bucket"
}

resource "aws_s3_bucket_acl" "b_acl" {
  bucket = aws_s3_bucket.b.id
  acl    = "private"
}
"""),
            ("case3_v4_acl_log_delivery_write.tf", """
resource "aws_s3_bucket" "b" {
  bucket = "log-bucket"
}

resource "aws_s3_bucket_acl" "b_acl" {
  bucket = aws_s3_bucket.b.id
  acl    = "log-delivery-write"
}
"""),
        ],
        "unknown": [
            ("case1_var_acl.tf", """
variable "bucket_acl_choice" {
  type = string
}

resource "aws_s3_bucket" "b" {
  bucket = "unknown-acl-bucket"
  acl    = var.bucket_acl_choice
}
"""),
            ("case2_module_output_acl.tf", """
resource "aws_s3_bucket" "b" {
  bucket = "unknown-v4-acl-bucket"
}

resource "aws_s3_bucket_acl" "b_acl" {
  bucket = aws_s3_bucket.b.id
  acl    = module.policy_loader.calculated_acl
}
"""),
        ],
    },
    "S3-03": {
        "fail": [
            ("case1_v3_no_sse.tf", """
resource "aws_s3_bucket" "b" {
  bucket = "unencrypted-v3-bucket"
}
"""),
            ("case2_v4_no_sse.tf", """
resource "aws_s3_bucket" "b" {
  bucket = "unencrypted-v4-bucket"
}
"""),
            ("case3_v4_unrelated_resource.tf", """
resource "aws_s3_bucket" "b" {
  bucket = "unencrypted-target-bucket"
}

resource "aws_s3_bucket_versioning" "v" {
  bucket = aws_s3_bucket.b.id
  versioning_configuration {
    status = "Enabled"
  }
}
"""),
        ],
        "pass": [
            ("case1_v3_sse_aes256.tf", """
resource "aws_s3_bucket" "b" {
  bucket = "v3-aes256-bucket"
  server_side_encryption_configuration {
    rule {
      apply_server_side_encryption_by_default {
        sse_algorithm = "AES256"
      }
    }
  }
}
"""),
            ("case2_v3_sse_kms.tf", """
resource "aws_s3_bucket" "b" {
  bucket = "v3-kms-bucket"
  server_side_encryption_configuration {
    rule {
      apply_server_side_encryption_by_default {
        sse_algorithm     = "aws:kms"
        kms_master_key_id = "arn:aws:kms:us-east-1:123456789012:key/12345678"
      }
    }
  }
}
"""),
            ("case3_v4_sse_resource.tf", """
resource "aws_s3_bucket" "b" {
  bucket = "v4-sse-bucket"
}

resource "aws_s3_bucket_server_side_encryption_configuration" "sse" {
  bucket = aws_s3_bucket.b.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "aws:kms"
    }
  }
}
"""),
            ("case4_kms_key_from_module.tf", """
resource "aws_s3_bucket" "b" {
  bucket = "pass-v4-sse-kms-key-from-module"
}

resource "aws_s3_bucket_server_side_encryption_configuration" "sse" {
  bucket = aws_s3_bucket.b.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm     = "aws:kms"
      kms_master_key_id = module.shared_kms.key_arn
    }
  }
}
"""),
        ],
        "unknown": [
            ("case1_unresolved_algo.tf", """
variable "unresolved_sse_algo" {
  type = string
}

resource "aws_s3_bucket" "b" {
  bucket = "unknown-sse-bucket"
  server_side_encryption_configuration {
    rule {
      apply_server_side_encryption_by_default {
        sse_algorithm = var.unresolved_sse_algo
      }
    }
  }
}
"""),
            ("case2_data_source_algo.tf", """
data "aws_ssm_parameter" "sse_algo" {
  name = "/platform/s3/sse_algorithm"
}

resource "aws_s3_bucket" "b" {
  bucket = "unknown-v4-sse-algo-from-ssm"
}

resource "aws_s3_bucket_server_side_encryption_configuration" "sse" {
  bucket = aws_s3_bucket.b.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = data.aws_ssm_parameter.sse_algo.value
    }
  }
}
"""),
        ],
    },
    "SG-01": {
        "fail": [
            ("case1_inline_all_0.tf", """
resource "aws_security_group" "sg" {
  name = "open-ssh-inline"
  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
}
"""),
            ("case2_rule_resource_ipv6.tf", """
resource "aws_security_group" "sg" {
  name = "open-ssh-ipv6-sg"
}

resource "aws_security_group_rule" "ssh_ipv6" {
  type              = "ingress"
  from_port         = 22
  to_port           = 22
  protocol          = "tcp"
  ipv6_cidr_blocks  = ["::/0"]
  security_group_id = aws_security_group.sg.id
}
"""),
            ("case3_port_range_includes_22.tf", """
resource "aws_security_group" "sg" {
  name = "open-range-sg"
  ingress {
    from_port   = 20
    to_port     = 25
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
}
"""),
        ],
        "pass": [
            ("case1_restricted_cidr.tf", """
resource "aws_security_group" "sg" {
  name = "bastion-ssh-sg"
  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["10.0.0.0/16"]
  }
}
"""),
            ("case2_different_port.tf", """
resource "aws_security_group" "sg" {
  name = "web-http-sg"
  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
}
"""),
            ("case3_egress_only.tf", """
resource "aws_security_group" "sg" {
  name = "egress-ssh-sg"
}

resource "aws_security_group_rule" "ssh_egress" {
  type              = "egress"
  from_port         = 22
  to_port           = 22
  protocol          = "tcp"
  cidr_blocks       = ["0.0.0.0/0"]
  security_group_id = aws_security_group.sg.id
}
"""),
        ],
        "unknown": [
            ("case1_cidr_variable.tf", """
variable "remote_admin_cidr" {
  type = string
}

resource "aws_security_group" "sg" {
  name = "unknown-cidr-ssh-sg"
  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = [var.remote_admin_cidr]
  }
}
"""),
            ("case2_port_variable.tf", """
variable "dynamic_ingress_port" {
  type = number
}

resource "aws_security_group" "sg" {
  name = "unknown-port-sg"
  ingress {
    from_port   = var.dynamic_ingress_port
    to_port     = var.dynamic_ingress_port
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
}
"""),
        ],
    },
    "SG-02": {
        "fail": [
            ("case1_inline_rdp.tf", """
resource "aws_security_group" "sg" {
  name = "open-rdp-inline"
  ingress {
    from_port   = 3389
    to_port     = 3389
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
}
"""),
            ("case2_rule_ipv6_rdp.tf", """
resource "aws_security_group" "sg" {
  name = "open-rdp-rule"
}

resource "aws_security_group_rule" "rdp_rule" {
  type              = "ingress"
  from_port         = 3389
  to_port           = 3389
  protocol          = "tcp"
  ipv6_cidr_blocks  = ["::/0"]
  security_group_id = aws_security_group.sg.id
}
"""),
            ("case3_all_traffic_rdp.tf", """
resource "aws_security_group" "sg" {
  name = "all-traffic-sg"
  ingress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}
"""),
        ],
        "pass": [
            ("case1_restricted_ip.tf", """
resource "aws_security_group" "sg" {
  name = "restricted-rdp-sg"
  ingress {
    from_port   = 3389
    to_port     = 3389
    protocol    = "tcp"
    cidr_blocks = ["192.168.1.50/32"]
  }
}
"""),
            ("case2_port_443.tf", """
resource "aws_security_group" "sg" {
  name = "web-https-sg"
  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
}
"""),
            ("case3_rule_internal.tf", """
resource "aws_security_group" "sg" {
  name = "internal-rdp-sg"
}

resource "aws_security_group_rule" "rdp_internal" {
  type              = "ingress"
  from_port         = 3389
  to_port           = 3389
  protocol          = "tcp"
  cidr_blocks       = ["10.1.0.0/16"]
  security_group_id = aws_security_group.sg.id
}
"""),
        ],
        "unknown": [
            ("case1_cidr_var.tf", """
variable "office_rdp_cidr" {
  type = string
}

resource "aws_security_group" "sg" {
  name = "unknown-rdp-sg"
  ingress {
    from_port   = 3389
    to_port     = 3389
    protocol    = "tcp"
    cidr_blocks = [var.office_rdp_cidr]
  }
}
"""),
            ("case2_rule_remote_state.tf", """
data "terraform_remote_state" "net" {
  backend = "local"
}

resource "aws_security_group" "sg" {
  name = "unknown-remote-rdp-sg"
}

resource "aws_security_group_rule" "rdp_state" {
  type              = "ingress"
  from_port         = 3389
  to_port           = 3389
  protocol          = "tcp"
  cidr_blocks       = [data.terraform_remote_state.net.outputs.vpn_cidr]
  security_group_id = aws_security_group.sg.id
}
"""),
        ],
    },
    "RDS-01": {
        "fail": [
            ("case1_explicit_true.tf", """
resource "aws_db_instance" "db" {
  instance_class      = "db.t3.micro"
  engine              = "mysql"
  publicly_accessible = true
}
"""),
            ("case2_resolved_default_true.tf", """
variable "public_db_flag" {
  type    = bool
  default = true
}

resource "aws_db_instance" "db" {
  instance_class      = "db.t3.micro"
  engine              = "postgres"
  publicly_accessible = var.public_db_flag
}
"""),
            ("case3_expression_true.tf", """
locals {
  is_exposed = true
}

resource "aws_db_instance" "db" {
  instance_class      = "db.t3.micro"
  engine              = "mariadb"
  publicly_accessible = local.is_exposed
}
"""),
        ],
        "pass": [
            ("case1_explicit_false.tf", """
resource "aws_db_instance" "db" {
  instance_class      = "db.t3.micro"
  engine              = "mysql"
  publicly_accessible = false
}
"""),
            ("case2_omitted_default_false.tf", """
resource "aws_db_instance" "db" {
  instance_class = "db.t3.micro"
  engine         = "postgres"
}
"""),
            ("case3_resolved_default_false.tf", """
variable "public_db_flag" {
  type    = bool
  default = false
}

resource "aws_db_instance" "db" {
  instance_class      = "db.t3.micro"
  engine              = "oracle-ee"
  publicly_accessible = var.public_db_flag
}
"""),
        ],
        "unknown": [
            ("case1_unresolved_var.tf", """
variable "unresolved_db_public" {
  type = bool
}

resource "aws_db_instance" "db" {
  instance_class      = "db.t3.micro"
  engine              = "mysql"
  publicly_accessible = var.unresolved_db_public
}
"""),
            ("case2_data_source.tf", """
data "aws_ssm_parameter" "db_exposure" {
  name = "/config/db_public"
}

resource "aws_db_instance" "db" {
  instance_class      = "db.t3.micro"
  engine              = "postgres"
  publicly_accessible = data.aws_ssm_parameter.db_exposure.value
}
"""),
        ],
    },
    "RDS-02": {
        "fail": [
            ("case1_explicit_false.tf", """
resource "aws_db_instance" "db" {
  instance_class    = "db.t3.micro"
  engine            = "mysql"
  storage_encrypted = false
}
"""),
            ("case2_omitted_missing.tf", """
resource "aws_db_instance" "db" {
  instance_class = "db.t3.micro"
  engine         = "postgres"
}
"""),
            ("case3_resolved_default_false.tf", """
variable "encrypt_storage_flag" {
  type    = bool
  default = false
}

resource "aws_db_instance" "db" {
  instance_class    = "db.t3.micro"
  engine            = "mysql"
  storage_encrypted = var.encrypt_storage_flag
}
"""),
        ],
        "pass": [
            ("case1_explicit_true.tf", """
resource "aws_db_instance" "db" {
  instance_class    = "db.t3.micro"
  engine            = "mysql"
  storage_encrypted = true
}
"""),
            ("case2_with_kms_key.tf", """
resource "aws_db_instance" "db" {
  instance_class    = "db.t3.micro"
  engine            = "postgres"
  storage_encrypted = true
  kms_key_id        = "arn:aws:kms:us-east-1:123456789012:key/sample-key"
}
"""),
            ("case3_resolved_default_true.tf", """
variable "encrypt_storage_flag" {
  type    = bool
  default = true
}

resource "aws_db_instance" "db" {
  instance_class    = "db.t3.micro"
  engine            = "mariadb"
  storage_encrypted = var.encrypt_storage_flag
}
"""),
        ],
        "unknown": [
            ("case1_unresolved_var.tf", """
variable "unresolved_storage_enc" {
  type = bool
}

resource "aws_db_instance" "db" {
  instance_class    = "db.t3.micro"
  engine            = "mysql"
  storage_encrypted = var.unresolved_storage_enc
}
"""),
            ("case2_module_output.tf", """
resource "aws_db_instance" "db" {
  instance_class    = "db.t3.micro"
  engine            = "postgres"
  storage_encrypted = module.compliance_baseline.storage_encrypted
}
"""),
        ],
    },
    "EBS-01": {
        "fail": [
            ("case1_explicit_false.tf", """
resource "aws_ebs_volume" "vol" {
  availability_zone = "us-east-1a"
  size              = 40
  encrypted         = false
}
"""),
            ("case2_omitted_missing.tf", """
resource "aws_ebs_volume" "vol" {
  availability_zone = "us-east-1a"
  size              = 20
}
"""),
            ("case3_resolved_default_false.tf", """
variable "encrypt_volume" {
  type    = bool
  default = false
}

resource "aws_ebs_volume" "vol" {
  availability_zone = "us-east-1b"
  size              = 50
  encrypted         = var.encrypt_volume
}
"""),
        ],
        "pass": [
            ("case1_explicit_true.tf", """
resource "aws_ebs_volume" "vol" {
  availability_zone = "us-east-1a"
  size              = 40
  encrypted         = true
}
"""),
            ("case2_with_kms.tf", """
resource "aws_ebs_volume" "vol" {
  availability_zone = "us-east-1a"
  size              = 100
  encrypted         = true
  kms_key_id        = "arn:aws:kms:us-east-1:123456789012:key/vol-key"
}
"""),
            ("case3_resolved_default_true.tf", """
variable "encrypt_volume" {
  type    = bool
  default = true
}

resource "aws_ebs_volume" "vol" {
  availability_zone = "us-east-1c"
  size              = 80
  encrypted         = var.encrypt_volume
}
"""),
        ],
        "unknown": [
            ("case1_unresolved_var.tf", """
variable "unresolved_ebs_enc" {
  type = bool
}

resource "aws_ebs_volume" "vol" {
  availability_zone = "us-east-1a"
  size              = 10
  encrypted         = var.unresolved_ebs_enc
}
"""),
            ("case2_data_lookup.tf", """
data "external" "volume_flags" {
  program = ["python", "-c", "import sys, json; json.dump({'encrypted': 'true'}, sys.stdout)"]
}

resource "aws_ebs_volume" "vol" {
  availability_zone = "us-east-1a"
  size              = 15
  encrypted         = data.external.volume_flags.result.encrypted
}
"""),
        ],
    },
    "CT-01": {
        "fail": [
            ("case1_single_region.tf", """
resource "aws_cloudtrail" "trail" {
  name                          = "single-region-trail"
  s3_bucket_name                = "audit-bucket"
  is_multi_region_trail         = false
  enable_log_file_validation    = true
}
"""),
            ("case2_no_log_validation.tf", """
resource "aws_cloudtrail" "trail" {
  name                          = "no-log-validation-trail"
  s3_bucket_name                = "audit-bucket"
  is_multi_region_trail         = true
  enable_log_file_validation    = false
}
"""),
            ("case3_both_omitted.tf", """
resource "aws_cloudtrail" "trail" {
  name           = "default-trail"
  s3_bucket_name = "audit-bucket"
}
"""),
        ],
        "pass": [
            ("case1_both_true.tf", """
resource "aws_cloudtrail" "trail" {
  name                          = "compliant-trail"
  s3_bucket_name                = "audit-bucket"
  is_multi_region_trail         = true
  enable_log_file_validation    = true
}
"""),
            ("case2_resolved_defaults_true.tf", """
variable "multi_region" {
  type    = bool
  default = true
}

variable "log_validation" {
  type    = bool
  default = true
}

resource "aws_cloudtrail" "trail" {
  name                          = "compliant-var-trail"
  s3_bucket_name                = "audit-bucket"
  is_multi_region_trail         = var.multi_region
  enable_log_file_validation    = var.log_validation
}
"""),
            ("case3_full_compliant_trail.tf", """
resource "aws_cloudtrail" "trail" {
  name                          = "corporate-audit-trail"
  s3_bucket_name                = "sec-logs-bucket"
  is_multi_region_trail         = true
  enable_log_file_validation    = true
  kms_key_id                    = "arn:aws:kms:us-east-1:123456789012:key/trail-key"
}
"""),
        ],
        "unknown": [
            ("case1_unresolved_multi_region.tf", """
variable "unresolved_multi_region" {
  type = bool
}

resource "aws_cloudtrail" "trail" {
  name                          = "unknown-trail-1"
  s3_bucket_name                = "audit-bucket"
  is_multi_region_trail         = var.unresolved_multi_region
  enable_log_file_validation    = true
}
"""),
            ("case2_unresolved_validation.tf", """
variable "unresolved_validation" {
  type = bool
}

resource "aws_cloudtrail" "trail" {
  name                          = "unknown-trail-2"
  s3_bucket_name                = "audit-bucket"
  is_multi_region_trail         = true
  enable_log_file_validation    = var.unresolved_validation
}
"""),
        ],
    },
    "IAM-01": {
        "fail": [
            ("case1_json_inline_admin.tf", """
resource "aws_iam_policy" "admin" {
  name = "full-admin-policy"
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = "*"
        Resource = "*"
      }
    ]
  })
}
"""),
            ("case2_heredoc_policy.tf", """
resource "aws_iam_role_policy" "role_admin" {
  name = "role-admin-policy"
  role = "admin-role"
  policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": "*",
      "Resource": "*"
    }
  ]
}
EOF
}
"""),
            ("case3_action_list_star.tf", """
resource "aws_iam_user_policy" "user_admin" {
  name = "user-admin-policy"
  user = "admin-user"
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = ["*"]
        Resource = ["*"]
      }
    ]
  })
}
"""),
        ],
        "pass": [
            ("case1_scoped_actions.tf", """
resource "aws_iam_policy" "read_only" {
  name = "read-only-policy"
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = ["s3:GetObject", "s3:ListBucket"]
        Resource = "*"
      }
    ]
  })
}
"""),
            ("case2_scoped_resources.tf", """
resource "aws_iam_policy" "bucket_admin" {
  name = "bucket-admin-policy"
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = "*"
        Resource = "arn:aws:s3:::my-special-bucket/*"
      }
    ]
  })
}
"""),
            ("case3_effect_deny.tf", """
resource "aws_iam_policy" "deny_all" {
  name = "deny-all-policy"
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Deny"
        Action   = "*"
        Resource = "*"
      }
    ]
  })
}
"""),
        ],
        "unknown": [
            ("case1_policy_variable.tf", """
variable "custom_raw_policy" {
  type = string
}

resource "aws_iam_policy" "dynamic_policy" {
  name   = "dynamic-iam-policy"
  policy = var.custom_raw_policy
}
"""),
            ("case2_template_file.tf", """
data "template_file" "rendered_policy" {
  template = "${file(\"${path.module}/policy.json\")}"
}

resource "aws_iam_policy" "templated_policy" {
  name   = "templated-iam-policy"
  policy = data.template_file.rendered_policy.rendered
}
"""),
        ],
    },
    "KMS-01": {
        "fail": [
            ("case1_explicit_false.tf", """
resource "aws_kms_key" "key" {
  description         = "key-without-rotation"
  enable_key_rotation = false
}
"""),
            ("case2_omitted_missing.tf", """
resource "aws_kms_key" "key" {
  description = "key-default-rotation"
}
"""),
            ("case3_resolved_default_false.tf", """
variable "rotate_kms_keys" {
  type    = bool
  default = false
}

resource "aws_kms_key" "key" {
  description         = "key-var-false"
  enable_key_rotation = var.rotate_kms_keys
}
"""),
        ],
        "pass": [
            ("case1_explicit_true.tf", """
resource "aws_kms_key" "key" {
  description         = "compliant-kms-key"
  enable_key_rotation = true
}
"""),
            ("case2_resolved_default_true.tf", """
variable "rotate_kms_keys" {
  type    = bool
  default = true
}

resource "aws_kms_key" "key" {
  description         = "compliant-var-key"
  enable_key_rotation = var.rotate_kms_keys
}
"""),
            ("case3_rotation_period.tf", """
resource "aws_kms_key" "key" {
  description              = "compliant-period-key"
  enable_key_rotation      = true
  rotation_period_in_days  = 90
}
"""),
        ],
        "unknown": [
            ("case1_unresolved_rotation.tf", """
variable "unresolved_key_rotation" {
  type = bool
}

resource "aws_kms_key" "key" {
  description         = "unknown-rotation-key"
  enable_key_rotation = var.unresolved_key_rotation
}
"""),
            ("case2_module_kms_rotation.tf", """
resource "aws_kms_key" "key" {
  description         = "unknown-module-key"
  enable_key_rotation = module.kms_policy.rotation_enabled
}
"""),
        ],
    },
    "SEC-01": {
        "fail": [
            ("case1_provider_access_key.tf", """
provider "aws" {
  region     = "us-east-1"
  access_key = "AKIAIOSFODNN7EXAMPLE"
  secret_key = "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
}
"""),
            ("case2_db_literal_password.tf", """
resource "aws_db_instance" "db" {
  instance_class = "db.t3.micro"
  engine         = "mysql"
  username       = "admin"
  password       = "SuperSecretPassword123!"
}
"""),
            ("case3_resolved_default_password.tf", """
variable "db_password" {
  type    = string
  default = "ProductionSecretPass!99"
}

resource "aws_db_instance" "db" {
  instance_class = "db.t3.micro"
  engine         = "postgres"
  username       = "dbadmin"
  password       = var.db_password
}
"""),
        ],
        "pass": [
            ("case1_provider_no_keys.tf", """
provider "aws" {
  region = "us-west-2"
}
"""),
            ("case2_var_no_default.tf", """
resource "aws_db_instance" "db" {
  instance_class                      = "db.t3.micro"
  engine                              = "mysql"
  username                            = "admin"
  iam_database_authentication_enabled = true
}
"""),
            ("case3_secrets_manager_ref.tf", """
provider "aws" {
  region = "us-east-1"
  assume_role {
    role_arn = "arn:aws:iam::123456789012:role/DeployerRole"
  }
}
"""),
        ],
        "unknown": [
            ("case1_unresolved_var_password.tf", """
variable "unresolved_secret" {
  type = string
}

resource "aws_db_instance" "db" {
  instance_class = "db.t3.micro"
  engine         = "mysql"
  username       = "admin"
  password       = var.unresolved_secret
}
"""),
            ("case2_vault_secret.tf", """
data "vault_generic_secret" "db" {
  path = "secret/db"
}

resource "aws_db_instance" "db" {
  instance_class = "db.t3.micro"
  engine         = "mysql"
  username       = "admin"
  password       = data.vault_generic_secret.db.data["password"]
}
"""),
        ],
    },
}


def build_fixtures():
    total_files = 0
    labels = []
    for rule_id, status_dict in FIXTURE_DEFS.items():
        for status, cases in status_dict.items():
            expected = status.upper()
            target_dir = FIXTURES_ROOT / rule_id / status
            target_dir.mkdir(parents=True, exist_ok=True)
            for fname, tf_code in cases:
                file_path = target_dir / fname
                file_path.write_text(tf_code.strip() + "\n", encoding="utf-8")
                total_files += 1
                rel_path = f"fixtures/{rule_id}/{status}/{fname}"
                labels.append((rel_path, rule_id, expected, f"Fixture test case for {rule_id} expecting {expected}"))

    # Write fixture labels CSV
    LABELS_CSV.parent.mkdir(parents=True, exist_ok=True)
    with open(LABELS_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, lineterminator="\n")
        writer.writerow(["file", "rule_id", "expected", "note"])
        for row in labels:
            writer.writerow(row)

    print(f"Generated {total_files} fixture files across {len(FIXTURE_DEFS)} rules.")
    print(f"Wrote {len(labels)} fixture labels to {LABELS_CSV}")


if __name__ == "__main__":
    build_fixtures()
