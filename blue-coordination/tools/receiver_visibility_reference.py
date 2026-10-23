"""Finite receiver-relative activation rules; authentication remains native-owned.

Distinct timestamp inputs deliberately do not qualify full-K tie ordering. Each
phase retains its installing source time A, propagates max causal visibility V,
and uses the original source input time for authority. A terminal decision can
advance only the exact member/channel/generation lifetime that examined it.
"""


def derive_visibility(data):
    phases = {}
    rows = []
    for phase in data["installations"]:
        parent = phase.get("parent")
        if parent is not None and parent not in phases:
            raise ValueError("missing causal predecessor")
        scan = phase["installTime"]
        visibility = max(scan, phases[parent]["visibility"] if parent else scan)
        phases[phase["channel"]] = {"scan": scan, "visibility": visibility}
        rows.append({"channel": phase["channel"], "scan": scan,
                     "visibility": visibility})
    selected = phases[data["selectedChannel"]]
    original = data["inputTime"]
    terminal = data["terminal"]
    selected_lifetime = data["selectedLifetime"]
    eligible = original < selected["scan"]
    terminal_applies = (terminal["lifetime"] == selected_lifetime
                        and terminal["time"] < selected["scan"])
    return {"phases": rows, "originalInputTime": original,
            "eligibleBeforeScan": eligible,
            "genuinePrefixAccepted": eligible,
            "foreignTerminalCursorAccepted": terminal_applies,
            "visibleBeforeInstallation": data["observationTime"] >= selected["visibility"]}
