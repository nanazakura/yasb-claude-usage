#!/usr/bin/env python3
"""YASB CustomWidget: Claude Code API usage (session limit)."""

import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import URLError

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


def get_usage(force=False):
    if not force and CACHE_PATH.exists():
        age = time.time() - CACHE_PATH.stat().st_mtime
        if age < CACHE_TTL:
            with open(CACHE_PATH) as f:
                return json.load(f)

    token = get_token()
    data = fetch_usage(token)

    with open(CACHE_PATH, "w") as f:
        json.dump(data, f)

    return data


def time_until(iso_str):
    if not iso_str:
        return "\u2014"
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
    return "\u2588" * filled + "\u2591" * (width - filled)


def main():
    force = "--force" in sys.argv
    try:
        data = get_usage(force=force)
    except (URLError, OSError, KeyError, json.JSONDecodeError) as e:
        output = {
            "text": "??",
            "tooltip": f"Error: {e}",
            "status": "high",
            "five_pct": 0,
            "seven_pct": 0,
            "sonnet_pct": 0,
            "five_reset": "??",
            "seven_reset": "??",
            "sonnet_reset": "??",
        }
        print(json.dumps(output))
        return

    five = data.get("five_hour") or {}
    seven = data.get("seven_day") or {}
    sonnet = data.get("seven_day_sonnet") or {}
    extra = data.get("extra_usage") or {}

    five_pct = round(five.get("utilization", 0))
    seven_pct = round(seven.get("utilization", 0))
    sonnet_pct = round(sonnet.get("utilization", 0))
    five_reset = time_until(five.get("resets_at"))
    seven_reset = time_until(seven.get("resets_at"))
    sonnet_reset = time_until(sonnet.get("resets_at"))

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
        f"  Resets in {five_reset}",
        "",
        "7-day rolling",
        f"  {progress_bar(seven_pct)} {seven_pct}%",
        f"  Resets in {seven_reset}",
        "",
        "7-day Sonnet",
        f"  {progress_bar(sonnet_pct)} {sonnet_pct}%",
        f"  Resets in {sonnet_reset}",
    ]

    if extra.get("is_enabled"):
        used = extra.get("used_credits", 0) / 100
        limit = extra.get("monthly_limit", 0) / 100
        extra_pct = round(extra.get("utilization", 0))
        lines += [
            "",
            "Extra credits",
            f"  {progress_bar(extra_pct)} {extra_pct}%",
            f"  ${used:.2f} / ${limit:.2f}",
        ]

    output = {
        "text": f"{five_pct}%",
        "five_pct": five_pct,
        "seven_pct": seven_pct,
        "sonnet_pct": sonnet_pct,
        "five_reset": five_reset,
        "seven_reset": seven_reset,
        "sonnet_reset": sonnet_reset,
        "status": status,
        "tooltip": "\n".join(lines),
    }
    print(json.dumps(output))


if __name__ == "__main__":
    main()
