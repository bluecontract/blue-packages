#!/usr/bin/env python3
"""Read a data package using the installed Blue Python implementation."""
import argparse
import json
from pathlib import Path
from blue_packages.reader import read_package

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--root',type=Path,required=True)
parser.add_argument('command',choices=('verify','inspect'))
parser.add_argument('archive',nargs='?',type=Path)
args=parser.parse_args()
package=read_package(args.archive or args.root/'dist/package.bluepkg')
print(json.dumps(package.manifest if args.command=='inspect' else
    {'verified':True,'packageBlueId':package.blue_id,'archiveSha256':package.archive_sha,'exports':list(package.exports)},indent=2))
