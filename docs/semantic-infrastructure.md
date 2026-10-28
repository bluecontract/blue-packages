# Semantic card infrastructure deployment

One manual workflow, **Deploy semantic cards infrastructure**, creates or updates
the existing `semantics/template.yaml` stack. Select `dev` or `prod`; the account,
region and role ARNs come from reviewed files in `semantics/environments/`.
The workflow uses GitHub OIDC, not stored AWS access keys.

| Target | AWS account | Region | Application stack and bucket |
| --- | --- | --- | --- |
| DEV | `604151511147` | `eu-west-1` | `blue-semantic-cards-dev` |
| PROD | `334557859583` | `eu-west-1` | `blue-semantic-cards-prod` |

The AWS deployment role trusts only the immutable subject
`repo:bluecontract@93829250/blue-packages@1391542341:ref:refs/heads/main`
and audience `sts.amazonaws.com`. Feature branches, pull requests and other
repositories cannot assume it. Both targets are manual; no new GitHub environment
or approval rule is required. Repository access to main remains the code-review
and authorization boundary. The workflow independently checks `github.ref`.

## One-time administrator bootstrap

The existing account-wide GitHub OIDC provider is reused. The bootstrap does not
create or modify it. Verify its audience includes `sts.amazonaws.com` first.

An AWS administrator deploys `semantics/automation-bootstrap.yaml` once per account.
This creates only the deployment role, scoped CloudFormation execution role and
two permissions boundaries. It does not create card content or enable generation.

```sh
aws sts get-caller-identity --profile blue-dev-admin
aws cloudformation deploy --profile blue-dev-admin --region eu-west-1 \
  --stack-name blue-semantic-cards-dev-automation \
  --template-file semantics/automation-bootstrap.yaml \
  --parameter-overrides EnvName=dev \
  --capabilities CAPABILITY_NAMED_IAM --no-fail-on-empty-changeset

aws sts get-caller-identity --profile blue-prod-admin
aws cloudformation deploy --profile blue-prod-admin --region eu-west-1 \
  --stack-name blue-semantic-cards-prod-automation \
  --template-file semantics/automation-bootstrap.yaml \
  --parameter-overrides EnvName=prod \
  --capabilities CAPABILITY_NAMED_IAM --no-fail-on-empty-changeset
```

The routine GitHub role cannot modify this bootstrap stack, its roles or the
boundaries. Those remain administrator-owned. The routine role can pass only its
exact execution role, and only to CloudFormation. The execution role can manage
only the selected card bucket and the two named read/publish roles. It cannot
deploy Core, Business, compute, databases, nested stacks or change the OIDC provider.

`DescribeChangeSet` is a read-only grant on the selected application stack ARN,
including its exact account, region and stack name. It does not require a
`cloudformation:ChangeSetName` IAM context value, so the CLI waiter can read that
stack's change sets even when this context is absent. This also permits reading
administrator-created change sets on that same stack. Create, execute and delete
remain restricted to CLI-generated change-set names; creating a change set still
requires the exact execution role, and `PassRole` remains unchanged. Other stacks,
including the automation stack, receive no additional access. Updating this grant
requires an administrator to update the bootstrap stack; the routine workflow
cannot grant itself permissions.

Each application role must carry its corresponding boundary. The read boundary
allows bucket listing and JSON reads; the publish boundary also allows JSON writes.
Explicit denies exclude other actions and resources. The execution role cannot
remove or broaden those boundaries. It does administer the selected bucket's
access policy; this is intentionally an infrastructure-administration role for
that bucket, not merely a publisher. Bucket versioning, encryption, HTTPS and
retained data are configured by the application template. DEV permits public
JSON reads with browser CORS; PROD remains private.

The optional boundary parameters preserve the previous administrator-driven
template interface. They are mandatory when deploying through the delegated
execution role; omitted or different boundaries are denied by AWS IAM.

## Routine operation

The workflow must first exist on `main` for manual dispatch. From Actions, choose
**Deploy semantic cards infrastructure → Run workflow → main → dev or prod**.
Equivalent CLI:

```sh
gh workflow run semantic-cards-infrastructure.yml --ref main -f environment=dev
gh workflow run semantic-cards-infrastructure.yml --ref main -f environment=prod
```

Only the selected environment is deployed. Runs for the same environment are
serialized and do not cancel an in-progress deployment. CloudFormation performs
the actual update and rollback; there is no additional deployment state engine.
An unchanged template is a successful no-op. The adapter verifies the actual AWS
account before mutation, then requires a completed stack with the expected
execution role and bucket before writing a successful receipt.

For administrator-led bootstrap or recovery, the same adapter can be used locally:

