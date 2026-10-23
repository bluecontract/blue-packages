#!/usr/bin/env python3
"""Small AWS CLI adapter for the existing semantic-card CloudFormation template.

No credentials are persisted. This does not replace CloudFormation's deployment
engine, configure publication, create models, or delete card objects.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
TARGETS = {"dev": "604151511147", "prod": "334557859583"}


def configuration(environment: str) -> dict:
    if environment not in TARGETS:
        raise ValueError("environment must be dev or prod")
    config = json.loads((ROOT / "semantics/environments" / f"{environment}.json").read_text())
    account = TARGETS[environment]
    prefix = f"blue-semantic-cards-{environment}"
    expected = {
        "environment": environment,
        "account_id": account,
        "region": "eu-west-1",
        "stack_name": prefix,
        "deployment_role_arn": f"arn:aws:iam::{account}:role/{prefix}-github-deploy",
        "cloudformation_role_arn": f"arn:aws:iam::{account}:role/{prefix}-cloudformation",
        "read_boundary_arn": f"arn:aws:iam::{account}:policy/{prefix}-read-boundary",
        "publish_boundary_arn": f"arn:aws:iam::{account}:policy/{prefix}-publish-boundary",
    }
    if config != expected:
        raise ValueError("environment configuration does not match the reviewed account/resource mapping")
    return config


def aws(config: dict, *arguments: str) -> list[str]:
    return ["aws", *arguments, "--region", config["region"], "--no-cli-pager"]


def aws_json(config: dict, *arguments: str) -> dict:
    result = subprocess.run(aws(config, *arguments, "--output", "json"),
                            check=True, stdout=subprocess.PIPE, text=True)
    return json.loads(result.stdout)


def deploy(config: dict, output: Path) -> dict:
    output.mkdir(parents=True, exist_ok=True)
    receipt_path = output / "receipt.json"
    # A fresh output prevents a failed run from being mistaken for an old success.
    if receipt_path.exists():
        raise ValueError(f"receipt already exists: choose a fresh output directory ({output})")
    template = ROOT / "semantics/template.yaml"
    receipt = {
        "schema_version": 1,
        "environment": config["environment"],
        "account_id": config["account_id"],
        "region": config["region"],
        "stack_name": config["stack_name"],
        "cloudformation_role_arn": config["cloudformation_role_arn"],
        "template_sha256": hashlib.sha256(template.read_bytes()).hexdigest(),
        "source_sha": os.environ.get("GITHUB_SHA", "local"),
        "started_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "result": "RUNNING",
    }
    receipt_path.write_text(json.dumps(receipt, indent=2) + "\n")
    try:
        identity = aws_json(config, "sts", "get-caller-identity")
        if identity["Account"] != config["account_id"]:
            raise ValueError("AWS caller account differs from the explicitly selected environment")
        receipt["caller_arn"] = identity["Arn"]
        subprocess.run(aws(config, "cloudformation", "deploy",
                           "--template-file", str(template),
                           "--stack-name", config["stack_name"],
                           "--role-arn", config["cloudformation_role_arn"],
                           "--parameter-overrides",
                           f"EnvName={config['environment']}",
                           "CreateGitHubOIDCProvider=false",
                           f"ReadRolePermissionsBoundaryArn={config['read_boundary_arn']}",
                           f"PublishRolePermissionsBoundaryArn={config['publish_boundary_arn']}",
                           "--capabilities", "CAPABILITY_NAMED_IAM",
                           "--no-fail-on-empty-changeset"), check=True)
        response = aws_json(config, "cloudformation", "describe-stacks",
                            "--stack-name", config["stack_name"])
        stack, = response["Stacks"]
        if stack["StackStatus"] not in ("CREATE_COMPLETE", "UPDATE_COMPLETE"):
            raise ValueError(f"stack is not successfully deployed: {stack['StackStatus']}")
        if stack.get("RoleARN") != config["cloudformation_role_arn"]:
            raise ValueError("stack is not attached to the expected scoped execution role")
        values = {item["OutputKey"]: item["OutputValue"] for item in stack.get("Outputs", [])}
        if values.get("BucketName") != config["stack_name"]:
            raise ValueError("unexpected or missing semantic bucket output")
        receipt.update(result="PASS", stack_status=stack["StackStatus"],
                       stack_id=stack["StackId"], outputs=values)
        (output / "github-variables.txt").write_text(values["GitHubVariables"])
    except Exception as exc:
        # Messages come from local checks/CLI, never a credential-bearing command.
        receipt.update(result="FAIL", error_type=type(exc).__name__, error=str(exc))
        raise
    finally:
        receipt["finished_at_utc"] = dt.datetime.now(dt.timezone.utc).isoformat()
        receipt_path.write_text(json.dumps(receipt, indent=2) + "\n")
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("config", "deploy"):
        command = sub.add_parser(name)
        command.add_argument("--environment", choices=tuple(TARGETS), required=True)
        if name == "config":
            command.add_argument("--github-output", type=Path)
        else:
            command.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        config = configuration(args.environment)
        if args.command == "config":
            if args.github_output:
                with args.github_output.open("a") as f:
                    for name, value in config.items():
                        f.write(f"{name}={value}\n")
            else:
                print(json.dumps(config, indent=2))
        else:
            print(json.dumps(deploy(config, args.output), indent=2))
        return 0
    except (ValueError, KeyError, OSError, subprocess.SubprocessError) as exc:
        print(f"Semantic infrastructure deployment failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
