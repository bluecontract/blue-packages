The Operation Request `document` slot is an exact identity commitment, not an
ordinary payload-presence test. A supplied slot on the exact request, an inherited
fixed reference, or an inherited ordinary present value supplies a target. An
inherited declaration alone supplies none. Consequently a valid metadata-only,
contracts-only, empty or scalar exact target is retained even when Language
`present(target)` is false. This does not change Language presence or the ordinary
presence rule for the optional `request` argument. Exactification and value
certification still demand every required target/type dependency: unavailable or
invalid evidence propagates its existing failure and never turns an addressed
request into an unaddressed request. `requireExactDocumentVersion: true` still
requires the supplied target and compares its exact identity with the original
input member. Addressed-lineage selection and stale-intent rejection are unchanged.
