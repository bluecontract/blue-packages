# Reseller clauses — 0.4.0-preview.3-myos.6

Tested business edition: reusable workflow-step listeners, native timer clauses,
fixed/bookable products, attributed balances, and parameterized document creation.
See WALKTHROUGH.md for the live Agreement and copyable documents and operations.

Each business folder contains source definitions and its immutable dist/package.bluepkg.
Foundation and Time dist folders are exact dependency copies for local package builds;
their original publication directories are unchanged.

MyOS currently uses a temporary 1,000,000-gas host budget per invocation. The published
100,000-gas specification is unchanged. Replayers must select the matching budget;
saved invocation policies retain it. This is an experimental host override.

Build/import generators and end-to-end tests live in ../myos-aws-test/scripts and
../myos-aws-test/runtime/blue-core-service. No bespoke native handler implements this
reseller business flow: it composes the package definitions on the generic runtime.