```sh
AWS_PROFILE=blue-dev-admin python3 tools/semantic_infrastructure.py deploy \
  --environment dev --output build/semantic-infrastructure/dev-first
```

Choose a fresh output directory for each invocation. Receipts contain environment,
account, stack, execution-role ARN, template hash, source SHA, timestamps and result.
No access keys or tokens are recorded. A failed command returns a nonzero exit
status and retains a `FAIL` receipt when execution reached the deployment stage.

## Infrastructure is separate from generation and publication

The workflow publishes its receipt and five non-secret configuration values as a
per-environment artifact. It **does not overwrite** repository-wide `SEMANTICS_*`
variables: doing so would silently switch the existing publication pipeline to
whichever infrastructure target was deployed last.

The current generation/publication workflows still select one configured bucket
and use the existing `semantics-publish` environment. Follow
[semantic card automation](semantic-cards.md#enable-automation) to configure that
chosen target and its environment protections. The infrastructure role is distinct
from the read role and publish role. AWS access is through OIDC; `OPENAI_API_KEY`
is only needed for model generation, which this workflow never runs.

## Public DEV card access

The application template makes only DEV JSON cards publicly readable over HTTPS.
PROD keeps all four Block Public Access settings enabled and has no anonymous
read grant or browser CORS rule. The existing generation and publication roles
and their permissions boundaries are unchanged. ACLs remain disabled in both
environments; public access comes from the DEV bucket policy.

Setting `public-read` during upload is not supported: `BucketOwnerEnforced`
disables ACLs, and the publisher's boundary denies `s3:PutObjectAcl`. The bucket
policy covers existing and future cards without changing the upload code.
See [AWS Object Ownership](https://docs.aws.amazon.com/AmazonS3/latest/userguide/about-object-ownership.html).

After merge, for an already bootstrapped DEV account, an administrator must first update
`blue-semantic-cards-dev-automation` using the bootstrap command above. This adds
`s3:GetBucketCORS` and `s3:PutBucketCORS` to the existing CloudFormation execution
role, scoped to its card bucket. No new role is needed. The GitHub deployment
workflow cannot update that administrator-owned stack itself.

Then run **Deploy semantic cards infrastructure → main → dev**.
Generation and publication do not need to run again: existing
JSON objects become readable under the updated bucket policy.

Account/organization Block Public Access settings take precedence over the bucket
configuration. If they block public policies, the account administrator must
review the delivery approach before deployment. This PR does not change those
settings. See [AWS Block Public Access](https://docs.aws.amazon.com/AmazonS3/latest/userguide/access-control-block-public-access.html).

After deployment, verify a published card without AWS credentials:

```sh
curl --fail --include \
  -H 'Origin: http://localhost:3000' \
  'https://blue-semantic-cards-dev.s3.eu-west-1.amazonaws.com/GGJkb1eT3fsELNGUzujUXohSKN2ZzhFAMf3kbGHNAu1S.json'
```

Expect HTTP 200, the matching `blueId` and `semanticText`,
`Access-Control-Allow-Origin: *`, and `ETag` in `Access-Control-Expose-Headers`.
Browser reads may use any local port. To verify conditional-read preflight:

```sh
curl --fail --include --request OPTIONS \
  -H 'Origin: http://localhost:3000' \
  -H 'Access-Control-Request-Method: GET' \
  -H 'Access-Control-Request-Headers: If-None-Match' \
  'https://blue-semantic-cards-dev.s3.eu-west-1.amazonaws.com/GGJkb1eT3fsELNGUzujUXohSKN2ZzhFAMf3kbGHNAu1S.json'
```

Expect HTTP 200 with the requested method/header allowed. This CORS configuration
supports public reads from browsers; it grants no object writes or bucket listing.
See [AWS CORS configuration](https://docs.aws.amazon.com/AWSCloudFormation/latest/TemplateReference/aws-properties-s3-bucket-corsrule.html).

## Validation

```sh
python -m unittest discover -s tools -p 'test_semantic*.py' -v
cfn-lint semantics/template.yaml semantics/automation-bootstrap.yaml
```

The local tests exercise account mismatch, failure receipts, IAM grant boundaries
and denied escalation/cross-environment cases. They do not prove GitHub OIDC token
exchange. A real main-branch run is required for that final end-to-end check.

References: [AWS service roles](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/using-iam-servicerole.html),
[permissions boundaries](https://docs.aws.amazon.com/IAM/latest/UserGuide/access_policies_boundaries.html),
[GitHub manual dispatch](https://docs.github.com/en/actions/how-tos/manage-workflow-runs/manually-run-a-workflow).
