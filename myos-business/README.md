# MyOS Business domain types

This unpublished package supplies native discovery identities for Business processes. It does not redefine MyOS parties, representatives, Tasks, Mandates, transport or permissions. Those remain in their existing packages.

The plain hierarchy is `Growth Initiative → Outreach Initiative → Email Outreach Initiative`. `Outreach Prospect → Email Outreach Prospect` identifies the recipient process separately. `Reseller Offer` specializes `Offers/Offer`; it is one commercial model, not a restriction on Outreach.

The two `with Clauses` variants use the same authored clause initialization and amendment contracts as `DocumentsDomain/Document with Clauses`. The plain bases have no automatic behavior. Concrete documents still supply configuration, state and policy. No static Agent roles, provider selection, commercial approval, sending or research is introduced by these types.

Future voice or messaging outreach can extend Outreach Initiative and Outreach Prospect. Search by an ancestor type finds its descendants through native Core type ancestry; a type match alone does not establish UI adapter support or authority to act.

Build locally using `tools/build_final_gas.py blue-offers` followed by `tools/build_final_gas.py myos-business` with the qualified runtime classpath. Archives and dependency locks are deterministic local inputs. No upload, registry publication or deployment is part of the build. Consumers must import the exact archives and verify their hashes. Existing documents keep their original type and history.
