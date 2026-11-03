# Access Events package version labels

The unpublished package set replaces the `mvp-sync` suffix with the next explicit Access Events version. The authored definitions, protocol rules, operation budgets and exported type identities are unchanged. Package identities change because version and dependency metadata are part of each immutable publication.

| Package | Previous version | New version |
| --- | --- | --- |
| clause-documents | 0.8.0-preview.10.mvp-sync.1 | 0.8.0-preview.10.access-events.1 |
| clause-activation | 0.8.0-preview.4.access-events.1.mvp-sync.1 | 0.8.0-preview.4.access-events.2 |
| acme-bank, clause-attachments, clause-inspection, clause-payment, manual-payments, myos, shipping-instruction | 0.8.0-preview.7.access-events.3.mvp-sync.1 | 0.8.0-preview.7.access-events.4 |

The exact nine previous archives remain under `retained/version-labels-20261103` and are included in the existing retained archive inventory. They remain available for documents pinned to their historical package identities. Consumers must select one complete edition; combining old and new packages under the same aliases is unsupported.

The existing native builder generates the new archives and dependency locks. Core imports the resulting exact selection with its existing package importer, preserving historical catalogue entries and archives. Business imports only the corresponding package references and source provenance. Existing documents and historical template publications keep their original pins. No registry publication or deployment is performed by this change.

Local comparison and verification evidence is retained in ignored `reports/version-labels/`. Package reconstruction and identity checks establish source and archive equivalence; they do not qualify a live runtime rollout.
