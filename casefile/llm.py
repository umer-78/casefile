"""An LLM specialist behind the same typed contract: the extractor as a model call that must
return JSON matching `Extracted`, capped at the node's max_tokens so the budget check holds.
Pluggable; not measured in this repository (it runs without API keys)."""
import json
import urllib.request
from dataclasses import fields

from .graph import MAX_OUT
from .messages import Extracted

SCHEMA = {f.name: str(f.type) for f in fields(Extracted)}


def llm_extractor(model, base_url, api_key):
    def extract(docs, strict=False):
        prompt = ("Extract these fields from the claim documents as JSON with exactly these keys: "
                  f"{json.dumps(SCHEMA)}. parts is a list of [part, price]. "
                  + ("Compute total from the estimate's lines. " if strict else "")
                  + "Documents:\n" + json.dumps(docs))
        body = {"model": model, "temperature": 0, "max_tokens": MAX_OUT["extractor"],
                "response_format": {"type": "json_object"}, "messages": [{"role": "user", "content": prompt}]}
        req = urllib.request.Request(base_url.rstrip("/") + "/chat/completions", json.dumps(body).encode(),
                                     {"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"})
        with urllib.request.urlopen(req, timeout=60) as r:
            raw = json.loads(json.loads(r.read())["choices"][0]["message"]["content"])
        return Extracted(**{k: raw.get(k) for k in SCHEMA})       # a missing or extra field fails here, not downstream
    return extract
