#!/usr/bin/env python3
"""Offline security regression tests for the administrator-installed delegation.

The small policy matcher deliberately supports only the operators used by this
template and fails on unknown syntax. It checks policy behavior, not AWS service
authorization, CloudFormation handler behavior, or a live GitHub OIDC exchange.
Live qualification must separately use AWS IAM simulation and actual deployment.
"""

from fnmatch import fnmatchcase
from pathlib import Path
import re
import unittest

import yaml


ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = yaml.safe_load((ROOT / "semantics/automation-bootstrap.yaml").read_text())
ACCOUNTS = {"dev": "604151511147", "prod": "334557859583"}
SUBJECT = "repo:bluecontract@93829250/blue-packages@1391542341:ref:refs/heads/main"


def items(value):
    return value if isinstance(value, list) else [value]


def rendered(environment):
    """Resolve only the intrinsic functions used in the bootstrap template."""
    values = {"EnvName": environment, "AWS::AccountId": ACCOUNTS[environment],
              "AWS::Region": "eu-west-1", "AWS::Partition": "aws"}

    def reference(name):
        if name in values:
            return values[name]
        logical_id, _, attribute = name.partition(".")
        resource = TEMPLATE["Resources"][logical_id]
        properties = resource["Properties"]
        if resource["Type"] == "AWS::IAM::ManagedPolicy" and not attribute:
            return f"arn:aws:iam::{values['AWS::AccountId']}:policy/{resolve(properties['ManagedPolicyName'])}"
        if resource["Type"] == "AWS::IAM::Role":
            role = resolve(properties["RoleName"])
            if attribute == "Arn":
                return f"arn:aws:iam::{values['AWS::AccountId']}:role/{role}"
            if not attribute:
                return role
        raise AssertionError(f"Unsupported reference: {name}")

    def resolve(value):
        if isinstance(value, list):
            return [resolve(item) for item in value]
        if not isinstance(value, dict):
            return value
        if set(value) == {"Ref"}:
            return reference(value["Ref"])
        if set(value) == {"Fn::GetAtt"}:
            return reference(".".join(value["Fn::GetAtt"]))
        if set(value) == {"Fn::Sub"}:
            return re.sub(r"\$\{([^}]+)}", lambda match: reference(match[1]), value["Fn::Sub"])
        if any(key.startswith("Fn::") for key in value):
            raise AssertionError(f"Unsupported intrinsic: {value}")
        return {key: resolve(item) for key, item in value.items()}

    return resolve(TEMPLATE)


def decision(policy, action, resource="*", context=None, principal=None):
    """Evaluate this template's IAM subset, preserving explicit/implicit denial."""
    context = context or {}
    allowed = False
    for statement in policy["Statement"]:
        unknown = set(statement) - {"Sid", "Effect", "Action", "NotAction", "Resource",
                                    "NotResource", "Condition", "Principal"}
        if unknown:
            raise AssertionError(f"Unsupported statement syntax: {unknown}")
        if ("Action" in statement) == ("NotAction" in statement):
            raise AssertionError("Exactly one Action/NotAction is required")
        action_matches = any(fnmatchcase(action.lower(), pattern.lower())
                             for pattern in items(statement.get("Action", statement.get("NotAction"))))
        if action_matches == ("NotAction" in statement):
            continue
        if "Resource" in statement and "NotResource" in statement:
            raise AssertionError("Resource and NotResource are mutually exclusive")
        if "Resource" in statement or "NotResource" in statement:
            resource_matches = any(fnmatchcase(resource, pattern)
                                   for pattern in items(statement.get("Resource", statement.get("NotResource"))))
            if resource_matches == ("NotResource" in statement):
                continue
        elif "Principal" not in statement:
            raise AssertionError("Only trust statements may omit Resource")
        if "Principal" in statement:
            if not isinstance(statement["Principal"], dict):
                raise AssertionError("Unsupported principal syntax")
            if principal not in [p for group in statement["Principal"].values() for p in items(group)]:
                continue
        matches = True
        for operator, conditions in statement.get("Condition", {}).items():
            if operator not in ("StringEquals", "ArnEquals", "StringLike"):
                raise AssertionError(f"Unsupported condition: {operator}")
            for key, expected in conditions.items():
                if key not in context:
                    matches = False
                elif operator == "StringLike":
                    matches &= any(fnmatchcase(context[key], pattern) for pattern in items(expected))
                else:
                    matches &= context[key] in items(expected)
        if not matches:
            continue
        if statement["Effect"] == "Deny":
            return "explicitDeny"
        if statement["Effect"] != "Allow":
            raise AssertionError(f"Unknown effect: {statement['Effect']}")
        allowed = True
    return "allowed" if allowed else "implicitDeny"


