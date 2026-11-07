package blue.contracts;

import blue.bex.Engine;
import blue.language.next.Exact;
import java.util.Map;

/** Conformance-only adapter matching DocumentDispatchV1's raw dispatch binding. */
public final class RawDispatchEvaluation {
    private RawDispatchEvaluation() {}

    public static Engine.Result evaluate(Contracts processor, Exact host,
            Map<String, Object> dispatch, Map<String, Object> program, long limit) {
        var meter = new ContractModel.Meter(limit);
        var logical = new LogicalWork(processor.blue, meter);
        if (processor.bindings().contractsEdition().demandScoped())
            logical.obligations = new ContractObligations(logical);
        var context = new Engine.Context();
        context.document = processor.blue.requiredRootView(host, logical);
        context.bindings = Map.of("dispatch", dispatch);
        context.readDocument = (path, view, document) -> document instanceof Exact exact
                ? logical.read(exact, path.equals("/") ? "" : path)
                : processor.blue.readBex(document, path);
        context.matcher = (value, pattern) -> processor.blue.matches(value, pattern, logical);
        context.nodeBlueId = logical::nodeBlueId;
        return processor.bex.execute(program, context, meter);
    }
}
