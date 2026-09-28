# Blue Coordination — Ed25519 Full-Prefix Binding 1.0

**Edition:** 21 September 2026, event-only integration.  
**Status:** Normative concrete provider binding; not a universal requirement on all Coordination providers.  
**Imports:** the Coordination core, Contracts canonical platform encoding and RFC 8032 Ed25519. Exact local imports are appended in the complete binding artifact.

## 1. Purpose and selection

This binding realizes Coordination's attributed immutable Timeline and complete-before promises using a source-bound Ed25519 verification key and signed full prefixes. It defines exact wire records and verification obligations in prose. It does not make a Python implementation normative.

The concrete **Ed25519 Timeline** type specializes the core Timeline role. Its exact type contains a `providerSpecification` reference to this complete binding Text and inherits the core `specification` reference. A Timeline descriptor contains exactly its concrete `type`, nonempty `timelineId` Text and `publicKey`. The key is 32 bytes encoded as exactly 64 lowercase hexadecimal characters. No whitespace or alternative alphabet is accepted.

The descriptor's full BlueId is the ordering-source identity. Changing the key changes that identity. This binding defines no implicit key rotation preserving the old identity. The receiver must explicitly adopt the exact descriptor and binding; a valid self-signature does not establish adoption.

The supplied concrete catalogue uses the core Actor, Source, Timeline Entry, Authority, Mandate Authority, Operation Mandate and Mandate Approval role definitions. Only the Timeline has this additional concrete provider subtype. The reference authoring alias `Coordination/Timeline` selects Ed25519 Timeline; the base role remains separately identified in the catalogue.

## 2. Entry representation and attribution

An entry is admitted Blue content with the exact standard Timeline Entry type. The fields are those of the selected Coordination entry contract. When the admitted message is a typed Operation Request, `operation` is required and is the exact same reference as `message`; otherwise `operation` is absent. The provider includes this field before identifying and signing the Entry. All reference-valued slots are published as pure exact references; `timestamp` is the integer microsecond value. Unknown direct fields are invalid. `prevEntry` is absent only for genesis. Null does not mean absence.

The provider establishes the actual actor from an authenticated ingress. The actor must be in its separately provisioned append permissions. The provider verifies exact message content and the standard actor/Timeline records. Optional origin data is admitted exact content. Authority is a claim, not a provider authorization decision for every target process.

The standard Actor has exactly its `type` and nonempty `actorId` Text. A standard Source value is arbitrary admitted origin data of the selected Source role. The provider cannot broaden append permission merely because a document's source discovery mentions a new actor.

## 3. Append order and idempotence

For a new accepted submission, the assigned timestamp is the greatest of the requested ordering time, the immediately previous accepted timestamp plus one, and the largest previously promised exclusive completeness frontier. Empty history contributes zero instead of a previous timestamp. All accepted timestamps remain in `0..9007199254740991`.

The new entry names the last accepted entry as its predecessor. If no supported timestamp remains, append fails. An accepted duplicate message under a new submission is a new Entry, not content-based deduplication.

When an append request ID is supplied, it is nonempty Text. Its bound request consists of actual Actor BlueId, requested time, exact message BlueId, optional authority BlueId and optional source BlueId. The reference request commitment uses the imported Contracts platform commitment with kind `coordination.append/1` and keys `actor`, `time`, `message`, `authority`, `source`; absent optional values use JSON null. Reuse with equal bound request returns the original Entry. Reuse with different bound request is an idempotency conflict.

## 4. Signed statement

The complete-prefix package is a closed platform record with exactly `statement` and `signature`. The statement contains exactly:

| Key | Exact value |
|---|---|
| `timeline` | Exact source Timeline BlueId as Text |
| `completeBefore` | Canonical decimal Text for the exclusive frontier |
| `entries` | Ordered array of exact Entry BlueId Text values, from genesis through the full prefix below the frontier |

The frontier Text has ASCII digits only, no sign, no leading zero except `0`, and a value in `0..9007199254740992`. The largest value is the permanent-closure sentinel and is not an accepted Entry timestamp.

The entry list is complete, duplicate-free and in increasing source timestamp/predecessor order. Every listed entry is strictly below the frontier. An empty signed list is positive empty-prefix evidence. Entry bodies may be transferred separately by exact identity; unavailable bodies are not empty-prefix evidence.

`signature` is an Ed25519 signature encoded as exactly 128 lowercase hexadecimal characters, representing 64 bytes.

