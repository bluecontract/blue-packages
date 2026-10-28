# Public semantic cards

`blue-packages` owns public type descriptions. Cards are reviewable JSON files in
`semantics/cards/<typeBlueId>.json` and are delivered independently through S3.
Neither Core nor Business is a build dependency or a delivery API. Package
archives and their BlueIds do not include these separately correctable artifacts.

The decision is always by **exact type BlueId**, not package version, filename,
alias or commit:

1. A valid card in the repo is ready. Reuse it even if S3 has never received it.
2. Otherwise, restore the exact published S3 card into the proposed commit.
3. Only an identity missing from both places gets a model request.
4. Publish committed cards separately. Uploading a missing object never calls a model.

Changing a README, package version, generator or prompt does not regenerate an
existing card. A new type BlueId does. Invalid cards fail validation rather than
being silently replaced. Generated prose still needs review.

## Card content

The generated response, committed file and S3 object have the same two fields:

```json
{
  "blueId": "<exact type BlueId>",
  "semanticText": "# Type name\n\nWhat this type means and does."
}
```

See [Hello Clause](../semantics/cards/6djSCK7TuFMBty51HWymVGRpnBdYTyFGf944FWZFYG4D.json)
for a concrete card.

`blueId` selects the exact type definition. `semanticText` explains its meaning
in English Markdown for both UI generation and agents discussing documents,
including consumers reached through MCP. It starts with the type name and covers
only applicable information:

- Purpose, parameters, bindings and source-defined defaults explain what is
  configured and how configuration changes behavior.
- Triggers, actors, guards, effects and rejections explain what can happen and
  distinguish an attempted operation from a confirmed outcome.
- State sources, units and absence semantics explain how to interpret document
  data without inventing values or treating missing state as a default.
- Material constraints and non-guarantees prevent claims the type does not support.

There is no mandatory section list or minimum prose length. A simple type may
need only a short explanation; headings help organize complex types. State and
limitations sections are unnecessary when there is nothing relevant to explain.
Cards contain shared type semantics, not screen layouts, UI components,
Terms-writing instructions or conversation style. Current values and permissions
still come from authorized document data, not the card.

Do not add `metadata`, dependency BlueId lists, hashes, package versions, model
details or review/validation envelopes to cards. Bounded source definitions,
dependencies and checksums remain in ignored generation requests for grounding
and source checks. The prompt version remains in `semantics/generator.json`.
Validation checks the two-field shape, exact identity and size; it does not prove
that the prose correctly describes execution. Review the meaning against sources.

## Discovery

Every check reads `PACKAGES.json`, verifies the selected archives using the existing
release tooling and inspects their exact `package-records.json` definitions. It
finds all exported descendants of `Clauses/Clause`, exported types with `clauses`
(including inherited declarations), and exported helpers referenced by executable
definitions, child templates or instruction clauses. `PUBLIC-CLAUSES.json` is not
the discovery source; it is only an additional coverage assertion in tests.

To add a clause, declare its export in `blue-package.yaml`, build its package and
affected dependants, and refresh the package catalogues as usual. The next PR
check discovers its final BlueId automatically. An added export without a matching
built export fails with `Unbuilt exports ...; rebuild the package`. A `.blue` file
which has not been exported/built has no published identity to describe. This
pipeline does not rebuild packages or prove that authored sources match a build;
the normal package build and qualification checks still apply.

On the initial implementation's source collection, discovery finds 69 subjects:
52 clauses, 11 clause hosts and 6 helpers. No model calls are needed for discovery.
Older committed cards are retained and published even after leaving the current
selection. Historical editions absent from both repo and S3 need an explicit
backfill using their exact package sources. Core adaptations which create new
BlueIds need their own exact cards; upstream identity aliases cannot cover them.

## Local preparation

Use Python 3.13 and the Codex CLI version pinned in `semantics/generator.json`:

```sh
python3.13 -m venv .venv
.venv/bin/python -m pip install -r tools/semantic-requirements.txt
npm install -g @openai/codex@0.162.1
codex login

# No model request; shows ready and missing types.
.venv/bin/python tools/semantic_cards.py check

# Optional read-only AWS credentials: restore S3 cards before planning generation.
.venv/bin/python tools/semantic_cards.py plan --bucket YOUR_BUCKET

# Generate only missing cards; add --bucket YOUR_BUCKET to reuse S3 as well.
.venv/bin/python tools/semantic_cards.py generate --jobs 4 --bucket YOUR_BUCKET

.venv/bin/python tools/semantic_cards.py check
git add semantics/cards
```

