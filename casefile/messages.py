"""Typed handoffs: what each agent may pass to the next. No free text travels between nodes;
every message is one of these, validated on construction."""
from dataclasses import dataclass, field

DECISIONS = ("approve", "deny", "refer")


@dataclass
class Extracted:
    policy: str
    vehicle: str
    loss_date: str
    policy_start: str
    policy_end: str
    limit: float
    excess: float
    parts: list                       # [(part, price)]
    labour_hours: float
    labour_rate: float
    total: float = None               # None when there is no estimate
    missing: list = field(default_factory=list)

    def __post_init__(self):
        if self.total is not None and self.total < 0:
            raise ValueError("negative total")


@dataclass
class Findings:
    covered: bool
    within_limit: bool
    duplicate: bool
    overpriced: list                  # [(item, charged, reference)]
    checked: list                     # which checks ran


@dataclass
class Review:
    ok: bool
    send_back_to: str = ""            # "extractor" or "investigator" when not ok
    reasons: list = field(default_factory=list)


@dataclass
class Recommendation:
    decision: str
    payout: float
    reasons: list

    def __post_init__(self):
        if self.decision not in DECISIONS:
            raise ValueError(f"unknown decision {self.decision}")
        if self.decision != "approve" and self.payout:
            raise ValueError("only an approval pays out")
