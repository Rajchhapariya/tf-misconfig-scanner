"""
Parser module for tfscan using python-hcl2.
Parses Terraform .tf and .tfvars files into normalized Resource models and a ScanContext.
Resolves variable default values and .tfvars assignments.
Flags unresolvable expressions (module outputs, data sources, missing vars) as unresolved.
"""
from dataclasses import dataclass, field
from pathlib import Path
import re
from typing import Any, Dict, List, Optional, Set, Tuple

import hcl2

from tfscan.models import Resource


@dataclass
class ScanContext:
    target_path: Path
    files: List[Path] = field(default_factory=list)
    resources: Dict[str, List[Resource]] = field(default_factory=dict)
    all_resources_by_address: Dict[str, Resource] = field(default_factory=dict)
    providers: List[Resource] = field(default_factory=list)
    variables: Dict[str, Any] = field(default_factory=dict)
    variable_defaults: Dict[str, Any] = field(default_factory=dict)
    locals: Dict[str, Any] = field(default_factory=dict)
    declared_vars: Set[str] = field(default_factory=set)

    def get_resources_by_type(self, resource_type: str) -> List[Resource]:
        return self.resources.get(resource_type, [])

    def resolve_attribute(self, raw_val: Any) -> Tuple[Any, bool]:
        """
        Resolves an attribute value.
        Returns (resolved_value, is_resolved).
        If is_resolved is False, the value cannot be statically determined.
        """
        return resolve_value(raw_val, self)

    def find_linked_s3_resources(self, bucket: Resource) -> Dict[str, List[Resource]]:
        """
        Locates separate v4+ S3 resources linked to this bucket:
        - aws_s3_bucket_public_access_block
        - aws_s3_bucket_acl
        - aws_s3_bucket_server_side_encryption_configuration
        Matches via:
          - aws_s3_bucket.<name>.id
          - aws_s3_bucket.<name>.bucket
          - exact bucket string literal name
        """
        linked: Dict[str, List[Resource]] = {
            "aws_s3_bucket_public_access_block": [],
            "aws_s3_bucket_acl": [],
            "aws_s3_bucket_server_side_encryption_configuration": [],
        }

        bucket_name_raw = bucket.get_attr("bucket")
        resolved_bucket_name, _ = self.resolve_attribute(bucket_name_raw)

        candidate_refs = {
            f"aws_s3_bucket.{bucket.resource_name}.id",
            f"aws_s3_bucket.{bucket.resource_name}.bucket",
            f"${{aws_s3_bucket.{bucket.resource_name}.id}}",
            f"${{aws_s3_bucket.{bucket.resource_name}.bucket}}",
            f"aws_s3_bucket.{bucket.resource_name}",
            bucket.resource_name,
        }
        if resolved_bucket_name:
            candidate_refs.add(str(resolved_bucket_name))
        if isinstance(bucket_name_raw, str):
            candidate_refs.add(bucket_name_raw)

        for target_type in linked.keys():
            for res in self.get_resources_by_type(target_type):
                target_bucket_val = res.get_attr("bucket")
                if target_bucket_val is None:
                    continue

                if isinstance(target_bucket_val, list) and len(target_bucket_val) == 1:
                    target_bucket_val = target_bucket_val[0]

                target_str = str(target_bucket_val).strip()
                # Check for reference matches
                if (
                    target_str in candidate_refs
                    or any(c in target_str for c in candidate_refs if len(c) > 3)
                ):
                    linked[target_type].append(res)
                else:
                    # Check if target_bucket_val resolves to the same bucket name
                    res_val, is_res = self.resolve_attribute(target_bucket_val)
                    if is_res and res_val and resolved_bucket_name and res_val == resolved_bucket_name:
                        linked[target_type].append(res)

        return linked


def unwrap_list_if_single(val: Any) -> Any:
    if isinstance(val, list) and len(val) == 1:
        return val[0]
    return val


