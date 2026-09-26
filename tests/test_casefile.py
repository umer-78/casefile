from dataclasses import replace

import pytest

from casefile.claims import make
from casefile.graph import Limits, Store, approve, fingerprint, run
from casefile.messages import Recommendation


def find(pred, n=400):
    return next(c for c in map(make, range(n)) if pred(c))


def test_claims_are_reproducible_and_the_answer_key_holds():
    assert make(7).documents == make(7).documents
    for c in map(make, range(300)):
        if "over_limit" in c.planted and "missing_estimate" not in c.planted:     # without an estimate it can't be known
            s = run(c, Store())
            assert s["findings"] is None or not s["findings"]["within_limit"]


def test_reviewer_sends_back_and_the_graph_still_stops():
    slipped = find(lambda c: "estimate" in c.documents and not c.planted and
                   abs(float(c.documents["estimate"].rsplit("Total: ", 1)[1]) -
                       sum(float(l.rsplit(" ", 1)[1]) for l in c.documents["estimate"].splitlines() if l.startswith("Part:"))
                       - eval(c.documents["estimate"].split("Labour: ")[1].split("\n")[0].replace(" hours at ", "*"))) > 1)
    s = run(slipped, Store())
    assert s["path"][:4] == ["extractor", "investigator", "reviewer", "extractor"] and s["status"] != "running"


def test_replay_from_a_snapshot_reaches_the_same_end():
    claim, store = make(3), Store()
    first = run(claim, store)
    again = run(claim, Store(), state=store.load(claim.id, 2))
    assert fingerprint(first) == fingerprint(again)


def test_ceilings_and_step_limit_are_enforced_by_code():
    claim = make(3)
    tight = run(claim, Store(), replace(Limits(), max_dollars=0.0002))
    assert tight["status"] == "stopped_budget" and tight["cost"]["dollars"] <= 0.0002
    short = run(claim, Store(), replace(Limits(), max_steps=2))
    assert short["status"] == "stopped_max_steps" and len(short["path"]) == 2


def test_no_payout_without_a_human():
    claim = find(lambda c: not c.planted)
    store = Store()
    state = run(claim, store)
    if state["status"] == "awaiting_approval":
        assert approve(store, claim.id, "adjuster-1")["status"] == "paid"
    with pytest.raises(ValueError):
        approve(store, claim.id, "adjuster-1")
    with pytest.raises(ValueError):
        Recommendation("deny", 100.0, [])
