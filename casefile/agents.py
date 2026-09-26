"""The three specialists. Each takes typed input and returns a typed message; each could be an
LLM behind a JSON-schema contract (see llm.py), and here is a deterministic implementation so
every run is reproducible. Tools (the prior-claims lookup) can fail, as real ones do."""
import random
import re

from .claims import LABOUR_RATE, PARTS
from .messages import Extracted, Findings, Review

OVERPRICED = 1.5            # charged above 1.5x the reference is flagged


def num(pattern, text, default=None, cast=float):
    m = re.search(pattern, text)
    return cast(m.group(1)) if m else default


def extractor(docs, strict=False):
    """Fields from the claim packet. strict: compute the total from the estimate's lines instead of trusting its Total."""
    fnol, pol, est = docs.get("fnol", ""), docs.get("policy", ""), docs.get("estimate")
    parts = [(p, float(c)) for p, c in re.findall(r"Part: ([a-z ]+?) (\d+\.\d+)", est or "")]
    hours, rate = num(r"Labour: (\d+(?:\.\d+)?) hours", est or "", 0.0), num(r"hours at (\d+(?:\.\d+)?)", est or "", 0.0)
    total = None if est is None else (round(sum(c for _, c in parts) + hours * rate, 2) if strict else num(r"Total: (\d+(?:\.\d+)?)", est))
    return Extracted(num(r"Policy (POL-\d+)", fnol, "", str), num(r"Vehicle (\w+ \w+)", fnol, "", str),
                     num(r"Date of loss ([\d-]+)", fnol, "", str), num(r"Start ([\d-]+)", pol, "", str),
                     num(r"End ([\d-]+)", pol, "", str), num(r"Limit (\d+(?:\.\d+)?)", pol, 0.0), num(r"Excess (\d+(?:\.\d+)?)", pol, 0.0),
                     parts, hours, rate, total, [] if est is not None else ["estimate"])


def prior_claims_tool(claim, attempt, failure_rate=0.2):
    """The claims system's history lookup; times out now and then (seeded, so replays match)."""
    if random.Random(f"{claim.id}:lookup:{attempt}").random() < failure_rate:
        raise TimeoutError("claims system did not answer")
    return claim.prior_claims


def investigator(ext, claim, attempt):
    checked, duplicate = ["coverage", "limit", "pricing"], False
    try:
        history = prior_claims_tool(claim, attempt)
        duplicate = any(h["date"] == ext.loss_date and h["policy"] == ext.policy for h in history)
        checked.append("duplicate")
    except TimeoutError:
        pass
    covered = ext.policy_start <= ext.loss_date <= ext.policy_end
    within = ext.total is None or ext.total - ext.excess <= ext.limit
    over = [(p, c, PARTS[p]) for p, c in ext.parts if p in PARTS and c > OVERPRICED * PARTS[p]]
    if ext.labour_rate > OVERPRICED * LABOUR_RATE:
        over.append(("labour rate", ext.labour_rate, LABOUR_RATE))
    return Findings(covered, within, duplicate, over, checked)


def reviewer(ext, findings):
    """Sends work back when it cannot be trusted yet; passes it on otherwise."""
    if ext.total is not None:
        lines = round(sum(c for _, c in ext.parts) + ext.labour_hours * ext.labour_rate, 2)
        if abs(lines - ext.total) > 1:
            return Review(False, "extractor", [f"estimate lines add up to {lines:.2f}, stated total {ext.total:.2f}"])
    if "duplicate" not in findings.checked:
        return Review(False, "investigator", ["prior-claims check did not run"])
    return Review(True)
