# ACME timelines and an executable Timeline Access document

All company/person data are fictional. The Ed25519 signatures are real but use
public test keys. [protocol.json](../examples/protocol.json) contains complete
requests, signed responses, exact Blue references and the executed before/after
documents. Type aliases below resolve to those exact types; there is no separate
protocolVersion, providerId, accessId, timelineId or grantId.

## Provider and actor types

ACME specializes Timeline Provider with domain details. Its exact type carries
those inherited values, including the common API base. The
instance supplies only its verification key. Clients resolve the inherited fields
through Blue; their omission from the instance JSON does not make them absent.

```json
{
  "name": "ACME Timeline Provider",
  "type": "Coordination/Timeline Provider",
  "companyName": "ACME Timeline Services Sp. z o.o.",
  "registeredOffice": "Example Street 10, Warsaw, Poland",
  "website": "https://acme.example",
  "endpoint": "https://timeline.acme.example"
}
```

```json
{
  "type": "Example/ACME Timeline Provider",
  "publicKey": "d04ab232742bb4ab3a1368bd4615e4e6d0224ab71a016baf8520a332c9778737"
}
```


Actors describe the publishing entity separately from the timeline's provider.
Principal Actor is human; Agent Actor is non-human. Domain identity data belong in
subtypes, such as Polish Citizen and ACME Access Service.

```json
{
  "type": "Example/Polish Citizen",
  "givenName": "Anna",
  "familyName": "Example",
  "citizenNumber": "DEMO-42"
}
```

```json
{
  "type": "Example/ACME Access Service",
  "serviceName": "ACME timeline access"
}
```


## Timelines and Hello entries

A timeline uses its canonical URL to distinguish its history. It has a provider,
but no additional arbitrary timeline ID. Its provider supplies the API base,
so POST to `https://timeline.acme.example/timelines/read` reads its history. The same URL serves
ACME's public control history. The exact timeline in the request selects the source.

```json
{
  "type": "Coordination/Signed Timeline",
  "provider": {
    "type": "Example/ACME Timeline Provider",
    "publicKey": "d04ab232742bb4ab3a1368bd4615e4e6d0224ab71a016baf8520a332c9778737"
  },
  "url": "https://timeline.acme.example/timelines/1234",
  "publicRead": false
}
```

```json
{
  "type": "Coordination/Timeline Entry",
  "timeline": {
    "blueId": "67uHAw9iqVeVfkLoJvcscrn5yR6EVtVJiKFmnjD7SuaG"
  },
  "timestamp": 1791288000000000,
  "actor": {
    "type": "Example/Polish Citizen",
    "givenName": "Anna",
    "familyName": "Example",
    "citizenNumber": "DEMO-42"
  },
  "message": "Hello"
}
```

```json
{
  "type": "Coordination/Timeline Entry",
  "timeline": {
    "blueId": "67uHAw9iqVeVfkLoJvcscrn5yR6EVtVJiKFmnjD7SuaG"
  },
  "timestamp": 1791288002000000,
  "actor": {
    "type": "Example/Polish Citizen",
    "givenName": "Anna",
    "familyName": "Example",
    "citizenNumber": "DEMO-42"
  },
  "message": "Hello 2",
  "prevEntry": {
    "blueId": "GajRtdu14ELqjvrR1nGbnv1CWpG5E9Uuv8TvnzNFKrcj"
  }
}
```


The entries are immutable. Hello 2 names Hello as its immediate predecessor.
Only one entry is allowed per microsecond per timeline. Simultaneous publications
must get different increasing timestamps, wait, or fail.

## The initial access document

The allowed timeline list holds Blue references, so it does not repeat provider
details. Each allowed key may read every allowed timeline. The provider is declared
once in contracts.provider. Resolve the API locations from that channel and its
provider to fetch the public history; no extra lookup identifier is needed.