Review and commit the cards with the package changes in your normal PR. Local
generation never uploads to S3 or creates a git commit. Without `--bucket`, it
uses the repo only and does not claim to have checked S3. Successful cards survive
other failures; rerunning requests only the remaining identities. `--jobs` permits
1–16 concurrent local calls. Contexts and reports go to ignored `build/semantics/`.

To prepare a card manually with Codex or another model, run `plan`, supply the
corresponding `build/semantics/requests/<blueId>.txt` and
`semantics/output.schema.json`, then import its JSON response:

```sh
.venv/bin/python tools/semantic_cards.py accept \
  --request build/semantics/requests/TYPE_BLUE_ID.json \
  --response /path/to/response.json \
  --output semantics/cards
```

For a different generator, record its actual model, effort and version in that
request's `generator` object for diagnostics. Acceptance checks the request
checksum, exact BlueId and output schema, then saves the two-field response
without enriching it. It refuses to overwrite an existing different card. The
CI collector also rechecks the request against the current source evidence.
The model receives bounded exact definitions and dependencies, never credentials
or private account documents as input. Local execution uses a temporary working
directory and the CLI read-only sandbox.

## GitHub workflows

`Semantic cards check` runs on every PR, main push and manual dispatch, including
commits with unchanged clauses. It validates cards and reports missing identities.
Missing descriptions are informational: they do not block package publication.
Malformed committed data or inconsistent package artifacts do fail the check.

After a successful check, `Generate missing semantic cards`:

1. Rechecks that the source is current main or an open PR from this repository.
2. Uses trusted tooling from the workflow's default-branch revision to parse the
   candidate checkout as data. Fork PRs do not receive generation credentials.
3. Lists the S3 bucket, reuses local cards, restores published cards, and prepares
   a matrix containing only missing BlueIds.
4. Generates up to 8 cards concurrently in separate jobs. The model job has no
   AWS role or repository write token. Its Action and CLI versions are pinned.
5. Independently validates each output and commits successful/restored cards in
   **one bot commit** to the still-current PR branch. A partial batch preserves
   its successes. Main runs open a separate review PR instead of pushing to main.

The batch limit is 256 identities, matching GitHub's matrix limit. A successful
bot commit dispatches the coverage and package integrity workflows for its new
SHA; their next generation pass handles remaining identities. Existing cards are
not regenerated. A duplicate main run skips an already open generation PR for
that source revision. A run where every remaining card fails stops without a
commit; rerun the check after resolving the failure.

Normal pushes reject concurrent branch changes; the bot never force-pushes. If
the source advances during generation, results remain in the run's artifacts for
14 days and the newer check owns preparation. Two independent PRs introducing
the same previously unseen BlueId can generate it independently until a card is
committed in their source or published. There is no cross-PR generation database.

