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
    "blueId": "2faiePGMsr9ewNxP3a5sJQaQ7vFPh9jJnHGtn8e9bbFd"
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
    "blueId": "2faiePGMsr9ewNxP3a5sJQaQ7vFPh9jJnHGtn8e9bbFd"
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
    "blueId": "21Tq8Lm9CiYQGcKH1DoZ9aSXVNwKpfqmaRkencrgxh3r"
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
      "blueId": "2faiePGMsr9ewNxP3a5sJQaQ7vFPh9jJnHGtn8e9bbFd"
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


The document's initial BlueId is `23YsAbVLpHEtvqjByFnDGVTvKCh96PWot2eiCusNJbCU`. Its public channel
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
    "blueId": "23YsAbVLpHEtvqjByFnDGVTvKCh96PWot2eiCusNJbCU"
  },
  "channel": "provider",
  "operation": "update",
  "request": {
    "type": "Coordination/Timeline Access Update",
    "allowedTimelines": [
      {
        "blueId": "2faiePGMsr9ewNxP3a5sJQaQ7vFPh9jJnHGtn8e9bbFd"
      },
      {
        "blueId": "2u3wcjzqAecTkHcNLmG4CpZydCVeEDCcYa1mmCbT29PF"
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
      "blueId": "2faiePGMsr9ewNxP3a5sJQaQ7vFPh9jJnHGtn8e9bbFd"
    },
    {
      "blueId": "2u3wcjzqAecTkHcNLmG4CpZydCVeEDCcYa1mmCbT29PF"
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
    "blueId": "2LUnB4Rk3oK8vUGwFxJqKiWKM2GGFfiqAzPJxt1B3XaU"
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
    "blueId": "FErdNdRjdxiE1wxvxMZKe8WcxJMop7xzkZxnJm5Q1AWC"
  },
  "object": {
    "type": "Coordination/Timeline Read Response",
    "request": {
      "blueId": "AYWJMoAc8sspRnBKkWWSN3g7ZvbdcfZfSmeM1iT9RpSZ"
    },
    "checkpoint": {
      "type": "Coordination/Timeline Attestation",
      "timeline": {
        "blueId": "2LUnB4Rk3oK8vUGwFxJqKiWKM2GGFfiqAzPJxt1B3XaU"
      },
      "guarantee": {
        "type": "Coordination/Timeline Completeness Guarantee",
        "timeline": {
          "blueId": "2LUnB4Rk3oK8vUGwFxJqKiWKM2GGFfiqAzPJxt1B3XaU"
        },
        "completeBefore": 1791288003000000,
        "lastEntry": {
          "blueId": "2gCyM1CAL5D3S9YQS75G5PrfWRcei1RZTt7FXezPcfLb"
        }
      },
      "signature": "574ff098a6ec191e797e1e877725627ecd56d5e6a261a83945cc50fc24abb8c308635184dab330802d2be8eda6321f871de987ab740ce41ed9e721371a011800"
    },
    "page": {
      "type": "Coordination/Timeline Entries Page",
      "timeline": {
        "blueId": "2LUnB4Rk3oK8vUGwFxJqKiWKM2GGFfiqAzPJxt1B3XaU"
      },
      "checkpoint": {
        "blueId": "Gvfrdu8QeuQhJZa8Sq9rjYDkaTEpHzLyiEGUjcBMYkRk"
      },
      "entries": [
        {
          "type": "Coordination/Timeline Entry",
          "timeline": {
            "blueId": "2LUnB4Rk3oK8vUGwFxJqKiWKM2GGFfiqAzPJxt1B3XaU"
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
                "blueId": "2faiePGMsr9ewNxP3a5sJQaQ7vFPh9jJnHGtn8e9bbFd"
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
            "blueId": "2LUnB4Rk3oK8vUGwFxJqKiWKM2GGFfiqAzPJxt1B3XaU"
          },
          "timestamp": 1791288002500000,
          "actor": {
            "type": "Example/ACME Access Service",
            "serviceName": "ACME timeline access"
          },
          "message": {
            "type": "Contracts/Operation Request",
            "document": {
              "blueId": "23YsAbVLpHEtvqjByFnDGVTvKCh96PWot2eiCusNJbCU"
            },
            "channel": "provider",
            "operation": "update",
            "request": {
              "type": "Coordination/Timeline Access Update",
              "allowedTimelines": [
                {
                  "blueId": "2faiePGMsr9ewNxP3a5sJQaQ7vFPh9jJnHGtn8e9bbFd"
                },
                {
                  "blueId": "2u3wcjzqAecTkHcNLmG4CpZydCVeEDCcYa1mmCbT29PF"
                }
              ],
              "allowedKeys": [
                "a09aa5f47a6759802ff955f8dc2d2a14a5c99d23be97f864127ff9383455a4f0",
                "17cb79fb2b4120f2b1ec65e4198d6e08b28e813feb01e4a400839b85e18080ce"
              ]
            }
          },
          "prevEntry": {
            "blueId": "8Xft8LyJEmc6xXsjhuiSvef7zbQLvBNksihTLE4phBTA"
          },
          "operation": {
            "blueId": "7GRbYEuKGjVqZt1h5qX7grddVnJZiezGvnHaBDaxaeHE"
          }
        }
      ],
      "hasMore": false
    }
  },
  "signature": "0dd31f72ade1d3daf6aabdfcf6096640e6c9ea2bbd7753ad61ca47a0112eec92d31e2329704065cac274cc01674a3cf6dcda03ff414e2fbbfcac36321bc90d03"
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
      "blueId": "2faiePGMsr9ewNxP3a5sJQaQ7vFPh9jJnHGtn8e9bbFd"
    },
    "limit": 100
  },
  "publicKey": "a09aa5f47a6759802ff955f8dc2d2a14a5c99d23be97f864127ff9383455a4f0",
  "signature": "421f1faac9c4e31461fee6907fda77e95f03ea41cb255c75ee35ccf5216a01bbda7b177e4990568451be133ad30af66d4275f45fd0052e037a741f1e591edb00"
}
```

```json
{
  "type": "Coordination/Signed Reader Request",
  "request": {
    "type": "Coordination/Read Timeline Request",
    "timeline": {
      "blueId": "2faiePGMsr9ewNxP3a5sJQaQ7vFPh9jJnHGtn8e9bbFd"
    },
    "limit": 100,
    "afterEntry": {
      "blueId": "21Tq8Lm9CiYQGcKH1DoZ9aSXVNwKpfqmaRkencrgxh3r"
    }
  },
  "publicKey": "a09aa5f47a6759802ff955f8dc2d2a14a5c99d23be97f864127ff9383455a4f0",
  "signature": "f7511891487c6c9763073be9799acf2531f099fd652a1733c1185697b0826d05a71b57440798e620f6a6a98aab8d611fdba0a661132ac3aaa30fad619938770b"
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
    "blueId": "FErdNdRjdxiE1wxvxMZKe8WcxJMop7xzkZxnJm5Q1AWC"
  },
  "object": {
    "type": "Coordination/Timeline Read Response",
    "request": {
      "blueId": "GcfDReFFPMafCwPS2wSuS4XkiHLkPsg7hTD7cdUJiTFe"
    },
    "checkpoint": {
      "type": "Coordination/Timeline Attestation",
      "timeline": {
        "blueId": "2faiePGMsr9ewNxP3a5sJQaQ7vFPh9jJnHGtn8e9bbFd"
      },
      "guarantee": {
        "type": "Coordination/Timeline Completeness Guarantee",
        "timeline": {
          "blueId": "2faiePGMsr9ewNxP3a5sJQaQ7vFPh9jJnHGtn8e9bbFd"
        },
        "completeBefore": 1791288003000000,
        "lastEntry": {
          "blueId": "HYjDcTAhBDYttnRqcwgrZRAFFnoYwDGaF6wSETVtSzy1"
        }
      },
      "signature": "ceb90bc664d0d93f2b2334ba3e19d3a0f03c3d4546f02f7dcf25b972555a207223db1f3675a70bd36219cc89b32c8b54eec8a7ef9edc8c91d80f224f71d7cb0d"
    },
    "page": {
      "type": "Coordination/Timeline Entries Page",
      "timeline": {
        "blueId": "2faiePGMsr9ewNxP3a5sJQaQ7vFPh9jJnHGtn8e9bbFd"
      },
      "checkpoint": {
        "blueId": "J1iwefw9hmCj9n9vG9LApG4FkMMTynSb4H6HqnWYiVLz"
      },
      "entries": [
        {
          "type": "Coordination/Timeline Entry",
          "timeline": {
            "blueId": "2faiePGMsr9ewNxP3a5sJQaQ7vFPh9jJnHGtn8e9bbFd"
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
            "blueId": "2faiePGMsr9ewNxP3a5sJQaQ7vFPh9jJnHGtn8e9bbFd"
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
            "blueId": "21Tq8Lm9CiYQGcKH1DoZ9aSXVNwKpfqmaRkencrgxh3r"
          }
        }
      ],
      "hasMore": false
    }
  },
  "signature": "4ebbac1c6197a65409ca5a6b160133767c426f21cb97c1a167123ff7fb47558e88311b9ffe67b6011ac7ca73267f32544f8490d2ac870a4c6c17c3406830640b"
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
