"""
Cross-platform utility to fetch TerraGoat at pinned commit hash.
"""
import os
import subprocess
import sys
from pathlib import Path

PINNED_COMMIT = "729f8da62c6a85ce4af5ad3d123de97776d954c4"
REPO_URL = "https://github.com/bridgecrewio/terragoat.git"


def fetch_terragoat(target_dir: Path | None = None) -> Path:
    if target_dir is None:
        target_dir = Path(__file__).resolve().parent.parent / "data" / "terragoat"

    target_dir.parent.mkdir(parents=True, exist_ok=True)

    if (target_dir / ".git").is_dir():
        print(f"TerraGoat already exists at {target_dir}. Checking out pinned commit...")
        subprocess.run(["git", "fetch", "--all"], cwd=str(target_dir), check=True)
        subprocess.run(["git", "checkout", "-q", PINNED_COMMIT], cwd=str(target_dir), check=True)
    else:
        print(f"Cloning TerraGoat into {target_dir}...")
        subprocess.run(["git", "clone", REPO_URL, str(target_dir)], check=True)
        subprocess.run(["git", "checkout", "-q", PINNED_COMMIT], cwd=str(target_dir), check=True)

    # Verify commit
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=str(target_dir), capture_output=True, text=True, check=True
    )
    current_head = result.stdout.strip()
    print(f"Verified TerraGoat pinned commit HEAD: {current_head}")
    if not current_head.startswith(PINNED_COMMIT[:12]):
        raise RuntimeError(f"Commit mismatch! Expected {PINNED_COMMIT}, got {current_head}")

    aws_dir = target_dir / "terraform" / "aws"
    if not aws_dir.is_dir():
        raise FileNotFoundError(f"Terraform AWS folder not found at {aws_dir}")

    print(f"TerraGoat AWS folder verified at: {aws_dir}")
    return aws_dir


if __name__ == "__main__":
    fetch_terragoat()
