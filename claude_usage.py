#!/usr/bin/env python3
"""YASB CustomWidget: Claude Code API usage (session/weekly limits)."""

import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

CACHE_PATH = Path(os.environ.get("TEMP", "/tmp")) / "claude_usage_cache.json"
CACHE_TTL = 120  # 2 minutes
CREDS_PATH = Path.home() / ".claude" / ".credentials.json"
API_URL = "https://api.anthropic.com/api/oauth/usage"


def get_token():
    with open(CREDS_PATH) as f:
        return json.load(f)["claudeAiOauth"]["accessToken"]


def fetch_usage(token):
    req = Request(API_URL)
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("anthropic-beta", "oauth-2025-04-20")
    req.add_header("User-Agent", "claude-code/2.0.32")
    with urlopen(req, timeout=10) as resp:
        return json.loads(resp.read())


def read_cache():
    with open(CACHE_PATH) as f:
        return json.load(f)


def get_usage(force=False):
    """Return (data, stale_note). stale_note is set when serving old cache
    after a fetch failure; raises only if there is no cache to fall back on."""
    if not force and CACHE_PATH.exists():
        age = time.time() - CACHE_PATH.stat().st_mtime
        if age < CACHE_TTL:
            return read_cache(), None

    try:
        data = fetch_usage(get_token())
    except HTTPError as e:
        note = "token expired - open Claude Code" if e.code == 401 else f"HTTP {e.code}"
        return stale_fallback(note)
    except (URLError, OSError, KeyError, json.JSONDecodeError) as e:
        return stale_fallback(str(e) or type(e).__name__)

    with open(CACHE_PATH, "w") as f:
        json.dump(data, f)
    return data, None


def stale_fallback(note):
    if CACHE_PATH.exists():
        age_min = int((time.time() - CACHE_PATH.stat().st_mtime) / 60)
        return read_cache(), f"{note} (data {age_min}m old)"
    raise RuntimeError(note)


def pct(value):
    return round(value or 0)


def parse_limits(data):
    """Normalize API schemas into (session, weekly, scoped).

    Prefers the `limits` array (kind: session / weekly_all / weekly_scoped);
    falls back to legacy top-level five_hour / seven_day / seven_day_* blocks.
    """
    session = {"pct": 0, "reset": None}
    weekly = {"pct": 0, "reset": None}
    scoped = []  # e.g. [{"name": "Fable", "pct": 3, "reset": "..."}]

    for lim in data.get("limits") or []:
        entry = {"pct": pct(lim.get("percent")), "reset": lim.get("resets_at")}
        kind = lim.get("kind")
        if kind == "session":
            session = entry
        elif kind == "weekly_all":
            weekly = entry
        elif kind == "weekly_scoped":
            model = (lim.get("scope") or {}).get("model") or {}
            scoped.append({"name": model.get("display_name") or "Scoped", **entry})

    if not data.get("limits"):
        five = data.get("five_hour") or {}
        seven = data.get("seven_day") or {}
        session = {"pct": pct(five.get("utilization")), "reset": five.get("resets_at")}
        weekly = {"pct": pct(seven.get("utilization")), "reset": seven.get("resets_at")}
        for key, name in (("seven_day_sonnet", "Sonnet"), ("seven_day_opus", "Opus")):
            block = data.get(key)
            if block:
                scoped.append({
                    "name": name,
                    "pct": pct(block.get("utilization")),
                    "reset": block.get("resets_at"),
                })

    return session, weekly, scoped


def find_scoped(scoped, name):
    for entry in scoped:
        if entry["name"].lower() == name:
            return entry
    return None


def time_until(iso_str):
    if not iso_str:
        return "—"
    target = datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
    delta = target - datetime.now(timezone.utc)
    total = int(delta.total_seconds())
    if total <= 0:
        return "now"
    d, rem = divmod(total, 86400)
    h, m = divmod(rem // 60, 60)
    if d > 0:
        return f"{d}d{h:02d}h"
    if h > 0:
        return f"{h}h{m:02d}m"
    return f"{m}m"


def progress_bar(pct, width=20):
    filled = round(pct / 100 * width)
    return "█" * filled + "░" * (width - filled)


def error_output(message):
    return {
        "text": "??",
        "tooltip": f"Error: {message}",
        "status": "high",
        "five_pct": 0,
        "seven_pct": 0,
        "fable_pct": 0,
        "sonnet_pct": 0,
        "five_reset": "??",
        "seven_reset": "??",
        "fable_reset": "??",
        "sonnet_reset": "??",
    }


def build_output(data, stale_note):
    session, weekly, scoped = parse_limits(data)
    fable = find_scoped(scoped, "fable")
    sonnet = find_scoped(scoped, "sonnet")

    five_pct = session["pct"]
    if five_pct >= 80:
        status = "high"
    elif five_pct >= 50:
        status = "medium"
    else:
        status = "low"

    # Plain-text tooltip (no Pango markup)
    lines = [
        "Claude Code Usage",
        "",
        "5-hour session",
        f"  {progress_bar(five_pct)} {five_pct}%",
        f"  Resets in {time_until(session['reset'])}",
        "",
        "7-day rolling",
        f"  {progress_bar(weekly['pct'])} {weekly['pct']}%",
        f"  Resets in {time_until(weekly['reset'])}",
    ]

    for entry in scoped:
        lines += [
            "",
            f"7-day {entry['name']}",
            f"  {progress_bar(entry['pct'])} {entry['pct']}%",
            f"  Resets in {time_until(entry['reset'])}",
        ]

    extra = data.get("extra_usage") or {}
    used = (extra.get("used_credits") or 0) / 100
    limit_raw = extra.get("monthly_limit")
    if extra.get("is_enabled") and (limit_raw or used):
        lines += ["", "Extra credits"]
        if limit_raw:
            extra_pct = pct(extra.get("utilization"))
            lines += [
                f"  {progress_bar(extra_pct)} {extra_pct}%",
                f"  ${used:.2f} / ${limit_raw / 100:.2f}",
            ]
        else:
            lines += [f"  ${used:.2f} used"]

    if stale_note:
        lines += ["", f"(!) {stale_note}"]

    return {
        "text": f"{five_pct}%",
        "five_pct": five_pct,
        "seven_pct": weekly["pct"],
        "fable_pct": fable["pct"] if fable else 0,
        "sonnet_pct": sonnet["pct"] if sonnet else 0,
        "five_reset": time_until(session["reset"]),
        "seven_reset": time_until(weekly["reset"]),
        "fable_reset": time_until(fable["reset"]) if fable else "—",
        "sonnet_reset": time_until(sonnet["reset"]) if sonnet else "—",
        "status": status,
        "tooltip": "\n".join(lines),
    }


def main():
    force = "--force" in sys.argv
    # Never let an exception escape without JSON: YASB needs output every run.
    try:
        data, stale_note = get_usage(force=force)
        output = build_output(data, stale_note)
    except Exception as e:  # noqa: BLE001
        output = error_output(e)
    print(json.dumps(output))


if __name__ == "__main__":
    main()
