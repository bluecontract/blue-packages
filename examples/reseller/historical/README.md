# Historical reseller fixtures

The reservation and payment examples exercise the earlier stored-quote
checkout and embedded Order factory. Reproduce those scenarios with the exact
retained Reseller preview.9 archive and its dependencies.

```sh
python3 tools/run_reseller.py \
  --reseller-archive retained/reseller-preview.9/clause-reseller/package.bluepkg \
  --source examples/reseller/historical/agreement.blue \
  --scenarios examples/reseller/historical/smoke.case.json \
  --output reports/reseller-historical/smoke
```

The older `preview-*.case.json` files record scenarios for the
embedded factory variants of the three preview agreements. Use their
matching historical agreement source for reproduction.

## Stored-quote bootstrap checks

Run the native component probes from the repository root with Java 21 in
`JAVA_HOME` and a qualified Core test classpath in `BLUE_JAVA_CLASSPATH`.

```sh
historical_report="$PWD/reports/reseller-historical/bootstrap"
mkdir -p "$historical_report/classes"
"$JAVA_HOME/bin/javac" -cp "$BLUE_JAVA_CLASSPATH" -d "$historical_report/classes" \
  tools/BootstrapPreparationConformance.java tools/CommissionHistoryConformance.java \
  examples/reseller/historical/tests/*.java &&
"$JAVA_HOME/bin/java" -Xmx1500m -cp "$historical_report/classes:$BLUE_JAVA_CLASSPATH" \
  BootstrapOrdersConformance "$PWD" "$historical_report"
```

The runner mounts the exact retained preview.9 archive. It covers fixed
child parties, customer substitution, the frozen quote and fulfilment
snapshot, and correlated retries. The `refresh-definition` case in
`tools/check_operation_inputs.py` checks the retained archive's emitted
refresh plan with the native Documents selector.