def role_policy(template, logical_id):
    policies = template["Resources"][logical_id]["Properties"]["Policies"]
    return {"Statement": [statement for policy in policies
                          for statement in policy["PolicyDocument"]["Statement"]]}


class BootstrapSecurityTests(unittest.TestCase):
    def setUp(self):
        self.templates = {environment: rendered(environment) for environment in ACCOUNTS}

    def test_explicit_environment_and_separate_bootstrap_resources(self):
        self.assertEqual(TEMPLATE["Parameters"]["EnvName"]["AllowedValues"], ["dev", "prod"])
        self.assertNotIn("Default", TEMPLATE["Parameters"]["EnvName"])
        self.assertEqual({resource["Type"] for resource in TEMPLATE["Resources"].values()},
                         {"AWS::IAM::Role", "AWS::IAM::ManagedPolicy"})
        for template in self.templates.values():
            for resource in template["Resources"].values():
                if resource["Type"] == "AWS::IAM::Role":
                    self.assertLessEqual(len(resource["Properties"]["RoleName"]), 64)

    def test_main_oidc_trust_rejects_branches_tags_environments_and_mutable_subject(self):
        invalid_subjects = [SUBJECT.replace("heads/main", "heads/feature"),
                            SUBJECT.replace("ref:refs/heads/main", "ref:refs/tags/v1"),
                            SUBJECT.replace("ref:refs/heads/main", "environment:semantics-infra-dev"),
                            SUBJECT.replace("ref:refs/heads/main", "pull_request"),
                            "repo:bluecontract/blue-packages:ref:refs/heads/main",
                            SUBJECT.replace("1391542341", "1391542342")]
        for environment, template in self.templates.items():
            trust = template["Resources"]["GitHubDeploymentRole"]["Properties"]["AssumeRolePolicyDocument"]
            provider = f"arn:aws:iam::{ACCOUNTS[environment]}:oidc-provider/token.actions.githubusercontent.com"
            claims = {"token.actions.githubusercontent.com:aud": "sts.amazonaws.com",
                      "token.actions.githubusercontent.com:sub": SUBJECT}
            self.assertEqual(decision(trust, "sts:AssumeRoleWithWebIdentity", context=claims,
                                      principal=provider), "allowed")
            for subject in invalid_subjects:
                with self.subTest(environment=environment, subject=subject):
                    self.assertEqual(decision(trust, "sts:AssumeRoleWithWebIdentity",
                                              context={**claims, "token.actions.githubusercontent.com:sub": subject},
                                              principal=provider), "implicitDeny")
            self.assertEqual(decision(trust, "sts:AssumeRoleWithWebIdentity", context=claims,
                                      principal=provider.replace(ACCOUNTS[environment], "000000000000")), "implicitDeny")
            self.assertEqual(decision(trust, "sts:AssumeRoleWithWebIdentity",
                                      context={**claims, "token.actions.githubusercontent.com:aud": "elsewhere"},
                                      principal=provider), "implicitDeny")

    def test_boundaries_allow_cards_and_explicitly_deny_escalation_even_with_resource_grant(self):
        for environment, template in self.templates.items():
            bucket = f"arn:aws:s3:::blue-semantic-cards-{environment}"
            other_bucket = f"arn:aws:s3:::blue-semantic-cards-{'prod' if environment == 'dev' else 'dev'}"
            for logical_id in ("ReadPermissionsBoundary", "PublishPermissionsBoundary"):
                boundary = template["Resources"][logical_id]["Properties"]["PolicyDocument"]
                for action, resource in [("s3:ListBucket", bucket), ("s3:GetObject", f"{bucket}/cards/model.json")]:
                    self.assertEqual(decision(boundary, action, resource), "allowed")
                publisher = logical_id == "PublishPermissionsBoundary"
                self.assertEqual(decision(boundary, "s3:PutObject", f"{bucket}/model.json"),
                                 "allowed" if publisher else "explicitDeny")
                denied = [("s3:DeleteObject", f"{bucket}/model.json"),
                          ("s3:DeleteObjectVersion", f"{bucket}/model.json"),
                          ("s3:PutObjectAcl", f"{bucket}/model.json"),
                          ("s3:GetObject", f"{bucket}/credentials.txt"),
                          ("s3:GetObject", f"{other_bucket}/model.json"),
                          ("s3:PutObject", f"{other_bucket}/model.json"),
                          ("s3:ListBucket", other_bucket),
                          ("iam:CreateRole", "*"), ("sts:AssumeRole", "*"),
                          ("s3:PutBucketPolicy", bucket)]
                for action, resource in denied:
                    with self.subTest(environment=environment, boundary=logical_id, action=action, resource=resource):
                        # A resource policy granting a role session can bypass an
                        # implicit boundary deny, so these must be EXPLICIT denies.
                        self.assertEqual(decision(boundary, action, resource), "explicitDeny")

    def test_app_policy_mutation_requires_the_matching_existing_boundary(self):
        for environment, template in self.templates.items():
            policy = role_policy(template, "CloudFormationExecutionRole")
            base = f"arn:aws:iam::{ACCOUNTS[environment]}:"
            for role in ("read", "publish"):
                target = f"{base}role/blue-semantic-cards-{environment}-{role}"
                boundary = f"{base}policy/blue-semantic-cards-{environment}-{role}-boundary"
                context = {"iam:PermissionsBoundary": boundary}
                for action in ("iam:CreateRole", "iam:PutRolePermissionsBoundary", "iam:PutRolePolicy", "iam:DeleteRolePolicy"):
                    with self.subTest(environment=environment, role=role, action=action):
                        self.assertEqual(decision(policy, action, target, context), "allowed")
                        for bad_context in ({}, {"iam:PermissionsBoundary": "arn:aws:iam::aws:policy/AdministratorAccess"},
                                            {"iam:PermissionsBoundary": boundary.replace(f"-{role}-boundary", "-publish-boundary" if role == "read" else "-read-boundary")}):
                            self.assertEqual(decision(policy, action, target, bad_context), "implicitDeny")
                        self.assertEqual(decision(policy, action, target + "-extra", context), "implicitDeny")
                        self.assertEqual(decision(policy, action, target.replace(ACCOUNTS[environment], "000000000000"), context), "implicitDeny")
                        self.assertEqual(decision(policy, action, target.replace(f"-{environment}-", "-prod-" if environment == "dev" else "-dev-"), context), "implicitDeny")
                self.assertEqual(decision(policy, "iam:DeleteRolePermissionsBoundary", target, context), "explicitDeny")
                self.assertEqual(decision(policy, "iam:AttachRolePolicy", target, context), "implicitDeny")

    def test_execution_role_cannot_mutate_bootstrap_or_manage_other_resources(self):
        for environment, template in self.templates.items():
            policy = role_policy(template, "CloudFormationExecutionRole")
            prefix = f"arn:aws:iam::{ACCOUNTS[environment]}:"
            for suffix in ("cloudformation", "github-deploy"):
                protected = f"{prefix}role/blue-semantic-cards-{environment}-{suffix}"
                for action in ("iam:PutRolePolicy", "iam:UpdateAssumeRolePolicy", "iam:CreateRole",
                               "iam:DeleteRole", "iam:PassRole", "iam:PutRolePermissionsBoundary"):
                    for role in ("read", "publish"):
                        context = {"iam:PermissionsBoundary": f"{prefix}policy/blue-semantic-cards-{environment}-{role}-boundary"}
                        self.assertEqual(decision(policy, action, protected, context), "implicitDeny")
            for role in ("read", "publish"):
                boundary = f"{prefix}policy/blue-semantic-cards-{environment}-{role}-boundary"
                for action in ("iam:CreatePolicyVersion", "iam:SetDefaultPolicyVersion", "iam:DeletePolicyVersion",
                               "iam:DeletePolicy", "iam:CreatePolicy"):
                    self.assertEqual(decision(policy, action, boundary), "implicitDeny")
            provider = f"{prefix}oidc-provider/token.actions.githubusercontent.com"
            for action in ("iam:CreateOpenIDConnectProvider", "iam:DeleteOpenIDConnectProvider", "iam:UpdateOpenIDConnectProviderThumbprint"):
                self.assertEqual(decision(policy, action, provider), "implicitDeny")
            bucket = f"arn:aws:s3:::blue-semantic-cards-{environment}"
            for action in ("s3:CreateBucket", "s3:PutBucketPolicy", "s3:PutBucketPublicAccessBlock", "s3:PutBucketVersioning"):
                self.assertEqual(decision(policy, action, bucket), "allowed")
                self.assertEqual(decision(policy, action, bucket + "-unrelated"), "implicitDeny")
            for action in ("s3:GetObject", "s3:PutObject", "s3:DeleteObject"):
                self.assertEqual(decision(policy, action, bucket + "/model.json"), "implicitDeny")
            for action in ("s3:DeleteBucket", "s3:PutLifecycleConfiguration", "cloudformation:CreateStack", "lambda:CreateFunction"):
                self.assertEqual(decision(policy, action, bucket), "implicitDeny")

    def test_deploy_create_changeset_requires_exact_stack_region_account_and_role(self):
        for environment, template in self.templates.items():
            policy = role_policy(template, "GitHubDeploymentRole")
            account = ACCOUNTS[environment]
            stack = f"arn:aws:cloudformation:eu-west-1:{account}:stack/blue-semantic-cards-{environment}/stack-id"
            execution_role = f"arn:aws:iam::{account}:role/blue-semantic-cards-{environment}-cloudformation"
            context = {"cloudformation:RoleArn": execution_role,
                       "cloudformation:ChangeSetName": "awscli-cloudformation-package-deploy-1234567890"}
            self.assertEqual(decision(policy, "cloudformation:CreateChangeSet", stack, context), "allowed")
            invalid_resources = [stack.replace("eu-west-1", "us-east-1"), stack.replace(account, "000000000000"),
                                 stack.replace(f"-{environment}/", "-other/"), stack.replace(f"-{environment}/", f"-{environment}-bootstrap/")]
            for resource in invalid_resources:
                self.assertEqual(decision(policy, "cloudformation:CreateChangeSet", resource, context), "implicitDeny")
            for bad_context in ({}, {"cloudformation:ChangeSetName": context["cloudformation:ChangeSetName"]},
                                {**context, "cloudformation:RoleArn": execution_role + "-other"},
                                {**context, "cloudformation:ChangeSetName": "unrelated-change-set"}):
                self.assertEqual(decision(policy, "cloudformation:CreateChangeSet", stack, bad_context), "implicitDeny")
            for action in ("cloudformation:DescribeStacks", "cloudformation:GetTemplateSummary", "cloudformation:DescribeStackEvents",
                           "cloudformation:TagResource", "cloudformation:UntagResource"):
                self.assertEqual(decision(policy, action, stack), "allowed")
                for resource in invalid_resources:
                    self.assertEqual(decision(policy, action, resource), "implicitDeny")
            self.assertEqual(decision(policy, "cloudformation:DeleteStack", stack), "implicitDeny")

    def test_cli_changeset_name_and_arn_are_scoped_to_the_target_stack(self):
        for environment, template in self.templates.items():
            policy = role_policy(template, "GitHubDeploymentRole")
            account = ACCOUNTS[environment]
            stack = f"arn:aws:cloudformation:eu-west-1:{account}:stack/blue-semantic-cards-{environment}/stack-id"
            name = "awscli-cloudformation-package-deploy-1234567890"
            arn = f"arn:aws:cloudformation:eu-west-1:{account}:changeSet/{name}/change-set-id"
            for action in ("cloudformation:DescribeChangeSet", "cloudformation:ExecuteChangeSet", "cloudformation:DeleteChangeSet"):
                for change_set in (name, arn):
                    context = {"cloudformation:ChangeSetName": change_set}
                    # These APIs do not provide cloudformation:RoleArn.
                    self.assertEqual(decision(policy, action, stack, context), "allowed")
                    self.assertEqual(decision(policy, action, stack.replace(f"-{environment}/", "-unrelated/"), context), "implicitDeny")
                    self.assertEqual(decision(policy, action, arn, context), "implicitDeny")
                self.assertEqual(decision(policy, action, stack, {"cloudformation:ChangeSetName": "other"}), "implicitDeny")
                self.assertEqual(decision(policy, action, stack, {"cloudformation:ChangeSetName": arn.replace(account, "000000000000")}), "implicitDeny")

    def test_deployment_role_can_only_pass_the_execution_role_to_cloudformation(self):
        for environment, template in self.templates.items():
            policy = role_policy(template, "GitHubDeploymentRole")
            execution_role = f"arn:aws:iam::{ACCOUNTS[environment]}:role/blue-semantic-cards-{environment}-cloudformation"
            context = {"iam:PassedToService": "cloudformation.amazonaws.com"}
            self.assertEqual(decision(policy, "iam:PassRole", execution_role, context), "allowed")
            self.assertEqual(decision(policy, "iam:PassRole", execution_role), "implicitDeny")
            self.assertEqual(decision(policy, "iam:PassRole", execution_role, {"iam:PassedToService": "lambda.amazonaws.com"}), "implicitDeny")
            for suffix in ("-other", "-read", "-publish"):
                self.assertEqual(decision(policy, "iam:PassRole", execution_role + suffix, context), "implicitDeny")
            for action in ("iam:PutRolePolicy", "iam:CreateRole", "iam:UpdateAssumeRolePolicy", "iam:CreateOpenIDConnectProvider", "s3:PutBucketPolicy"):
                for resource in ("*", execution_role, execution_role.replace("-cloudformation", "-read"),
                                 f"arn:aws:s3:::blue-semantic-cards-{environment}"):
                    self.assertEqual(decision(policy, action, resource), "implicitDeny")


if __name__ == "__main__":
    unittest.main()