def resolve_value(val: Any, context: ScanContext) -> Tuple[Any, bool]:
    """
    Recursively resolves expressions and variable references.
    Returns (resolved_value, True) if fully resolved.
    Returns (None, False) if any part is dynamic/unresolvable.
    """
    if val is None:
        return None, True

    if isinstance(val, bool) or isinstance(val, (int, float)):
        return val, True

    if isinstance(val, list):
        if len(val) == 1 and not isinstance(val[0], (list, dict)):
            # Check if this single item is a wrapped scalar
            return resolve_value(val[0], context)
        resolved_items = []
        for item in val:
            res_item, ok = resolve_value(item, context)
            if not ok:
                return None, False
            resolved_items.append(res_item)
        return resolved_items, True

    if isinstance(val, dict):
        resolved_dict = {}
        for k, v in val.items():
            if k.startswith("__"):  # e.g. __start_line__
                continue
            res_v, ok = resolve_value(v, context)
            if not ok:
                return None, False
            resolved_dict[k] = res_v
        return resolved_dict, True

    if isinstance(val, str):
        val_clean = val.strip()

        # Handle jsonencode(...) function calls parsed by python-hcl2
        if (val_clean.startswith("${jsonencode(") and val_clean.endswith(")}")) or (
            val_clean.startswith("jsonencode(") and val_clean.endswith(")")
        ):
            if val_clean.startswith("${"):
                inner = val_clean[len("${jsonencode(") : -len(")}")]
            else:
                inner = val_clean[len("jsonencode(") : -len(")")]
            try:
                import ast
                evaluated = ast.literal_eval(inner)
                return resolve_value(evaluated, context)
            except Exception:
                return None, False

        # Pure unresolvable indicators
        unresolvable_patterns = [
            r"data\.[a-zA-Z0-9_\-\.]+",
            r"module\.[a-zA-Z0-9_\-\.]+",
            r"null_resource\.",
            r"remote_state",
            r"\$\{.*\(.*\) concurred\}",
        ]
        for pat in unresolvable_patterns:
            if re.search(pat, val_clean):
                return None, False

        # Variable reference: var.name or ${var.name}
        var_match = re.match(r"^\$\{var\.([a-zA-Z0-9_\-]+)\}$", val_clean) or re.match(
            r"^var\.([a-zA-Z0-9_\-]+)$", val_clean
        )
        if var_match:
            var_name = var_match.group(1)
            if var_name in context.variables:
                return resolve_value(context.variables[var_name], context)
            return None, False

        # Local reference: local.name or ${local.name}
        local_match = re.match(r"^\$\{local\.([a-zA-Z0-9_\-]+)\}$", val_clean) or re.match(
            r"^local\.([a-zA-Z0-9_\-]+)$", val_clean
        )
        if local_match:
            loc_name = local_match.group(1)
            if loc_name in context.locals:
                return resolve_value(context.locals[loc_name], context)
            return None, False

        # String containing unresolvable ${...} interpolation
        if "${" in val_clean:
            # Check if it's interpolating variables
            interpolations = re.findall(r"\$\{([^}]+)\}", val_clean)
            for item in interpolations:
                item = item.strip()
                if item.startswith("var."):
                    var_name = item.split("var.", 1)[1]
                    if var_name not in context.variables:
                        return None, False
                elif item.startswith("local."):
                    loc_name = item.split("local.", 1)[1]
                    if loc_name not in context.locals:
                        return None, False
                else:
                    return None, False

            # If all sub-variables are resolvable, perform substitution
            resolved_str = val_clean
            for item in interpolations:
                item_strip = item.strip()
                if item_strip.startswith("var."):
                    vname = item_strip.split("var.", 1)[1]
                    sub_val, ok = resolve_value(context.variables[vname], context)
                    if not ok:
                        return None, False
                    resolved_str = resolved_str.replace(f"${{{item}}}", str(sub_val))
                elif item_strip.startswith("local."):
                    lname = item_strip.split("local.", 1)[1]
                    sub_val, ok = resolve_value(context.locals[lname], context)
                    if not ok:
                        return None, False
                    resolved_str = resolved_str.replace(f"${{{item}}}", str(sub_val))
            return resolved_str, True

        return val_clean, True

    return val, True


