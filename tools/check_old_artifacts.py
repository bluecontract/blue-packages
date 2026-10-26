#!/usr/bin/env python3
"""Reproduce the old Java/Core persisted-artifact boundary without migrating data.

Uses exact local Git objects, already prepared package inputs and offline Gradle.
The output must be a new task-owned directory. No original checkout is changed.
A successful check confirms the documented rejection, not deployment compatibility.
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import tarfile

BASES = {'java': '96931942c6c077bbc41538c5296076863898ab92',
         'core': '94b0788c1c7167d2a6e60c5863af515626e82a6a'}


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def run(command, cwd, log):
    with log.open('w') as stream:
        subprocess.run(command, cwd=cwd, stdout=stream, stderr=subprocess.STDOUT, check=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--java', type=Path, required=True)
    parser.add_argument('--myos', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    results = {}
    for name, checkout in [('java', args.java.resolve()), ('core', args.myos.resolve())]:
        baseline = BASES[name]
        archive = output / (name + '-baseline.tar')
        with archive.open('wb') as stream:
            subprocess.run(['git', '-C', str(checkout), 'archive', baseline], stdout=stream, check=True)
        old = output / (name + '-baseline')
        old.mkdir()
        with tarfile.open(archive) as source:
            source.extractall(old, filter='data')
        runtime = checkout if name == 'java' else checkout / 'runtime'
        old_runtime = old if name == 'java' else old / 'runtime'
        artifacts = output / (name + '-artifacts')
        probe = runtime / 'verification/compatibility'
        init = runtime / 'gradle/artifact-compatibility.gradle'
        command = ['bash', './gradlew', '-I', str(init),
                   '-PcompatibilitySource=' + str(probe),
                   '-PcompatibilityOutput=' + str(artifacts),
                   ':verification:artifactCompatibility', '--offline', '--no-daemon', '--console=plain']
        if name == 'java':
            command.append('-PbluePackagesDir=' + str(runtime / 'vendor/blue-packages'))
        run(command + ['-PcompatibilityMode=write'], old_runtime, output / (name + '-old.log'))
        retained = {p.name: sha(p) for p in artifacts.iterdir() if p.is_file()}
        run(command + ['-PcompatibilityMode=read'], runtime, output / (name + '-new.log'))
        assert all(sha(artifacts / p) == digest for p, digest in retained.items()), 'Old artifact was changed'
        corrected = json.loads((artifacts / 'corrected.json').read_text())
        results[name] = {
            'base': baseline, 'candidate': subprocess.check_output(['git', '-C', str(checkout), 'rev-parse', 'HEAD'], text=True).strip(),
            'candidateDiffSha256': hashlib.sha256(subprocess.check_output(['git', '-C', str(checkout), 'diff', 'HEAD'])).hexdigest(),
            'baselineArchiveSha256': sha(archive),
            'probeSha256': sha(probe / 'ArtifactCompatibilityProbe.java'),
            'buildAdapterSha256': sha(init),
            'retainedArtifactsSha256': retained,
            'oldArtifactsUnchanged': True,
            'checks': {case: corrected[case]['oldArtifactChecks'] for case in ('ascii', 'unicode')},
            'deploymentCompatibleWithAffectedHistory': False,
        }
    (output / 'result.json').write_text(json.dumps(results, indent=2) + '\n')
    print('Checks completed. Affected Unicode histories cannot resume; deployment remains restricted.')


if __name__ == '__main__':
    main()