```json
{
  "type": "Coordination/Timeline Access",
  "allowedTimelines": [
    {
      "blueId": "67uHAw9iqVeVfkLoJvcscrn5yR6EVtVJiKFmnjD7SuaG"
    }
  ],
  "allowedKeys": [
    "a09aa5f47a6759802ff955f8dc2d2a14a5c99d23be97f864127ff9383455a4f0"
  ],
  "contracts": {
    "provider": {
      "type": "Coordination/Public Timeline Channel",
      "provider": {
        "type": "Example/ACME Timeline Provider",
        "publicKey": "d04ab232742bb4ab3a1368bd4615e4e6d0224ab71a016baf8520a332c9778737"
      },
      "url": "https://timeline.acme.example/timelines/access"
    },
    "update": {
      "type": "Coordination/Update Timeline Access"
    }
  }
}
```


The document's initial BlueId is `5gAmgyeMdvYVZhHC4QJnvLgrnktSa1k7P4YwXixv6kNu`. Its public channel
means the Signed Timeline with that provider, that URL and publicRead=true, carrying
no additional API location. The signed provider descriptor confirms that this is ACME's reserved control timeline.
ACME publishes the complete initial document there to confirm its initial grants.
Anyone can verify this publication. A self-authored copy alone does not grant access.

contracts.update has type Update Timeline Access, a real Contracts Sequential
Workflow Operation. The type supplies BEX validation and an Update Document step
that replaces both lists atomically. It rejects duplicate values and foreign
providers. This is executable Blue content, not prose interpreted by a custom ACL
state machine. The specification contains the exact operation rules; the exported
type contains its actual program.

## One operation updates timelines and keys

Here ACME adds its second timeline and another reader key with one operation.
Every update targets the original published document. Both lists are replaced
atomically in accepted timeline order; a later accepted replacement determines the
lists. There is no version precondition or revision number.

```json
{
  "type": "Contracts/Operation Request",
  "document": {
    "blueId": "5gAmgyeMdvYVZhHC4QJnvLgrnktSa1k7P4YwXixv6kNu"
  },
  "channel": "provider",
  "operation": "update",
  "request": {
    "type": "Coordination/Timeline Access Update",
    "allowedTimelines": [
      {
        "blueId": "67uHAw9iqVeVfkLoJvcscrn5yR6EVtVJiKFmnjD7SuaG"
      },
      {
        "blueId": "7s84My5goBx3MMmWp9XeNCVoMN1XLHJLUJcMy71YTYwz"
      }
    ],
    "allowedKeys": [
      "a09aa5f47a6759802ff955f8dc2d2a14a5c99d23be97f864127ff9383455a4f0",
      "17cb79fb2b4120f2b1ec65e4198d6e08b28e813feb01e4a400839b85e18080ce"
    ]
  }
}
```


This operation is the message of a public control entry and also its identical
operation field. Feed that complete entry to Contracts at its timestamp. The
pinned processor returns `APPLIED` and the resulting
document has these permission fields:

```json
{
  "allowedTimelines": [
    {
      "blueId": "67uHAw9iqVeVfkLoJvcscrn5yR6EVtVJiKFmnjD7SuaG"
    },
    {
      "blueId": "7s84My5goBx3MMmWp9XeNCVoMN1XLHJLUJcMy71YTYwz"
    }
  ],
  "allowedKeys": [
    "a09aa5f47a6759802ff955f8dc2d2a14a5c99d23be97f864127ff9383455a4f0",
    "17cb79fb2b4120f2b1ec65e4198d6e08b28e813feb01e4a400839b85e18080ce"
  ]
}
```


Omitting a key or timeline from a later replacement removes its corresponding
permissions in this document. Independent grants can still provide access. Owner
credentials authorize asking ACME to make the change; reader signatures cannot.

## Fetch that public channel's complete history

Resolve the inline channel's inherited provider URLs. Verify the signed GET
`https://timeline.acme.example/provider` descriptor against that provider, then send
this bare request to the shared read URL:

`POST https://timeline.acme.example/timelines/read`

