"""python -m casefile.demo   write the live demo's data (docs/data.json): the bench's 30 recorded claims, each
with its documents, planted problems (the answer key) and the whole claim state after every step, so the
page can step through a run; plus results/summary.json. The claims are synthetic, made by casefile.claims."""
import json
from pathlib import Path

from .claims import make
from .graph import Limits, Store, fingerprint, run

ROOT = Path(__file__).resolve().parent.parent


def build(out=ROOT / "docs", n=30):
    summary = json.loads((ROOT / "results" / "summary.json").read_text())
    recorded = [json.loads(line) for line in (ROOT / "results" / "runs.jsonl").read_text().splitlines() if line]
    claims = []
    for i in range(n):
        claim, store = make(i), Store()
        final = run(claim, store, Limits())
        if fingerprint(final) != fingerprint(recorded[i]):
            raise SystemExit(f"{claim.id} did not replay to its recorded state")
        steps = [json.loads(s) for (s,) in store.db.execute("SELECT state FROM snapshots WHERE claim = ? ORDER BY step", (claim.id,))]
        claims.append({"id": claim.id, "documents": claim.documents, "prior_claims": claim.prior_claims, "planted": sorted(claim.planted),
                       "steps": steps})
    out.mkdir(exist_ok=True)
    (out / "data.json").write_text(json.dumps({"summary": summary, "limits": Limits().__dict__, "claims": claims}, indent=1))
    print(f"wrote {out / 'data.json'}: {len(claims)} claims, all replayed to their recorded states")


if __name__ == "__main__":
    build()