`GITHUB_TOKEN` pushes do not trigger ordinary push workflows. The explicit
dispatches above run validation after the bot commit. GitHub may also create PR
runs requiring approval for bot events; other required checks must be configured
for bot commits according to repository policy. See GitHub's
[token event rules](https://docs.github.com/en/actions/concepts/security/github_token).

`Publish semantic cards` runs independently on main, `blue-packages-*` tags and
manual dispatch. It accepts only commits in main history, skips superseded main
runs, validates committed cards and publishes them without model calls. It is not
a dependency of the existing package release workflow. Tag runs fill gaps but
cannot roll an existing card back to an older correction. Main runs promote the
reviewed repo version. Old type identities and S3 object versions are never deleted.

To recover a failed upload, rerun publication on main. To regenerate missing
outputs on a PR, dispatch `semantic-cards-check.yml` for its branch. Generation's
own manual dispatch is limited to main. The generation workflow must first exist
on the default branch for `workflow_run` triggers to operate.

## S3 layout and checking presence

```text
s3://blue-semantic-cards-${EnvName}/<typeBlueId>.json

# EnvName=dev, using the locally generated Hello Clause card:
s3://blue-semantic-cards-dev/6djSCK7TuFMBty51HWymVGRpnBdYTyFGf944FWZFYG4D.json
```

Each object contains the complete card JSON, identical to the canonical repo
file in `semantics/cards/<typeBlueId>.json`. There are no intermediate folders or
head files. Git preserves review history; bucket versioning preserves previous
published contents under the same object key. Publication compares the entire
two-field card to detect corrections; no content hash is stored in the card.

The planner uses paginated `ListObjectsV2` for the dedicated bucket (up to 1,000
keys per request), then compares sets locally. It does **not** issue a presence
`HEAD` request for every clause. For a card absent from the repo, it fetches that
BlueId's JSON directly, checks identity/schema/size, and stages the file. A local
card whose key is absent from S3 is reported as `unpublished`, not generated again.
This presence check does not compare existing S3 contents to local corrections;
publication handles that. AWS errors, including access denied, are never treated
as a missing card.

Publication also lists keys once and uploads missing cards with `If-None-Match: *`.
It reads existing cards to skip identical contents and detect corrections. Only
main (or an explicit `--promote`) applies corrections, using `If-Match` with the
current ETag. Concurrent different writes cannot silently overwrite each other;
a conflict fails publication and is resolved by rerunning from current main.
Each upload is a single object write; there is no separate pointer to repair.

Clients fetch `<typeBlueId>.json` directly and validate its identity and two-field
schema. Objects use `Cache-Control: no-cache`; clients can revalidate with the
ETag so corrections are visible even when the type BlueId is unchanged.
This change supplies the producer and S3 contract. Business/chat still need an
S3 or CDN reader and mapping to their registry; no `blue-packages` code dependency
is needed. Only public package semantics belong in this bucket. Private/custom
document semantics remain in their existing account scope.

The earlier full-record format is not accepted by this schema. When migrating,
review existing repo cards as `blueId` plus `semanticText`, update consumers that
require removed fields, and publish the reviewed correction from main. Existing
S3 objects are replaced through the same conditional promotion; bucket versioning
retains their previous contents. Restore does not silently strip legacy fields.

## Enable automation

For scoped infrastructure creation and updates from GitHub, see
[Semantic card infrastructure deployment](semantic-infrastructure.md). It adds
separate DEV/PROD deployment roles and a manual workflow around this same template.
The following steps remain the administrator-driven setup for the card pipeline;
deploying infrastructure does not itself enable generation or switch its target.

`semantics/template.yaml` defines the bucket as `blue-semantic-cards-${EnvName}`.
It enables versioning, encryption and private access, requires HTTPS, and retains
the bucket when deleting or replacing the stack. It also creates separate GitHub
read/publish roles and can create the account's GitHub OIDC provider if needed.

Give the template and these steps to the colleague with AWS deployment access.
The deployer needs permission to manage this CloudFormation stack, its S3 bucket
and IAM roles/policies (and the OIDC provider when creating it). First confirm
the AWS account selected by their CLI:

```sh
aws sts get-caller-identity --query Account --output text
aws iam list-open-id-connect-providers \
  --query 'OpenIDConnectProviderList[].Arn' --output text
```

If the list contains an ARN ending in
`:oidc-provider/token.actions.githubusercontent.com`, reuse it: leave
`CreateGitHubOIDCProvider=false`. Check that its client IDs include
`sts.amazonaws.com` using `aws iam get-open-id-connect-provider
--open-id-connect-provider-arn PROVIDER_ARN`. If the audience is missing, add it
with `aws iam add-client-id-to-open-id-connect-provider
--open-id-connect-provider-arn PROVIDER_ARN --client-id sts.amazonaws.com`.
If there is no provider, use `CreateGitHubOIDCProvider=true` in the deployment
below. A permission error from either read command must be resolved, not treated
as an absent provider. An existing provider may be shared with `blue-repository`;
do not create a duplicate or replace it.

For dev in `eu-west-1`, deploy from the `blue-packages` checkout:

```sh
aws cloudformation deploy \
  --template-file semantics/template.yaml \
  --stack-name blue-semantic-cards-dev \
  --parameter-overrides EnvName=dev CreateGitHubOIDCProvider=false \
  --capabilities CAPABILITY_NAMED_IAM \
  --no-fail-on-empty-changeset \
  --region eu-west-1
```

The bucket name must be available. Region and account ID are configuration values,
not part of the name. The dev roles are `blue-semantic-cards-dev-read` and
`blue-semantic-cards-dev-publish`. Keep the chosen provider parameter on later
deployments. The stack retains any OIDC provider it creates because it may later
be shared by other repositories. It does not deploy an API or modify GitHub settings.

After a successful deployment, have the colleague run this and send back the
output (five non-secret `NAME=value` lines, already filled with the actual account
ID and role ARNs):

```sh
aws cloudformation describe-stacks \
  --stack-name blue-semantic-cards-dev \
  --query 'Stacks[0].Outputs[?OutputKey==`GitHubVariables`].OutputValue | [0]' \
  --output text \
  --region eu-west-1
```

Add those five values to **Settings → Secrets and variables → Actions → Variables**
in `bluecontract/blue-packages`. No AWS access keys need to be exchanged. The AWS
colleague does not need access to GitHub to do this part.

The workflows default to checks only. Configure these repository Actions variables:

- `SEMANTICS_BUCKET`: `blue-semantic-cards-dev` for `EnvName=dev`, or the corresponding environment's bucket.
- `SEMANTICS_AWS_REGION`: bucket region.
- `SEMANTICS_AWS_ACCOUNT_ID`: expected AWS account ID.
- `SEMANTICS_READ_ROLE_ARN`: OIDC role for listing and reading the bucket's cards.
- `SEMANTICS_PUBLISH_ROLE_ARN`: separate OIDC role for listing, reading and writing it.
- `SEMANTICS_GENERATION_ENABLED`: `true` after model access and S3 reads are ready.
- `SEMANTICS_PUBLICATION_ENABLED`: `true` after publication permissions are ready.

Add repository secret `OPENAI_API_KEY` with access to the pinned model. GitHub
generation uses API billing; a developer's local Codex login is not a GitHub
Actions credential. The default model/effort and CLI version are in
`semantics/generator.json`; changes affect newly missing cards only.

Enable Actions permission to create pull requests. Permit the collector's
`contents: write`, `pull-requests: write` and `actions: write` permissions, and
allow bot commits to source PR branches. Main stays behind the usual PR review.
Create the `semantics-publish` environment and restrict it to main and the
reviewed `blue-packages-*` tags. Neither enable flag bypasses repository or
environment protection rules.

Both roles trust audience `sts.amazonaws.com`. The template uses the exact
immutable OIDC prefix returned by GitHub's API for this repository on 2026-10-22:
`repo:bluecontract@93829250/blue-packages@1391542341`. The read role permits that
prefix followed by `:ref:refs/heads/main` (the trusted generation workflow runs on
the default branch even when inspecting a PR). The publish role permits the
prefix followed by `:environment:semantics-publish`. If the repository is renamed,
transferred or its OIDC customization changes, update the trust policy using the
current API result:

```sh
gh api repos/bluecontract/blue-packages/actions/oidc/customization/sub
```

See
[GitHub's AWS OIDC guide](https://docs.github.com/en/actions/how-tos/secure-your-work/security-harden-deployments/oidc-in-aws).
The template grants:

- `s3:ListBucket` on `arn:aws:s3:::blue-semantic-cards-dev` for both roles.
- `s3:GetObject` on `arn:aws:s3:::blue-semantic-cards-dev/*.json` for both roles.
- `s3:PutObject` on those objects for the publisher only. No delete permission.

Use the corresponding bucket name for other environments. Listing is at the bucket
root, so do not retain a condition restricting `s3:prefix` to the old layout.

With SSE-KMS, grant the corresponding KMS permissions as well. Keep bucket access
private unless public delivery through a bucket/CDN policy is intentionally
configured; Business can use a read role. Keep bucket versioning enabled to retain
earlier corrections. See AWS's
[OIDC setup](https://docs.aws.amazon.com/IAM/latest/UserGuide/id_roles_providers_create_oidc.html),
[S3 listing contract](https://docs.aws.amazon.com/AmazonS3/latest/API/API_ListObjectsV2.html)
and [conditional writes](https://docs.aws.amazon.com/AmazonS3/latest/userguide/conditional-writes.html).

A maintainer can publish a reviewed local checkout manually, without generation:

```sh
.venv/bin/python tools/semantic_cards.py publish --bucket YOUR_BUCKET
```

This fills missing objects but does not promote corrections. Only use
`--promote` when deliberately applying the reviewed current-main card selection.
To correct a card, edit `semanticText` in its repo JSON, validate, and submit a PR
explaining the correction and its source basis. Keep its exact BlueId unchanged.
Publication replaces `<typeBlueId>.json` after merge; S3 versioning retains the
previous object contents.

## Verification

```sh
.venv/bin/python -m unittest discover -s tools -p 'test_semantic*.py' -v
.venv/bin/python -m unittest discover -s tools -p 'test_release.py' -v
.venv/bin/python tools/semantic_cards.py check
```

Tests cover discovery, new unbuilt exports, unchanged identities, local cards
missing from S3, S3 restoration, partial generation, the two-field schema,
generation request/source checks, pagination, AWS errors, conditional
publication/corrections and stale PRs. AWS
responses and model processes are simulated; these tests spend no model tokens
and do not write to S3. A configured GitHub run is still needed to verify actual
IAM, model access and repository branch policies.
