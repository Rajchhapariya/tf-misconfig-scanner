"""
Unit tests for the Terraform parser and expression resolver.
"""
from pathlib import Path
import pytest

from tfscan.models import Status
from tfscan.parser import parse_directory, resolve_value


def test_parse_simple_fixture(tmp_path):
    tf_file = tmp_path / "main.tf"
    tf_file.write_text("""
variable "env" {
  type    = string
  default = "production"
}

resource "aws_s3_bucket" "example" {
  bucket = "my-${var.env}-bucket"
  acl    = "private"
}
""", encoding="utf-8")

    ctx = parse_directory(tmp_path)
    assert len(ctx.files) == 1
    assert "env" in ctx.variables
    assert ctx.variables["env"] == "production"

    buckets = ctx.get_resources_by_type("aws_s3_bucket")
    assert len(buckets) == 1
    b = buckets[0]
    assert b.resource_name == "example"

    # Test resolved bucket name
    res_val, ok = ctx.resolve_attribute(b.get_attr("bucket"))
    assert ok is True
    assert res_val == "my-production-bucket"


def test_unresolved_variable_returns_false(tmp_path):
    tf_file = tmp_path / "main.tf"
    tf_file.write_text("""
variable "unassigned_var" {
  type = string
}

resource "aws_db_instance" "db" {
  instance_class      = "db.t3.micro"
  publicly_accessible = var.unassigned_var
}
""", encoding="utf-8")

    ctx = parse_directory(tmp_path)
    dbs = ctx.get_resources_by_type("aws_db_instance")
    assert len(dbs) == 1

    res_val, ok = ctx.resolve_attribute(dbs[0].get_attr("publicly_accessible"))
    assert ok is False
    assert res_val is None


def test_tfvars_overrides_default(tmp_path):
    tf_file = tmp_path / "main.tf"
    tf_file.write_text("""
variable "is_encrypted" {
  type    = bool
  default = false
}

resource "aws_ebs_volume" "vol" {
  availability_zone = "us-east-1a"
  size              = 10
  encrypted         = var.is_encrypted
}
""", encoding="utf-8")

    tfvars_file = tmp_path / "terraform.tfvars"
    tfvars_file.write_text("""
is_encrypted = true
""", encoding="utf-8")

    ctx = parse_directory(tmp_path)
    vols = ctx.get_resources_by_type("aws_ebs_volume")
    assert len(vols) == 1

    res_val, ok = ctx.resolve_attribute(vols[0].get_attr("encrypted"))
    assert ok is True
    assert res_val is True
