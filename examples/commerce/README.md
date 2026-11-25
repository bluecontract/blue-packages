# Commercial agreements with the Catalog Clause

`Commerce/Catalog Clause` prices a selection against one supplier, currency and
catalogue revision. A saved quote records the priced lines, total, revision and
catalogue identity. Each agreement uses clause parameters and bindings to
determine who can request a quote, how prices change and whether the transaction
continues to an Order. [Catalog Clause](../../clause-commerce/types/catalog-clause.blue)

| Agreement | Result of the native check | Source and assertions |
| --- | --- | --- |
| Marigold Print Shop direct sale | Two posters and a postcard set produce a USD 43.75 Order. The shop's approval triggers one capture request. The Order observes the test guarantor's confirmed USD 43.75 capture. | [Walkthrough](direct-sale/README.md) · [Agreement](direct-sale/print-shop.blue) · [Basket](direct-sale/basket.yaml) · [Assertions](direct-sale/VerifyDirectSale.java) |
| Rivermill Packaging and Alder Street Café | A restock quote retains its EUR 97.00 price on revision 1. After both parties approve a catalogue amendment, the same basket gets a fresh EUR 104.50 quote on revision 2. | [Walkthrough](b2b-supply/README.md) · [Agreement](b2b-supply/cafe-supply-agreement.blue) · [Inputs and expectations](b2b-supply/operations.yaml) · [Assertions](b2b-supply/VerifyCafeSupply.java) |
| Harbor Arts event purchasing | The studio quotes EUR 300 and the caterer quotes EUR 162 for the same event key. Each quote retains its own supplier and lines. | [Agreement](event-supplier-quotes/agreement.blue) · [Inputs and expectations](event-supplier-quotes/event-supplier-quotes.case.yaml) · [Native runner](verification/RunCatalogueCase.java) |

## Pricing one event with two suppliers

Harbor Arts, North Room and Field Kitchen approve one agreement. It binds a
separate Catalog instance to each supplier's rates and quote collection. The
organizer uses `quoteStudio` and `quoteCatering` to save quotes for
`spring-concert` on 20 March 2027. The studio charges EUR 75 per hour for the
requested four-hour slot. Twelve boxed lunches at EUR 15 each receive a
10% discount. The eight-input case checks activation, separate quotes, rejection
of a catering item through the studio operation, rejection of a three-hour
studio selection, and a retry that emits no second quote event. It replays the
inputs to verify the same document outcome. [Case](event-supplier-quotes/event-supplier-quotes.case.yaml)

## Run the three checks

Use an ordinary checkout of Blue Packages containing this directory and its
checked-in [package catalogue and archives](../../PACKAGES.json). The qualified
catalogue SHA-256 is
`cbacbbfd235545505195d701c9ae8daee59e8220a490adeb5def4304d134f5b9`.
The runtime checks hashes and identities of the archives it mounts.

Set `JAVA_HOME` to a Java 21 JDK. In a separate MyOS Core checkout at the
[qualified revision](https://github.com/bluecontract/myos-core/tree/5a025dd4e95f2b020b7f16c754b565fc97d5ebe4),
generate the runtime and Core test classpath. Set `CORE_CHECKOUT` to the
absolute path of that checkout.

```sh
(cd "$CORE_CHECKOUT" && bash runtime/gradlew -p runtime :blue-core-service:writeHttpQualificationClasspath)
export BLUE_JAVA_CLASSPATH="$(cat "$CORE_CHECKOUT/reports/core-http-test-classpath.txt")"
```

From the Blue Packages repository root, run the checks in order. The temporary
directory holds generated reports and can be removed after inspection.

```sh
output_dir=$(mktemp -d)

bash examples/commerce/direct-sale/verify.sh "$output_dir/direct-sale.json"
"$JAVA_HOME/bin/java" -Xmx1200m -cp "$BLUE_JAVA_CLASSPATH" \
  examples/commerce/b2b-supply/VerifyCafeSupply.java "$PWD" examples/commerce/b2b-supply \
  > "$output_dir/b2b-supply.json"
bash examples/commerce/verification/run-case.sh \
  examples/commerce/event-supplier-quotes/event-supplier-quotes.case.yaml "$output_dir/event"
```

Expect `PASS` in `direct-sale.json` and `b2b-supply.json`. The event runner
writes its per-step journal, replay status and result to the `event` directory.
The direct-sale check uses signed inputs in a local in-memory Core tenant and a
simulated payment provider. It moves no money. The other two checks use local
native execution and end at saved quotes.
