"""Synthetic auto claims. Real claim files are private, so each claim packet (a first notice
of loss, a policy summary, a repair estimate) is generated from a seed, with the problems an
adjuster looks for planted in known claims: an estimate above the policy limit, a lapsed
policy, labour or parts priced far above the reference, a duplicate of a prior claim, a
missing estimate. The planted problems are the answer key."""
import random
from dataclasses import dataclass, field

PARTS = {"front bumper": 450, "rear bumper": 420, "headlamp": 310, "bonnet": 620, "door panel": 540, "wing mirror": 180,
         "windscreen": 380, "radiator": 290, "alloy wheel": 260, "tail lamp": 150}
LABOUR_RATE = 62.0          # reference labour rate per hour
ISSUES = ("over_limit", "lapsed_policy", "inflated_estimate", "duplicate_claim", "missing_estimate")


@dataclass
class Claim:
    id: str
    documents: dict                      # name -> text
    prior_claims: list                   # the claims system's history for this policy
    planted: set = field(default_factory=set)


def make(i, seed=0):
    rng = random.Random(f"{seed}:{i}")
    planted = {x for x in ISSUES if rng.random() < 0.12}
    policy, reg = f"POL-{rng.randint(100000, 999999)}", f"{rng.choice('ABCDEFGH')}{rng.randint(10, 99)} {rng.choice('XYZ')}{rng.choice('KLMN')}{rng.choice('PRST')}"
    day = rng.randint(1, 28)
    start = f"2025-{rng.randint(1, 6):02d}-{day:02d}"
    end = f"2025-{rng.randint(1, 3):02d}-{day:02d}" if "lapsed_policy" in planted else f"2026-{rng.randint(6, 12):02d}-{day:02d}"
    loss = f"2025-{rng.randint(7, 9):02d}-{rng.randint(1, 28):02d}"
    parts = rng.sample(sorted(PARTS), rng.randint(1, 4))
    markup = 2.4 if "inflated_estimate" in planted else rng.uniform(0.85, 1.15)
    lines = [(p, round(PARTS[p] * markup * rng.uniform(0.95, 1.05), 2)) for p in parts]
    hours = round(rng.uniform(2, 9), 1)
    rate = round(LABOUR_RATE * (markup if "inflated_estimate" in planted else rng.uniform(0.9, 1.1)), 2)
    total = round(sum(c for _, c in lines) + hours * rate, 2)
    stated = round(total + rng.choice([-90, 90, 180]), 2) if rng.random() < 0.15 else total    # a garage's arithmetic slip
    payable = total - 250                                  # the excess comes off first
    limit = max(100.0, round(payable * rng.uniform(0.4, 0.8), -2)) if "over_limit" in planted else round(total * rng.uniform(2, 6), -2) + 1000
    if payable <= limit:
        planted.discard("over_limit")                      # too small a claim to be over any limit
    fnol = (f"First notice of loss. Policy {policy}. Vehicle {reg}. Date of loss {loss}. "
            f"The insured reports {rng.choice(['a rear-end collision at a junction', 'a low-speed impact in a car park', 'a collision with a bollard'])}; "
            f"damage to the {', '.join(parts)}.")
    policy_doc = f"Policy {policy}. Cover: comprehensive. Start {start}. End {end}. Limit {limit:.2f}. Excess 250.00."
    estimate = ("Repair estimate for " + reg + ".\n" + "\n".join(f"Part: {p} {c:.2f}" for p, c in lines)
                + f"\nLabour: {hours} hours at {rate:.2f}\nTotal: {stated:.2f}")
    docs = {"fnol": fnol, "policy": policy_doc}
    if "missing_estimate" not in planted:
        docs["estimate"] = estimate
    prior = [{"policy": policy, "date": loss, "parts": parts}] if "duplicate_claim" in planted else \
        [{"policy": policy, "date": f"2024-{rng.randint(1, 12):02d}-{rng.randint(1, 28):02d}", "parts": rng.sample(sorted(PARTS), 1)}] * (rng.random() < 0.3)
    return Claim(f"CLM-{i:04d}", docs, prior, planted)
