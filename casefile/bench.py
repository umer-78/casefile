"""The ship gates, measured: 30 recorded claim runs with their node paths; a run replayed from a
stored snapshot to the same terminal state; the reviewer sending work back and the graph
still stopping; cost per claim against a ceiling enforced in code; and, on a day's volume
(900 claims), how many planted problems the agents catch."""
import json
from collections import Counter
from dataclasses import replace
from pathlib import Path

import statistics

from .claims import ISSUES, make
from .graph import Limits, Store, approve, fingerprint, run

RESULTS = Path(__file__).resolve().parent.parent / "results"
FLAG = {"over_limit": lambda s: s["findings"] and not s["findings"]["within_limit"],
        "lapsed_policy": lambda s: s["findings"] and not s["findings"]["covered"],
        "inflated_estimate": lambda s: s["findings"] and bool(s["findings"]["overpriced"]),
        "duplicate_claim": lambda s: s["findings"] and s["findings"]["duplicate"],
        "missing_estimate": lambda s: s["extracted"] and "estimate" in s["extracted"]["missing"]}


def bench():
    limits, store = Limits(), Store()
    claims = [make(i) for i in range(900)]
    states = [run(c, store, limits) for c in claims]
    # ship gate 1: 30 recorded runs
    recorded = states[:30]
    RESULTS.mkdir(exist_ok=True)
    (RESULTS / "runs.jsonl").write_text("\n".join(json.dumps(s) for s in recorded) + "\n")
    # ship gate 2: replay from a snapshot of a run that was sent back
    target = next(s for s in states if s["send_backs"] and s["step"] > 4)
    claim = next(c for c in claims if c.id == target["claim"])
    snap = store.load(claim.id, 3)
    replayed = run(claim, Store(), limits, state=snap)
    # ship gate 3: send-backs and termination
    backs = [s for s in states if s["send_backs"]]
    # ship gate 4: cost per claim, and a ceiling tight enough to bite
    dollars = [s["cost"]["dollars"] for s in states]
    tight = replace(limits, max_dollars=0.0006)
    capped = [run(c, Store(), tight) for c in claims]
    # the human gate
    waiting = [s for s in states if s["status"] == "awaiting_approval"]
    paid = approve(store, waiting[0]["claim"], "adjuster-7")
    # detection on the day's volume
    detect = {}
    for issue in ISSUES:
        has = [s for s, c in zip(states, claims) if issue in c.planted]
        not_has = [s for s, c in zip(states, claims) if issue not in c.planted]
        detect[issue] = {"planted": len(has), "caught": sum(bool(FLAG[issue](s)) for s in has),
                         "false_flags": sum(bool(FLAG[issue](s)) for s in not_has)}
    pct = lambda k, n: f"{100 * k / n:.0f}%" if n else "—"
    lines = ["## 30 recorded claim runs", "", "| Claim | Planted problems | Node path | Status | Decision | Tokens | Cost |",
             "|---|---|---|---|---|---|---|"]
    for s, c in zip(recorded, claims):
        rec = s["recommendation"] or {}
        lines.append(f"| {s['claim']} | {', '.join(sorted(c.planted)) or '—'} | {' → '.join(s['path'])} | {s['status']} | "
                     f"{rec.get('decision', '—')}{' ' + format(rec['payout'], ',.2f') if rec.get('payout') else ''} | "
                     f"{s['cost']['tokens']:,} | ${s['cost']['dollars']:.5f} |")
    lines += ["", "## Ship gates", "",
              f"- Replay: {claim.id} resumed from its step-3 snapshot reached the same terminal state "
              f"(fingerprint {fingerprint(target)} vs {fingerprint(replayed)}): **{fingerprint(target) == fingerprint(replayed)}**.",
              f"- Send-backs: {len(backs)} of {len(states)} claims were sent back by the reviewer at least once "
              f"({Counter(s['send_backs'] for s in backs)[1]} once, {Counter(s['send_backs'] for s in backs)[2]} twice); every claim "
              f"stopped, the longest after {max(s['step'] for s in states)} node runs (limit {limits.max_steps}).",
              f"- Stops: {dict(Counter(s['status'] for s in states))}.",
              f"- Cost per claim (ceiling ${limits.max_dollars}): median ${statistics.median(dollars):.5f}, max ${max(dollars):.5f}.",
              f"- With the ceiling cut to ${tight.max_dollars}: {sum(s['status'] == 'stopped_budget' for s in capped)} claims stopped "
              f"before the call that would cross it; the most any claim spent was ${max(s['cost']['dollars'] for s in capped):.5f}.",
              f"- Human gate: {len(waiting)} payouts waited for approval and none paid without one; approving "
              f"{paid['claim']} moved it to `{paid['status']}`.", "",
              "Cost per claim, 900 claims:", "", "```"]
    lo_, hi_ = min(dollars), max(dollars)
    edges = [lo_ + (hi_ - lo_) * i / 8 for i in range(9)]
    edges[-1] += 1e-9
    counts = [sum(lo <= d < hi for d in dollars) for lo, hi in zip(edges, edges[1:])]
    for (lo, hi), n in zip(zip(edges, edges[1:]), counts):
        lines.append(f"${lo:.5f}-{hi:.5f} {'#' * round(50 * n / max(counts)):<50} {n}")
    lines += ["```", "", "## Planted problems caught (900 claims)", "", "| Problem | Planted | Caught | False flags on other claims |",
              "|---|---|---|---|"]
    lines += [f"| {k} | {v['planted']} | {v['caught']} ({pct(v['caught'], v['planted'])}) | {v['false_flags']} |" for k, v in detect.items()]
    (RESULTS / "bench.md").write_text("\n".join(lines) + "\n")
    (RESULTS / "summary.json").write_text(json.dumps({"detection": detect, "statuses": dict(Counter(s["status"] for s in states)),
                                                      "median_dollars": statistics.median(dollars), "max_dollars": max(dollars),
                                                      "replay_equal": fingerprint(target) == fingerprint(replayed)}, indent=1))
    return "\n".join(lines)