## 5. Signed bytes

The signed message consists of the ASCII bytes for `Blue Coordination 1`, one LF byte, and the imported Contracts canonical encoding of a platform object containing exactly `kind` with Text value `prefix` and `value` with the statement object.

Contracts' `canonical` definition is the sole canonical platform encoder for this binding. It sorts object keys by Unicode scalar order, emits UTF-8 and no inter-token whitespace, retains array order, and distinguishes Boolean, null, Text and safe Integer. No floating-point values appear in this statement. This platform encoding is not the Language BlueId algorithm and is not replaced by ordinary library-default JSON formatting.

The signed statement does not include the signature. The selected primitive is RFC 8032 Ed25519, not Ed25519ph or Ed25519ctx. Public-key and signature lengths and hexadecimal grammar are checked before verification. A cryptographic library can implement the primitive; its API is not normative.

Normative external reference: RFC 8032, *Edwards-Curve Digital Signature Algorithm (EdDSA)*, Ed25519 and its test vectors. The distributed tests include the section 7.1 empty-message vector using public test key material, not a deployment key.

## 6. Acceptance conditions

A prefix package is accepted only when all of the following hold:

| Condition | Required evidence |
|---|---|
| Supported/adopted source | Exact requested Timeline is adopted and its concrete binding is supported |
| Closed shape | No missing or extra outer/statement keys; correct scalar/list formats |
| Exact source | Statement Timeline equals the requested exact Timeline |
| Adequate frontier | Stated frontier is at least the requested complete-before boundary |
| Valid signature | Signature verifies over the exact bytes above under the descriptor's key |
| Exact entries | Every named Entry resolves, is admitted and has the expected standard type and Timeline |
| Continuity | Genesis has no predecessor; every successor names the immediately previous list member |
| Order | Timestamps strictly increase and every timestamp is below the stated frontier |
| No duplicates | An Entry identity occurs once in the list |
| Consistent overlap | Every retained previously verified prefix agrees exactly on the common interval |

Failure of any condition yields a non-ready error, not a partially verified prefix. Content identity verification does not replace the signature; the signature does not replace source adoption or chain verification.

For two authenticated prefix statements, compare the ordered Entry IDs whose timestamps are below the smaller frontier. The sequences must be identical. A smaller historical request does not withdraw a larger previously promised frontier. The provider continues to obey the largest promise it has made.

A valid package is retained together with its exact proof commitment. The reference proof commitment uses the imported Contracts `digest` constructor with kind `coordination.prefix/1` and the complete package. This is platform audit identity, not a BlueId.

## 7. Capacity and provider state

The standard full-prefix wire limit is 4,096 entries. The reference provider stops accepting entries when its full supported history would exceed that limit; it does not truncate a longer history and describe the suffix as a complete genesis prefix.

The supplied feeder supports 256 current primitive sources and bounds one Mandate full replay at 4,096 processed external events. These last two values are reference-capacity declarations, not universal Coordination semantic limits. Capacity exhaustion is non-ready; it never proves authorization or idle-through.

Provider recovery preserves its exact accepted entries, largest closed frontier and idempotent request bindings. Promises are committed before exposure. Receiver recovery preserves adopted trust separately from received proof packages and reconstructs derived verified facts by verification or protected trusted state. An attacker cannot install a new adopted key through a restore package.

## 8. Required tests and scope

Conformance exercises positive and empty prefixes; wrong key/source; tampering; malformed hexadecimal; predecessor gaps; duplicate timestamps and identities; entries outside the frontier; conflicting overlap; historical smaller requests; back-insertion refusal; permanent closure; append idempotence; and restore preserving previous promises.

The binding authenticates the provider's assertion. It does not prove the truth of its real-world attribution or prevent a malicious provider from issuing contradictory signatures. Such contradictions are detectable evidence of a protocol violation when observed.

A paged history or another signature protocol needs its own exact binding. It may implement the same Coordination core without claiming this binding's wire conformance.

*End of the Ed25519 Full-Prefix Binding.*

---

# Exact imported specification bindings

```json
{
  "files": {
    "contracts/COMPLETE_SPECIFICATION.md": "dca04df596fb7e536d14cd1bdb923e943252f9915f814656d6918ecc2c7f00cd",
    "coordination/COMPLETE_SPECIFICATION.md": "76d7c299571caab8679fdbd2d073959ab9cd9f21eec8e19b137d5f9d649413d6"
  }
}
```
