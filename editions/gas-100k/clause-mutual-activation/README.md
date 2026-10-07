# Mutual Activation

Version **0.3.0-rc.1**. Two-party review, proposals, approvals and decline with exact revision matching. Pending review resets on amendment; activation or decline freezes the Agreement configuration.

Uses Agreements 0.3.0-rc.1. Amendment requests require `expectedRevision`; see
[the Agreements guide](../blue-agreements/docs/root-clauses.md). Old immutable
publications are retained separately. This package changes no native protocols.