```json
{
  "type": "Coordination/Read Timeline Request",
  "timeline": {
    "blueId": "DWs7SRJ9GjJ291kfsJg9YvvZVCei71HVXpK3zVGjuCMK"
  },
  "limit": 100
}
```


No reader key, signature, login, nonce, request label or client timestamp is needed.
This is the complete signed response, with the initial publication and update:

<details><summary>Public response: two entries and a completeness checkpoint</summary>

```json
{
  "type": "Coordination/Provider Attestation",
  "provider": {
    "blueId": "DqSrLRvQXMzhv7ZSpRTQHwKpVCv4NHJE1ywZyUC6cC8z"
  },
  "object": {
    "type": "Coordination/Timeline Read Response",
    "request": {
      "blueId": "b2wEdBBdzPaiSzwC8VtwUxcmMAtzwkNji3F9TXzwwGD"
    },
    "checkpoint": {
      "type": "Coordination/Timeline Attestation",
      "timeline": {
        "blueId": "DWs7SRJ9GjJ291kfsJg9YvvZVCei71HVXpK3zVGjuCMK"
      },
      "guarantee": {
        "type": "Coordination/Timeline Completeness Guarantee",
        "timeline": {
          "blueId": "DWs7SRJ9GjJ291kfsJg9YvvZVCei71HVXpK3zVGjuCMK"
        },
        "completeBefore": 1791288003000000,
        "lastEntry": {
          "blueId": "o1P1s15w5ujXUMezTQwHeiUApJYb93zgprtfoq2jfok"
        }
      },
      "signature": "ba971baf039295c7efaae6dceecc531314390bd67443aadc998820e3946bbcfa198bbcbe61745edde15c8acb10d549b24a647f32ef3098bde35a3a25145ce90b"
    },
    "page": {
      "type": "Coordination/Timeline Entries Page",
      "timeline": {
        "blueId": "DWs7SRJ9GjJ291kfsJg9YvvZVCei71HVXpK3zVGjuCMK"
      },
      "checkpoint": {
        "blueId": "8ZHfkH7XPVJVT8JDPm1NmN4vpcsQ2FdSMRPierwee4nB"
      },
      "entries": [
        {
          "type": "Coordination/Timeline Entry",
          "timeline": {
            "blueId": "DWs7SRJ9GjJ291kfsJg9YvvZVCei71HVXpK3zVGjuCMK"
          },
          "timestamp": 1791287999000000,
          "actor": {
            "type": "Example/ACME Access Service",
            "serviceName": "ACME timeline access"
          },
          "message": {
            "type": "Coordination/Timeline Access",
            "allowedTimelines": [
              {
                "blueId": "67uHAw9iqVeVfkLoJvcscrn5yR6EVtVJiKFmnjD7SuaG"
              }
            ],
            "allowedKeys": [
              "a09aa5f47a6759802ff955f8dc2d2a14a5c99d23be97f864127ff9383455a4f0"
            ],
            "contracts": {
              "provider": {
                "type": "Coordination/Public Timeline Channel",
                "provider": {
                  "type": "Example/ACME Timeline Provider",
                  "publicKey": "d04ab232742bb4ab3a1368bd4615e4e6d0224ab71a016baf8520a332c9778737"
                },
                "url": "https://timeline.acme.example/timelines/access"
              },
              "update": {
                "type": "Coordination/Update Timeline Access"
              }
            }
          }
        },
        {
          "type": "Coordination/Timeline Entry",
          "timeline": {
            "blueId": "DWs7SRJ9GjJ291kfsJg9YvvZVCei71HVXpK3zVGjuCMK"
          },
          "timestamp": 1791288002500000,
          "actor": {
            "type": "Example/ACME Access Service",
            "serviceName": "ACME timeline access"
          },
          "message": {
            "type": "Contracts/Operation Request",
            "document": {
              "blueId": "5gAmgyeMdvYVZhHC4QJnvLgrnktSa1k7P4YwXixv6kNu"
            },
            "channel": "provider",
            "operation": "update",
            "request": {
              "type": "Coordination/Timeline Access Update",
              "allowedTimelines": [
                {
                  "blueId": "67uHAw9iqVeVfkLoJvcscrn5yR6EVtVJiKFmnjD7SuaG"
                },
                {
                  "blueId": "7s84My5goBx3MMmWp9XeNCVoMN1XLHJLUJcMy71YTYwz"
                }
              ],
              "allowedKeys": [
                "a09aa5f47a6759802ff955f8dc2d2a14a5c99d23be97f864127ff9383455a4f0",
                "17cb79fb2b4120f2b1ec65e4198d6e08b28e813feb01e4a400839b85e18080ce"
              ]
            }
          },
          "prevEntry": {
            "blueId": "GenWvGs2A9JZGCRS3PB24yMLQNns32qSVR9XdapXgDcP"
          },
          "operation": {
            "blueId": "C9CVFN2KiGMLJzR37Js4gvbaguUpxCZQi7owsfgqywv"
          }
        }
      ],
      "hasMore": false
    }
  },
  "signature": "61a76d826025207a6a45cb35d162e762b29bbdd2decbdd5e36627eceec4b44ecf617f09d2904144fcb85dec63e578baf92cf27478036f827c0c5d051f6210306"
}
```

