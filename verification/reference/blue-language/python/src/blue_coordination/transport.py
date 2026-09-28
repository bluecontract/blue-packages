"""Optional development retained-history transport; not an importer.

The transcript matches RetainedHistoryPage.transcript in the supplied Java
source. Signature verification is delegated to an installed Ed25519 verifier;
this module never treats a signature as Contracts execution authority.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Callable
import struct
from .errors import Code, require
from .identity import scalar_string, document_id


def java_modified_utf8(text: str) -> bytes:
    # DataOutputStream.writeUTF encodes UTF-16 code units, including pairs.
    raw = scalar_string(text).encode('utf-16-be', errors='strict')
    body = bytearray()
    for i in range(0, len(raw), 2):
        c = int.from_bytes(raw[i:i+2], 'big')
        if 1 <= c <= 0x7F:
            body.append(c)
        elif c <= 0x7FF:
            body.extend((0xC0 | (c >> 6), 0x80 | (c & 0x3F)))
        else:
            body.extend((0xE0 | (c >> 12), 0x80 | ((c >> 6) & 0x3F), 0x80 | (c & 0x3F)))
    require(len(body) <= 65535, Code.INVALID_EVIDENCE, 'Java writeUTF byte length exceeded')
    return struct.pack('>H', len(body)) + bytes(body)

@dataclass(frozen=True)
class HistoryPageRequest:
    source_document_id: str
    first_epoch: int
    limit: int
    challenge: str

    def __post_init__(self):
        document_id(self.source_document_id); scalar_string(self.challenge)
        require(type(self.first_epoch) is int and 0 <= self.first_epoch <= 2**63 - 1,
                Code.INVALID_EVIDENCE, 'invalid requested epoch')
        require(type(self.limit) is int and 1 <= self.limit <= 256,
                Code.INVALID_EVIDENCE, 'page limit outside 1..256')
        require(bool(self.challenge), Code.INVALID_EVIDENCE, 'empty challenge')

@dataclass(frozen=True)
class HistoryPage:
    request: HistoryPageRequest
    authored_initial_blue_id: str
    head_epoch: int
    head_blue_id: str
    predecessor_blue_id: str
    receipt_identities: tuple[str, ...]
    signature: bytes = b''

    def transcript(self) -> bytes:
        r = self.request
        require(type(self.head_epoch) is int and 0 <= self.head_epoch <= 2**63-1, Code.INVALID_EVIDENCE, 'invalid head epoch')
        parts = [java_modified_utf8('blue-coordination-retained-history-page/1.0'),
            java_modified_utf8(r.source_document_id), struct.pack('>q', r.first_epoch),
            struct.pack('>i', r.limit), java_modified_utf8(r.challenge),
            java_modified_utf8(self.authored_initial_blue_id), struct.pack('>q', self.head_epoch),
            java_modified_utf8(self.head_blue_id), java_modified_utf8(self.predecessor_blue_id),
            struct.pack('>i', len(self.receipt_identities))]
        parts.extend(java_modified_utf8(identity) for identity in self.receipt_identities)
        return b''.join(parts)


def verify_page(page: HistoryPage, request: HistoryPageRequest, *, authored_initial: str,
                predecessor: str, receipt_rows: tuple[tuple[int, str, str | None, str, str], ...],
                verify_ed25519: Callable[[bytes, bytes], None]) -> None:
    """Rows are (epoch, sourceDocumentId, beforeBlueId, afterBlueId, receiptId).

    The caller supplies a trusted public-key verifier. Row identities themselves
    must come from the complete verified receipt codec of the selected Contracts
    profile; this verifier checks transport binding/continuity only.
    """
    require(page.request == request and page.authored_initial_blue_id == authored_initial
            and page.predecessor_blue_id == predecessor,
            Code.INVALID_EVIDENCE, 'response request/lineage/predecessor mismatch')
    require(page.head_epoch >= request.first_epoch, Code.NEEDS_RESOURCES, 'requested epoch unavailable')
    expected_count = min(request.limit, page.head_epoch - request.first_epoch + 1)
    require(len(receipt_rows) == expected_count and len(page.receipt_identities) == expected_count,
            Code.INVALID_EVIDENCE, 'partial or oversized retained page')
    previous = predecessor
    for i, (epoch, source, before, after, identity) in enumerate(receipt_rows):
        require(epoch == request.first_epoch + i and source == request.source_document_id,
                Code.INVALID_EVIDENCE, 'gapped, reordered or misattributed page')
        require(identity == page.receipt_identities[i], Code.INVALID_EVIDENCE, 'receipt identity mismatch')
        if epoch != 0:
            require(before == previous, Code.INVALID_EVIDENCE, 'receipt predecessor mismatch')
        else:
            require(before is None and previous == authored_initial, Code.INVALID_EVIDENCE,
                    'epoch zero omits beforeBlueId and retains the separate authored anchor')
        previous = after
    if request.first_epoch + expected_count - 1 == page.head_epoch:
        require(previous == page.head_blue_id, Code.INVALID_EVIDENCE, 'captured head mismatch')
    try:
        verify_ed25519(page.signature, page.transcript())
    except Exception as error:
        from .errors import CoordinationError
        raise CoordinationError(Code.INVALID_EVIDENCE, 'invalid retained page signature') from error
