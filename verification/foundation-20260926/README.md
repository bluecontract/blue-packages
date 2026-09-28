# Evidence scope

Files named language-*, bex-test-final, bex-reference-tests-rerun, contracts-test-final, contracts-selected, contracts-demo-final, bex-demo, identity-and-source-checks and java-final-package-check were executed or calculated for this delivery.

`upstream-reported-enum-order.json` is copied from the uploaded project, not a new run here. Its algorithms remain unchanged; the defect is not claimed fixed.

`contracts-reference-tests-final.log` is an interrupted broad test run: seven tests passed before review stopped it after 221 seconds during a larger case. It is not full-suite qualification. Twelve targeted public event/processing tests were then run to completion against the new resource binding; those results are in contracts-selected.log. All original test source files remain included for later complete runs.

The BEX group deselects exactly one leaked module-level unittest factory helper named `test(self, e=...)`; the generated unittest methods remain collected. No failing semantic test is excluded. Initial collection failures caused by missing fixture-helper modules were repaired by copying the exact original support files, which are now in SOURCE-LOCK.json. A first cold replay used the author's lowercase alias at the receiving worker; the example now sends the exact event, as the wire contract requires. The final cold-replay run passes.

Java was freshly compiled from 46 `blue-language-core` production source files in the uploaded workspace using Java 21.0.11 and Jackson/SnakeYAML dependencies. No precompiled Blue classes were used. This checks native package verification and Language creation only; it does not register or execute the new Contracts protocol. Gradle/JUnit, performance benchmarks, GHCR, MyOS and browser integration were not rerun in this task.
