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
    "blueId": "A3fAipLNZrLCPwwdZoXVMgmvNNGEEPCANwyUjd6iTv4x"
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
    "blueId": "A3fAipLNZrLCPwwdZoXVMgmvNNGEEPCANwyUjd6iTv4x"
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
    "blueId": "B8K1fuVQV3rQwxkPk38MtmSuLXK6MQDYexA5BcPhp2Jp"
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
      "blueId": "A3fAipLNZrLCPwwdZoXVMgmvNNGEEPCANwyUjd6iTv4x"
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


The document's initial BlueId is `7snCqm1ESL7HBuCpRUiF6U8SU6YYv1UN8UjU95s9xeHq`. Its public channel
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
    "blueId": "7snCqm1ESL7HBuCpRUiF6U8SU6YYv1UN8UjU95s9xeHq"
  },
  "channel": "provider",
  "operation": "update",
  "request": {
    "type": "Coordination/Timeline Access Update",
    "allowedTimelines": [
      {
        "blueId": "A3fAipLNZrLCPwwdZoXVMgmvNNGEEPCANwyUjd6iTv4x"
      },
      {
        "blueId": "FPHtFoyFWdFYBPpKNeTBW9ihgbenEF4ozB1w4ss9LiFF"
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
      "blueId": "A3fAipLNZrLCPwwdZoXVMgmvNNGEEPCANwyUjd6iTv4x"
    },
    {
      "blueId": "FPHtFoyFWdFYBPpKNeTBW9ihgbenEF4ozB1w4ss9LiFF"
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
    "blueId": "49WcAmiCcMDouWmQi38zFgD6nrZrLPSdRSwcg1DwKvDg"
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
    "blueId": "FMLpUzFTiLqEd5mcK1s7JbUr892wzPs7FTT128X6BjAN"
  },
  "object": {
    "type": "Coordination/Timeline Read Response",
    "request": {
      "blueId": "2zq2t4rcHe3xSCmiqKpVffUxxvsNHmbifFuCnhpwYQvC"
    },
    "checkpoint": {
      "type": "Coordination/Timeline Attestation",
      "timeline": {
        "blueId": "49WcAmiCcMDouWmQi38zFgD6nrZrLPSdRSwcg1DwKvDg"
      },
      "guarantee": {
        "type": "Coordination/Timeline Completeness Guarantee",
        "timeline": {
          "blueId": "49WcAmiCcMDouWmQi38zFgD6nrZrLPSdRSwcg1DwKvDg"
        },
        "completeBefore": 1791288003000000,
        "lastEntry": {
          "blueId": "FrfZ6MBZKcHRtoC81UhQ1ysNn4VyhdMYXuSKr5zf7Anj"
        }
      },
      "signature": "22eec7c97e74f03c4fa7ef501e35e00c78bf6e5351a877d2eb739259a17899b4b664b69efe90209f2cb4b90fa0a216bf05aaf78ae1397b78ef5ba70e9ac9c108"
    },
    "page": {
      "type": "Coordination/Timeline Entries Page",
      "timeline": {
        "blueId": "49WcAmiCcMDouWmQi38zFgD6nrZrLPSdRSwcg1DwKvDg"
      },
      "checkpoint": {
        "blueId": "CN1B6c59oxPmaA24TdXq61iSLFTUrGR1txhNaPaZhbgi"
      },
      "entries": [
        {
          "type": "Coordination/Timeline Entry",
          "timeline": {
            "blueId": "49WcAmiCcMDouWmQi38zFgD6nrZrLPSdRSwcg1DwKvDg"
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
                "blueId": "A3fAipLNZrLCPwwdZoXVMgmvNNGEEPCANwyUjd6iTv4x"
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
            "blueId": "49WcAmiCcMDouWmQi38zFgD6nrZrLPSdRSwcg1DwKvDg"
          },
          "timestamp": 1791288002500000,
          "actor": {
            "type": "Example/ACME Access Service",
            "serviceName": "ACME timeline access"
          },
          "message": {
            "type": "Contracts/Operation Request",
            "document": {
              "blueId": "7snCqm1ESL7HBuCpRUiF6U8SU6YYv1UN8UjU95s9xeHq"
            },
            "channel": "provider",
            "operation": "update",
            "request": {
              "type": "Coordination/Timeline Access Update",
              "allowedTimelines": [
                {
                  "blueId": "A3fAipLNZrLCPwwdZoXVMgmvNNGEEPCANwyUjd6iTv4x"
                },
                {
                  "blueId": "FPHtFoyFWdFYBPpKNeTBW9ihgbenEF4ozB1w4ss9LiFF"
                }
              ],
              "allowedKeys": [
                "a09aa5f47a6759802ff955f8dc2d2a14a5c99d23be97f864127ff9383455a4f0",
                "17cb79fb2b4120f2b1ec65e4198d6e08b28e813feb01e4a400839b85e18080ce"
              ]
            }
          },
          "prevEntry": {
            "blueId": "A9qi38eHhMYGhdUMkvbkjXS47xYrPXHXaGnHHtSr1Z7P"
          },
          "operation": {
            "blueId": "CdqJF57N9pkBAnj2fWGFNpyT46RwepC3q2ufGs3iHct8"
          }
        }
      ],
      "hasMore": false
    }
  },
  "signature": "f473eccd64f2f99964bf63990b3d9d80cae57233d8e23264ff9070cf8c3967df41b23337f4d890d14c036b11315728790c9ddb8305b947bb073c79454b57080d"
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
      "blueId": "A3fAipLNZrLCPwwdZoXVMgmvNNGEEPCANwyUjd6iTv4x"
    },
    "limit": 100
  },
  "publicKey": "a09aa5f47a6759802ff955f8dc2d2a14a5c99d23be97f864127ff9383455a4f0",
  "signature": "e4640a23a31f642bd1d21b7ef2f626f3e281d9faebb0052c4d77013a1136a8fe7fd76185752f2e0e687c1d35304df58ff313b7e401e5fbe544ef866f1199f204"
}
```

```json
{
  "type": "Coordination/Signed Reader Request",
  "request": {
    "type": "Coordination/Read Timeline Request",
    "timeline": {
      "blueId": "A3fAipLNZrLCPwwdZoXVMgmvNNGEEPCANwyUjd6iTv4x"
    },
    "limit": 100,
    "afterEntry": {
      "blueId": "B8K1fuVQV3rQwxkPk38MtmSuLXK6MQDYexA5BcPhp2Jp"
    }
  },
  "publicKey": "a09aa5f47a6759802ff955f8dc2d2a14a5c99d23be97f864127ff9383455a4f0",
  "signature": "a2ec5742cdb37bc660593dcb21456f2bf0339bcb3f7a4b5192f0ab88debcca5277ea3d0bfa1d7065525c677e5ee23731c02cda5bcf339f3e28633b5f8fd7b802"
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
    "blueId": "FMLpUzFTiLqEd5mcK1s7JbUr892wzPs7FTT128X6BjAN"
  },
  "object": {
    "type": "Coordination/Timeline Read Response",
    "request": {
      "blueId": "FAjoeuNo6YYQzXV7YbV4YkFNYUc5ZsyVcnKCSYVV75z1"
    },
    "checkpoint": {
      "type": "Coordination/Timeline Attestation",
      "timeline": {
        "blueId": "A3fAipLNZrLCPwwdZoXVMgmvNNGEEPCANwyUjd6iTv4x"
      },
      "guarantee": {
        "type": "Coordination/Timeline Completeness Guarantee",
        "timeline": {
          "blueId": "A3fAipLNZrLCPwwdZoXVMgmvNNGEEPCANwyUjd6iTv4x"
        },
        "completeBefore": 1791288003000000,
        "lastEntry": {
          "blueId": "Bb5KCVAM2PZztXnxuS62WSixaJtGTnLgDYdLtE87Hze2"
        }
      },
      "signature": "d7a8720a6e173a44eabf13df0c3075c43cd95aef420db0cd98087fddb7dca6b3933f21ab2c7b82146f6cc4d20a326fba305923e6226c1132695d9dfd3061d500"
    },
    "page": {
      "type": "Coordination/Timeline Entries Page",
      "timeline": {
        "blueId": "A3fAipLNZrLCPwwdZoXVMgmvNNGEEPCANwyUjd6iTv4x"
      },
      "checkpoint": {
        "blueId": "DMwsY98JHW7sBUMehb1ysXXLoLrGbA3V9tHL5Vyf5YCy"
      },
      "entries": [
        {
          "type": "Coordination/Timeline Entry",
          "timeline": {
            "blueId": "A3fAipLNZrLCPwwdZoXVMgmvNNGEEPCANwyUjd6iTv4x"
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
            "blueId": "A3fAipLNZrLCPwwdZoXVMgmvNNGEEPCANwyUjd6iTv4x"
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
            "blueId": "B8K1fuVQV3rQwxkPk38MtmSuLXK6MQDYexA5BcPhp2Jp"
          }
        }
      ],
      "hasMore": false
    }
  },
  "signature": "c8d9984d022d22648720c7c73913785db42e27851d7bc5e94d5424ad0d3d2a80dca72798bc28c3886f5931620ab515901b45dffe9c157599f9a8b4deea764f03"
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
