#!/usr/bin/env python3
"""Check unmodified native observations; this does not authenticate completions."""
import argparse
import json
from pathlib import Path
import bootstrap
from demand_reference import check_snapshot_envelope, check_result_observations


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('native_output', type=Path)
    args = parser.parse_args()
    data = json.loads(args.native_output.read_text())
    package = data['package']
    envelope = check_snapshot_envelope(package, data['after'], data['release'],
                                       package['snapshot']['runtimes'])
    result = check_result_observations(data['observations'], data['receipt'],
        data['before'], data['after'], data['event'], data['timestamp'],
        data['gasPolicy'], data['release'])
    print(json.dumps({'envelope': envelope, 'result': result,
        'nativeAuthority': 'Actual Java execution, restore and completion tests; not issued by this checker',
        'editionQualification': 'NOT_VERIFIED'}, indent=2))


if __name__ == '__main__':
    main()
