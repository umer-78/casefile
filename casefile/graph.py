"""The supervisor: a hand-rolled state machine over the specialists, with every stop condition
written down.

Path: extractor -> investigator -> reviewer -> (back to extractor or investigator when the
reviewer says so) -> recommend -> gate. It stops when any of these holds:
- the recommendation reaches the gate: a payout waits for a human (`awaiting_approval`),
  anything else is decided (`decided`);
- `max_steps` node runs (`stopped_max_steps`), or more than `max_send_backs` returns
  (`stopped_review_loop`);
- the next node's metered cost would cross the claim's token or dollar ceiling
  (`stopped_budget`). The check runs before the call and reserves the node's maximum output
  (the max_tokens a model call gets; a longer output is a contract violation), so spend can
  never cross the ceiling.
Every step writes the whole claim state to the store, so any run resumes from any snapshot.
"""
import hashlib
import json
import sqlite3
import time
from dataclasses import asdict, dataclass

from . import agents
from .messages import Extracted, Findings, Recommendation, Review

SYSTEM_TOKENS = 350                  # each node's instructions, metered as a model would be
MAX_OUT = {"extractor": 300, "investigator": 150, "reviewer": 80, "recommend": 150}   # each node's max_tokens


@dataclass
class Limits:
    max_steps: int = 10
    max_send_backs: int = 2
    max_tokens: int = 9000
    max_dollars: float = 0.002
    price_in: float = 0.15 / 1e6     # dollars per token, a small-model tier
    price_out: float = 0.60 / 1e6


def tokens(obj):
    return max(1, len(json.dumps(obj, default=str)) // 4)


class Store:
    def __init__(self, path=":memory:"):
        self.db = sqlite3.connect(path)
        self.db.executescript("""CREATE TABLE IF NOT EXISTS snapshots (claim TEXT, step INTEGER, state TEXT, PRIMARY KEY (claim, step));
                                 CREATE TABLE IF NOT EXISTS approvals (claim TEXT PRIMARY KEY, approver TEXT, decision TEXT, at REAL);""")

    def save(self, state):
        self.db.execute("INSERT OR REPLACE INTO snapshots VALUES (?, ?, ?)", (state["claim"], state["step"], json.dumps(state)))
        self.db.commit()

    def load(self, claim, step=None):
        q = "SELECT state FROM snapshots WHERE claim = ?" + (" AND step = ?" if step is not None else " ORDER BY step DESC LIMIT 1")
        row = self.db.execute(q, (claim, step) if step is not None else (claim,)).fetchone()
        return json.loads(row[0]) if row else None


def fingerprint(state):
    return hashlib.sha256(json.dumps({k: state[k] for k in ("status", "path", "recommendation", "cost")}, sort_keys=True)
                          .encode()).hexdigest()[:16]


def new_state(claim):
    return {"claim": claim.id, "step": 0, "node": "extractor", "status": "running", "strict": False, "lookups": 0,
            "send_backs": 0, "extracted": None, "findings": None, "review": None, "recommendation": None,
            "cost": {"tokens": 0, "dollars": 0.0}, "path": []}


def recommend(ext, f):
    reasons = []
    if "estimate" in ext.missing:
        return Recommendation("refer", 0.0, ["no repair estimate: request one"])
    if not f.covered:
        return Recommendation("deny", 0.0, [f"loss on {ext.loss_date} is outside the policy ({ext.policy_start} to {ext.policy_end})"])
    if f.duplicate:
        return Recommendation("refer", 0.0, ["a prior claim on this policy has the same date of loss"])
    if f.overpriced:
        return Recommendation("refer", 0.0, [f"{i} charged {c:.2f} against a reference of {r:.2f}" for i, c, r in f.overpriced])
    payout = ext.total - ext.excess
    if not f.within_limit:
        reasons.append(f"claimed {payout:.2f} exceeds the limit; capped at {ext.limit:.2f}")
        payout = ext.limit
    return Recommendation("approve", round(payout, 2), reasons + ["covered, priced in line, no duplicate"])


def step(state, claim, limits):
    """Run the next node; return False once the claim has stopped."""
    node = state["node"]
    if state["step"] >= limits.max_steps:
        state["status"] = "stopped_max_steps"
        return False
    inputs = {"extractor": claim.documents, "investigator": state["extracted"],
              "reviewer": [state["extracted"], state["findings"]], "recommend": [state["extracted"], state["findings"]]}[node]
    t_in = SYSTEM_TOKENS + tokens(inputs)
    projected_t = state["cost"]["tokens"] + t_in + MAX_OUT[node]
    projected_d = state["cost"]["dollars"] + t_in * limits.price_in + MAX_OUT[node] * limits.price_out
    if projected_t > limits.max_tokens or projected_d > limits.max_dollars:
        state["status"] = "stopped_budget"
        return False
    ext = Extracted(**state["extracted"]) if state["extracted"] else None
    if node == "extractor":
        out = agents.extractor(claim.documents, state["strict"])
        state["extracted"], state["node"] = asdict(out), "investigator"
    elif node == "investigator":
        state["lookups"] += 1
        out = agents.investigator(ext, claim, state["lookups"])
        state["findings"], state["node"] = asdict(out), "reviewer"
    elif node == "reviewer":
        out = agents.reviewer(ext, Findings(**state["findings"]))
        state["review"] = asdict(out)
        if out.ok:
            state["node"] = "recommend"
        elif state["send_backs"] >= limits.max_send_backs:
            state["status"] = "stopped_review_loop"
        else:
            state["send_backs"] += 1
            state["strict"] = state["strict"] or out.send_back_to == "extractor"
            state["node"] = out.send_back_to
    else:
        out = recommend(ext, Findings(**state["findings"]))
        state["recommendation"] = asdict(out)
        state["status"] = "awaiting_approval" if out.decision == "approve" else "decided"
    t_out = tokens(asdict(out))
    if t_out > MAX_OUT[node]:
        raise RuntimeError(f"{node} returned {t_out} tokens, over its {MAX_OUT[node]}-token contract")
    state["cost"]["tokens"] += t_in + t_out
    state["cost"]["dollars"] = round(state["cost"]["dollars"] + t_in * limits.price_in + t_out * limits.price_out, 8)
    state["path"].append(node)
    state["step"] += 1
    return state["status"] == "running"


def run(claim, store, limits=Limits(), state=None):
    """Run a claim to a stop, from the start or from a snapshot's state."""
    state = state or new_state(claim)
    store.save(state)
    while step(state, claim, limits):
        store.save(state)
    store.save(state)
    return state


def approve(store, claim_id, approver, decision="approve"):
    """The human gate: only this writes a payout decision back."""
    state = store.load(claim_id)
    if state is None or state["status"] != "awaiting_approval":
        raise ValueError(f"{claim_id} is not waiting for approval")
    store.db.execute("INSERT OR REPLACE INTO approvals VALUES (?, ?, ?, ?)", (claim_id, approver, decision, time.time()))
    state["status"] = "paid" if decision == "approve" else "rejected_by_human"
    state["step"] += 1
    store.save(state)
    store.db.commit()
    return state
