"""Inventory and admin-config storage.

On Vercel, connect an Upstash Redis store (Vercel Marketplace, free tier); it
sets KV_REST_API_URL / KV_REST_API_TOKEN (or UPSTASH_REDIS_REST_URL / _TOKEN).
Then the inventory and the administrator's risk appetite are shared by all
users. Without a store the API is stateless and the browser keeps new
registrations locally (the seeded synthetic inventory is always served).
"""
import json
import os
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parent.parent
SEED = ROOT / "data" / "synthetic" / "seed_inventory.json"
INV_KEY = "registry:inventory"
CFG_KEY = "registry:config"


def _creds():
    url = os.environ.get("KV_REST_API_URL") or os.environ.get("UPSTASH_REDIS_REST_URL")
    tok = os.environ.get("KV_REST_API_TOKEN") or os.environ.get("UPSTASH_REDIS_REST_TOKEN")
    return (url, tok) if url and tok else (None, None)


def persistent() -> bool:
    return _creds()[0] is not None


def _cmd(*args):
    url, tok = _creds()
    r = httpx.post(url, json=list(args), headers={"Authorization": f"Bearer {tok}"}, timeout=10)
    r.raise_for_status()
    return r.json().get("result")


def seed_inventory() -> list:
    try:
        return json.loads(SEED.read_text())
    except FileNotFoundError:
        return []


def list_inventory() -> list:
    if not persistent():
        return seed_inventory()
    raw = _cmd("HGETALL", INV_KEY) or []
    if not raw:
        for r in seed_inventory():
            _cmd("HSET", INV_KEY, r["id"], json.dumps(r))
        raw = _cmd("HGETALL", INV_KEY) or []
    items = [json.loads(raw[i + 1]) for i in range(0, len(raw), 2)]
    return sorted(items, key=lambda r: r.get("submitted", ""), reverse=True)


def get(reg_id: str):
    if not persistent():
        return next((r for r in seed_inventory() if r["id"] == reg_id), None)
    v = _cmd("HGET", INV_KEY, reg_id)
    return json.loads(v) if v else None


def put(reg: dict) -> bool:
    if not persistent():
        return False
    _cmd("HSET", INV_KEY, reg["id"], json.dumps(reg))
    return True


def get_config():
    if not persistent():
        return None
    v = _cmd("GET", CFG_KEY)
    return json.loads(v) if v else None


def put_config(cfg: dict) -> bool:
    if not persistent():
        return False
    _cmd("SET", CFG_KEY, json.dumps(cfg))
    return True


def reset() -> bool:
    if not persistent():
        return False
    _cmd("DEL", INV_KEY)
    _cmd("DEL", CFG_KEY)
    return True
