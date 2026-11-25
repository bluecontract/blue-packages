# Marigold Print Shop direct sale

Marigold Print Shop sells finished print goods for collection at its counter. The buyer deals with the shop, and the shop confirms the Order. The Payment Instruction names the shop as payee and uses a test guarantor.

| Catalogue item | Unit price | Quantity in the example | Line total |
|---|---:|---:|---:|
| Botanical poster | USD 18.50 | 2 | USD 37.00 |
| Five illustrated postcards, sold as one boxed set | USD 6.75 | 1 | USD 6.75 |
| **Total** | | | **USD 43.75** |

[print-shop.blue](print-shop.blue) holds the catalogue, Order template and Payment Instruction template. [basket.yaml](basket.yaml) supplies the catalogue revision, line selections and buyer email. The catalogue's optional `quoteBasket` workflow saves an immutable quote. The fixture calls it to verify the price independently. `prepareOrder` takes the same catalogue selections and freezes the server-computed price in the new Order requirement.

The native run prepared and provisioned an independent Order and Payment Instruction. Core checked that the selected instruction referenced the exact Order origin and matched its USD 43.75 total. The signed guarantor secured USD 43.75 while the Order awaited shop approval. Shop approval triggered one capture request for the same amount. The guarantor confirmed completion, which the Order observed. Repeating the quote, basket preparation and capture callback preserved one quote, one original Order requirement and one completed capture. A basket above the six-poster line cap and one with a stale catalogue revision were both rejected. [Native assertions](VerifyDirectSale.java)

The local fixture supplies timeline access, account bindings and guarantor reader keys. Its in-process Timeline Provider signs the inputs and delivers them to one in-memory Core tenant. The source placeholders `GUARANTOR_READER_KEY` and `marigold-test-payment-account` identify fixture bindings. Financial outcomes are submitted on the guarantor's signed channel. This exercise uses the MyOS Test Customer Payment Instruction and moves no money.

## Run the native check

The [reproduction instructions](../README.md#run-the-three-checks) show how to
generate the runtime classpath and launch [the verifier](verify.sh). It writes
a JSON report to the supplied path. Core checks each mounted archive's
checksum and BlueId. The fixture generates local channels and keys, so runtime
document identifiers can differ between runs.
