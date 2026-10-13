#!/usr/bin/env python3
"""Export the isolated Task M1 candidate sources to an explicit Core checkout."""
import hashlib
import json
from pathlib import Path
import shutil
import sys

root = Path(__file__).resolve().parents[1]
source = root / "blue-tasks"
core = Path(sys.argv[1]).resolve()
if not (core / "runtime/blue-core-service/build.gradle").is_file():
    raise SystemExit("Expected an explicit Core checkout")
target = core / "runtime/blue-core-service/src/test/resources/task-mvp-m1"
checksums = {}
for path in sorted(source.rglob("*")):
    if path.is_file() and not {"dist", "releases"}.intersection(path.relative_to(source).parts):
        relative = path.relative_to(source)
        destination = target / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(path, destination)
        checksums[str(relative)] = hashlib.sha256(path.read_bytes()).hexdigest()
(target / "source-checksums.json").write_text(json.dumps(checksums, indent=2) + "\n")
