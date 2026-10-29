"""
CLI command line interface for tfscan.
Syntax: tfscan scan <path> --format table|json|sarif [--output <filepath>]
Exit code:
  0: Clean scan (no FAIL findings)
  1: Policy violations found (at least one FAIL finding)
  2: Command-line or runtime error
"""
import argparse
from pathlib import Path
import sys

from tfscan.engine import ScannerEngine
from tfscan.reporter import format_json, format_sarif, format_table


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="tfscan",
        description="Static security misconfiguration scanner for Terraform AWS infrastructure.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    scan_parser = subparsers.add_parser("scan", help="Scan Terraform files for security misconfigurations.")
    scan_parser.add_argument(
        "path",
        type=str,
        help="Path to a Terraform file or directory containing .tf files.",
    )
    scan_parser.add_argument(
        "--format",
        choices=["table", "json", "sarif"],
        default="table",
        help="Output serialization format (default: table).",
    )
    scan_parser.add_argument(
        "--plan",
        action="store_true",
        help="Scan a Terraform plan JSON file (from `terraform show -json`).",
    )
    scan_parser.add_argument(
        "-o",
        "--output",
        type=str,
        default=None,
        help="Optional destination file path to write output report.",
    )

    return parser


def main(argv=None) -> int:
    parser = create_parser()
    args = parser.parse_args(argv)

    if args.command == "scan":
        target = Path(args.path)
        if not target.exists():
            print(f"Error: Target path '{args.path}' does not exist.", file=sys.stderr)
            return 2

        engine = ScannerEngine()
        result = engine.scan(target, is_plan_json=args.plan)

        if args.format == "json":
            output_text = format_json(result)
        elif args.format == "sarif":
            output_text = format_sarif(result)
        else:
            output_text = format_table(result)

        if args.output:
            out_path = Path(args.output)
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_text(output_text, encoding="utf-8")
        else:
            print(output_text)

        # Gate CI pipeline: exit 1 if any FAIL finding exists
        if result.has_failures:
            return 1
        return 0

    return 0


if __name__ == "__main__":
    sys.exit(main())
