# Positive MyOS tutorial examples

26 YAML files from 12 completed passing walkthroughs in the fresh resident/H2 run against MyOS main `164e90f4`. Language/Contracts **3.1.0-rc.32**, BEX **1.1.0-rc.6**, Coordination **3.0.0-rc.12**, Repository **3.0.0-rc.22**.

Only positive example inputs are included. Invalid documents, missing-resource examples and negative test cases are excluded. This is a verified subset; the larger test run was still ongoing when packaged.

## Use

Open **Blue Workbench** (`/workbench`). Use **Calculate / Inspect** for values and type definitions, **Store Content** to obtain exact BlueIds, and **Start Managed** for executable documents. For managed examples, create the Timeline named in the channel declaration with the matching account before invoking operations. Discover operations from the started document.

Files ending in `.template.yaml` require replacing their `<...>` placeholders with IDs returned by your app. They are not ready to paste unchanged. Keep saved original IDs for historical attachment. Use an isolated workspace/database. `factory-input.yaml` is an operation request, not a document to start.

The files preserve bytes from passing maintained tests, including corrected fixtures where those were used. Some sequences bind references and construct requests at runtime; this ZIP is example inputs, not a standalone test runner. The manifest records exact sources, hashes and passing walkthrough evidence.

## Included

- **01:** object identity and equivalent scalar forms.
- **02:** inline and referenced parent; store Xyz from 01 first.
- **03:** Point, Colored Point and valid instances; store types and fill returned IDs in order.
- **04:** compact/explicit lists and an empty list.
- **05:** bare managed document.
- **06:** counter and public increment operation.
- **10:** child and host for historical attachment/catch-up.
- **11:** shared child across occurrences and parents; use the child from 10.
- **13:** Orders and an initially empty collection host.
- **16:** temperature logger and shipment.
- **18:** Order, host, factory and its request input.

Run `python3 verify.py` after extraction to verify every example against the manifest.