def parse_directory(target_path: Path) -> ScanContext:
    """
    Parses all .tf and .tfvars files in the target directory or single file.
    """
    target = target_path.resolve()
    context = ScanContext(target_path=target)

    if target.is_file():
        if target.suffix == ".tf":
            context.files = [target]
        base_dir = target.parent
    else:
        context.files = sorted(list(target.rglob("*.tf")))
        base_dir = target

    # 1. Parse .tfvars files first
    tfvars_files = sorted(list(base_dir.glob("*.tfvars")) + list(base_dir.glob("*.auto.tfvars")))
    for tv_file in tfvars_files:
        try:
            with open(tv_file, "r", encoding="utf-8", errors="ignore") as f:
                parsed_vars = hcl2.load(f)
                for k, v in parsed_vars.items():
                    context.variables[k] = unwrap_list_if_single(v)
        except Exception:
            pass

    # 2. First pass: extract variable blocks and defaults, locals, and providers
    for tf_file in context.files:
        try:
            with open(tf_file, "r", encoding="utf-8", errors="ignore") as f:
                parsed = hcl2.load(f)

            # Variables
            for var_dict in parsed.get("variable", []):
                for var_name, var_body in var_dict.items():
                    context.declared_vars.add(var_name)
                    if "default" in var_body:
                        default_val = unwrap_list_if_single(var_body["default"])
                        context.variable_defaults[var_name] = default_val
                        if var_name not in context.variables:
                            context.variables[var_name] = default_val

            # Locals
            for loc_dict in parsed.get("locals", []):
                for loc_name, loc_val in loc_dict.items():
                    context.locals[loc_name] = unwrap_list_if_single(loc_val)

            # Providers
            for prov_dict in parsed.get("provider", []):
                for prov_name, prov_body in prov_dict.items():
                    alias = prov_body.get("alias")
                    if isinstance(alias, list) and alias:
                        alias = alias[0]
                    res_name = f"{prov_name}.{alias}" if alias else prov_name
                    line = prov_body.get("__start_line__", 1)
                    attrs = {k: unwrap_list_if_single(v) for k, v in prov_body.items() if not k.startswith("__")}
                    prov_res = Resource(
                        file_path=tf_file,
                        line_number=line,
                        resource_type=f"provider.{prov_name}",
                        resource_name=res_name,
                        address=f"provider.{res_name}",
                        attributes=attrs,
                        raw_block=prov_body,
                    )
                    context.providers.append(prov_res)

        except Exception:
            pass

    # 3. Second pass: extract all resources
    for tf_file in context.files:
        try:
            with open(tf_file, "r", encoding="utf-8", errors="ignore") as f:
                parsed = hcl2.load(f)

            for res_entry in parsed.get("resource", []):
                for rtype, rinstances in res_entry.items():
                    if not isinstance(rinstances, dict):
                        continue
                    for rname, rbody in rinstances.items():
                        if not isinstance(rbody, dict):
                            continue
                        line = rbody.get("__start_line__", 1)
                        attrs = {}
                        for k, v in rbody.items():
                            if k.startswith("__"):
                                continue
                            attrs[k] = unwrap_list_if_single(v)

                        address = f"{rtype}.{rname}"
                        res = Resource(
                            file_path=tf_file,
                            line_number=line,
                            resource_type=rtype,
                            resource_name=rname,
                            address=address,
                            attributes=attrs,
                            raw_block=rbody,
                        )
                        if rtype not in context.resources:
                            context.resources[rtype] = []
                        context.resources[rtype].append(res)
                        context.all_resources_by_address[address] = res
        except Exception:
            pass

    return context