</details>

It contains the checkpoint, page and real provider signatures. Verify and execute
the applicable entries to calculate the access document's current state.

For more than 100 entries, send the returned nextCursor as cursor, with the same
timeline and limit. Repeat until hasMore=false. The fixed checkpoint prevents
concurrent appends from changing the page sequence. Public history stays readable
after every private reader key has been revoked.

## Private reads: both Hello entries, then only Hello 2

Private requests use an Ed25519 Signed Reader Request. Sign the exact bytes
UTF8("blue.coordination.reader-request\n" + BlueId(innerRequest)). The target
already identifies the provider. Both requests use
`POST https://timeline.acme.example/timelines/read`. These are the complete signed requests:

```json
{
  "type": "Coordination/Signed Reader Request",
  "request": {
    "type": "Coordination/Read Timeline Request",
    "timeline": {
      "blueId": "67uHAw9iqVeVfkLoJvcscrn5yR6EVtVJiKFmnjD7SuaG"
    },
    "limit": 100
  },
  "publicKey": "a09aa5f47a6759802ff955f8dc2d2a14a5c99d23be97f864127ff9383455a4f0",
  "signature": "a4ce28722e35a94f4c407e2e3477477b388edf80ab9db206e827971e8e5c81727358654bdfc2d44bd77e4880d90e75ca4f9e08fd10f69844e33074a6fe358c0b"
}
```

```json
{
  "type": "Coordination/Signed Reader Request",
  "request": {
    "type": "Coordination/Read Timeline Request",
    "timeline": {
      "blueId": "67uHAw9iqVeVfkLoJvcscrn5yR6EVtVJiKFmnjD7SuaG"
    },
    "limit": 100,
    "afterEntry": {
      "blueId": "GajRtdu14ELqjvrR1nGbnv1CWpG5E9Uuv8TvnzNFKrcj"
    }
  },
  "publicKey": "a09aa5f47a6759802ff955f8dc2d2a14a5c99d23be97f864127ff9383455a4f0",
  "signature": "73c7bcee9fb7f6964538b02a59d26ebae5a002c1aecffff0f85765ae53cfd214036b48344c5e0d0ca5b82f724e77dccc250b6d717efcb685e588ffdc18f2bc06"
}
```


The first returns Hello and Hello 2; the second returns only Hello 2, with predecessor
evidence for Hello. Their full signed responses and a two-page variant are in the
same fixture, along with the individual response for each request.

<details><summary>Private response: Hello and Hello 2</summary>

