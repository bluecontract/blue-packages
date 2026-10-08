# Installation and native support

Use the exact current Mandates publication from `PACKAGES.json`. Build its BEX
definitions with `tools/build-payment-family.sh Mandates` from the repository
root, then regenerate catalogue views with `tools/sync_catalogues.py`.

The Core Java runtime pins the exact archive and native marker explicitly.
Qualification includes current signed-provider approval/termination and the
historical native authority/replay regression suite. Data inspection with a
Python package reader does not assert Python support for this native revision.
