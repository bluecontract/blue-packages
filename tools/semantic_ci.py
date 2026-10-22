#!/usr/bin/env python3
"""Trusted Actions orchestration: select a current source and commit validated cards."""
import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile
from urllib.parse import urlencode, quote

from jsonschema import ValidationError

from release import local, require, wire
from semantic_cards import accept, cards_in, inventory, read_json, save_card, validate_card


def gh(*args):
    return subprocess.check_output(['gh', *args], text=True).strip()


def api(path):
    return json.loads(gh('api', path))


def target(event, repository, default_branch):
    run = event.get('workflow_run')
    if run:
        if run['conclusion'] != 'success' or run['head_repository']['full_name'] != repository:
            return None
        sha, branch = run['head_sha'], run['head_branch']
    else:
        branch = os.environ['GITHUB_REF_NAME']
        sha = os.environ['GITHUB_SHA']
    require(re.fullmatch('[0-9a-f]{40}', sha), 'Invalid source SHA')
    require(subprocess.run(['git', 'check-ref-format', 'refs/heads/' + branch], capture_output=True).returncode == 0, 'Invalid source branch')
    current = api(f'repos/{repository}/git/ref/heads/{quote(branch, safe="")}')['object']['sha']
    if current != sha:
        return None
    if branch == default_branch:
        query = urlencode({'state': 'open', 'head': repository.split('/')[0] + ':automation/semantics-' + sha[:12], 'base': default_branch})
        if api(f'repos/{repository}/pulls?{query}'):
            return None
        return dict(sha=sha, branch=branch, pullRequest=None, repository=repository, defaultBranch=default_branch)
    query = urlencode({'state': 'open', 'head': repository.split('/')[0] + ':' + branch, 'base': default_branch})
    matches = api(f'repos/{repository}/pulls?{query}')
    matches = [p for p in matches if p['head']['sha'] == sha and p['head']['repo']['full_name'] == repository]
    if len(matches) != 1:
        return None
    return dict(sha=sha, branch=branch, pullRequest=matches[0]['number'], repository=repository, defaultBranch=default_branch)


def collect(root, prepared, responses):
    subjects, definitions = inventory(root)
    destination = local(root, 'semantics/cards')
    plan = read_json(prepared / 'plan.json', 2_000_000)
    accepted, failed = [], []
    for blue_id in plan['restored']:
        require(blue_id in subjects, 'Recovered card is outside current selection')
        card = validate_card(read_json(prepared / 'cards' / (blue_id + '.json')), blue_id, definitions)
        save_card(destination, card)
        accepted.append(blue_id)
    for blue_id in plan['generate']:
        response = responses / (blue_id + '.json')
        if not response.exists():
            failed.append(blue_id)
            continue
        try:
            request = read_json(prepared / 'requests' / (blue_id + '.json'), 1_000_000)
            # Accept into an isolated folder before checking against the exact
            # candidate source again. No agent output becomes executable code.
            with tempfile.TemporaryDirectory() as tmp:
                card = accept(request, read_json(response), Path(tmp))
                validate_card(card, blue_id, definitions)
                save_card(destination, card)
            accepted.append(blue_id)
        except (ValueError, KeyError, TypeError, ValidationError) as error:
            print(f'Rejected {blue_id}: {str(error).splitlines()[0][:500]}')
            failed.append(blue_id)
    cards_in(root, definitions)
    return dict(accepted=accepted, failed=failed)


def commit(root, selected):
    repository, branch, expected = selected['repository'], selected['branch'], selected['sha']
    if api(f'repos/{repository}/git/ref/heads/{quote(branch, safe="")}')['object']['sha'] != expected:
        print('Source advanced; the newer coverage run owns generation. Results remain in the run artifact.')
        return
    if selected['pullRequest']:
        pr = api(f'repos/{repository}/pulls/{selected["pullRequest"]}')
        if pr['state'] != 'open' or pr['head']['sha'] != expected or pr['head']['repo']['full_name'] != repository:
            return

    def git(*args):
        return subprocess.check_output(['git', '-c', 'core.hooksPath=/dev/null', *args], cwd=root, text=True).strip()
    require(git('rev-parse', 'HEAD') == expected, 'Checkout differs from selected source')
    require(not (root / 'semantics/cards').is_symlink(), 'Cards directory cannot be a symlink')
    git('add', '--', 'semantics/cards')
    changed = git('diff', '--cached', '--name-only').splitlines()
    require(all(re.fullmatch(r'semantics/cards/[1-9A-HJ-NP-Za-km-z]{32,64}\.json', p) for p in changed), 'Refusing to commit non-card changes')
    if not changed:
        print('No new cards; no commit.')
        return
    git('config', 'user.name', 'github-actions[bot]')
    git('config', 'user.email', '41898282+github-actions[bot]@users.noreply.github.com')
    git('commit', '-m', f'docs(semantics): add {len(changed)} exact type cards')
    destination = branch if selected['pullRequest'] else 'automation/semantics-' + expected[:12]
    # A normal push rejects a concurrently updated source branch; never force it.
    git('push', 'origin', 'HEAD:refs/heads/' + destination)
    if not selected['pullRequest']:
        body = root / 'build/semantic-pr.md'
        body.parent.mkdir(exist_ok=True)
        body.write_text('Adds validated semantic cards for exact public types missing from the source collection.\n\n'
                        'Review the generated meanings before merging. Structural validation is not semantic or runtime qualification.\n')
        gh('pr', 'create', '--repo', repository, '--base', selected['defaultBranch'], '--head', destination,
           '--title', 'Add missing public semantic cards', '--body-file', str(body))
    # GITHUB_TOKEN pushes do not run push workflows; dispatch checks for the new head explicitly.
    for workflow in ('semantic-cards-check.yml', 'packages-release.yml'):
        gh('workflow', 'run', workflow, '--repo', repository, '--ref', destination)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=('target', 'collect', 'commit'))
    parser.add_argument('--root', type=Path, default=Path('candidate'))
    parser.add_argument('--prepared', type=Path, default=Path('prepared'))
    parser.add_argument('--responses', type=Path, default=Path('responses'))
    parser.add_argument('--target', type=Path, default=Path('target.json'))
    args = parser.parse_args()
    if args.command == 'target':
        event = json.loads(Path(os.environ['GITHUB_EVENT_PATH']).read_text())
        selected = target(event, os.environ['GITHUB_REPOSITORY'], event['repository']['default_branch'])
        args.target.write_bytes(wire(selected))
        with open(os.environ['GITHUB_OUTPUT'], 'a') as stream:
            stream.write('eligible=' + str(selected is not None).lower() + '\n')
            if selected:
                stream.write('sha=' + selected['sha'] + '\n')
        print(json.dumps(selected))
    elif args.command == 'collect':
        result = collect(args.root.resolve(), args.prepared, args.responses)
        print(json.dumps(result))
        with open(os.environ.get('GITHUB_STEP_SUMMARY', os.devnull), 'a') as stream:
            stream.write(f"\nAccepted cards: {len(result['accepted'])}; failed/missing outputs: {len(result['failed'])}.\n")
    else:
        commit(args.root.resolve(), read_json(args.target))


if __name__ == '__main__':
    main()