```json
{
  "type": "Coordination/Provider Attestation",
  "provider": {
    "blueId": "DqSrLRvQXMzhv7ZSpRTQHwKpVCv4NHJE1ywZyUC6cC8z"
  },
  "object": {
    "type": "Coordination/Timeline Read Response",
    "request": {
      "blueId": "2GAJW4Xfwo7hcczyX3SMWTmuhD3UZ4UMfn3jgt6uaeQu"
    },
    "checkpoint": {
      "type": "Coordination/Timeline Attestation",
      "timeline": {
        "blueId": "67uHAw9iqVeVfkLoJvcscrn5yR6EVtVJiKFmnjD7SuaG"
      },
      "guarantee": {
        "type": "Coordination/Timeline Completeness Guarantee",
        "timeline": {
          "blueId": "67uHAw9iqVeVfkLoJvcscrn5yR6EVtVJiKFmnjD7SuaG"
        },
        "completeBefore": 1791288003000000,
        "lastEntry": {
          "blueId": "A3gVTvQJFTTkkbrp9tx2bRA9FayCmoRQojGkc8VQE1kJ"
        }
      },
      "signature": "28d466fc0c28fc648df2f3e82599e86ccb962b83d000b4ed13945b77d9810ede7aed8645084c3c1edd0eb0b996c141619362db5e633b1e0deb6f5beeb4009607"
    },
    "page": {
      "type": "Coordination/Timeline Entries Page",
      "timeline": {
        "blueId": "67uHAw9iqVeVfkLoJvcscrn5yR6EVtVJiKFmnjD7SuaG"
      },
      "checkpoint": {
        "blueId": "8Azrc39MMfH9JqeWoPZwcgDbQebQ5m4fwtkNnZp2F2T7"
      },
      "entries": [
        {
          "type": "Coordination/Timeline Entry",
          "timeline": {
            "blueId": "67uHAw9iqVeVfkLoJvcscrn5yR6EVtVJiKFmnjD7SuaG"
          },
          "timestamp": 1791288000000000,
          "actor": {
            "type": "Example/Polish Citizen",
            "givenName": "Anna",
            "familyName": "Example",
            "citizenNumber": "DEMO-42"
          },
          "message": "Hello"
        },
        {
          "type": "Coordination/Timeline Entry",
          "timeline": {
            "blueId": "67uHAw9iqVeVfkLoJvcscrn5yR6EVtVJiKFmnjD7SuaG"
          },
          "timestamp": 1791288002000000,
          "actor": {
            "type": "Example/Polish Citizen",
            "givenName": "Anna",
            "familyName": "Example",
            "citizenNumber": "DEMO-42"
          },
          "message": "Hello 2",
          "prevEntry": {
            "blueId": "GajRtdu14ELqjvrR1nGbnv1CWpG5E9Uuv8TvnzNFKrcj"
          }
        }
      ],
      "hasMore": false
    }
  },
  "signature": "a471741942e751e7d7b314aaad26eb6efe71cb126fa4cac0c7aff6e06c4c75c4d163c18280e33a651708f67f3e712868e24084546261d81920235545dc298604"
}
```

</details>

Repeating a signature repeats that exact query; every use rechecks
current access. To demand history closed through a particular time, include
minimumCompleteBefore, rather than a client-created timestamp or expiry.

## One API endpoint

ACME's type supplies `endpoint: https://timeline.acme.example`. Every public and
private timeline uses `POST https://timeline.acme.example/timelines/read`.
The target timeline is part of the request. Public reads omit the reader envelope;
private reads carry an authorized key and Ed25519 signature. Every response is
provider-signed. Canonical timeline URLs identify histories and are not API bases.

## Permanent completeness

In this example completeBefore is `1791288003000000`. At hasMore=false, all entries in the
selected range strictly before that bound have been returned across the pages.
No later acceptance can insert an entry below it, including after an empty result.
At or after the boundary, new entries remain possible. A later poll uses afterEntry
with the last known entry. A limit=0 query obtains only the checkpoint and makes no
claim that the caller already possesses its contents.
