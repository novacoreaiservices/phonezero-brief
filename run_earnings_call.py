#!/usr/bin/env python3
"""PhoneZero fast earnings path: GitHub snap → bake brief → push phonezero-brief → xAI upload → Telnyx dial + SMS.

No xAI Live console / computerUse. CAD SoT = sogni-income-history snap.json Combined (usd×fx).
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import subprocess
import sys
import time
import urllib.request
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

ET = ZoneInfo("America/Toronto")
WORKERS = (462, 463, 478)
SNAP_URL = "https://raw.githubusercontent.com/novacoreaiservices/sogni-income-history/main/snap.json"
UTIL_URL = "https://raw.githubusercontent.com/novacoreaiservices/sogni-income-history/main/worker-utilization.csv"
BRIEF_DIR = Path("/workspace/phonezero-brief")
BUILDER = Path("/workspace/phonezero-builder")
FLEET_RAW = Path("/workspace/sogni-hourly-earnings/raw")
FINANCIAL_COLLECTION = "collection_7a4fef8b-da1f-4690-b4a2-6bb2d8e85324"
TEXML_APP = "3078078919191037222"
FROM = "+12892687236"
TO = "+14169312306"
OUTBOUND_XML = (
    "https://raw.githubusercontent.com/novacoreaiservices/sogni-income-history"
    "/main/phonezero/outbound.xml"
)
XAI_API = "https://api.x.ai/v1"
TELNYX_API = "https://api.telnyx.com/v2"


def now_et() -> datetime:
    return datetime.now(ET)


def http_get(url: str, timeout: int = 30) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "phonezero-brief/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def http_json(method: str, url: str, *, token: str, body: dict | None = None, form=None):
    data = None
    headers = {"Authorization": f"Bearer {token}"}
    if form is not None:
        # multipart left to subprocess curl for simplicity when needed
        raise NotImplementedError("use upload_file helper")
    if body is not None:
        data = json.dumps(body).encode()
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    with urllib.request.urlopen(req, timeout=60) as r:
        raw = r.read().decode()
        return json.loads(raw) if raw else {}


def money_words(cad: float) -> str:
    """Everyday CAD: fifty-four seventy-nine Canadian; month ~ sixteen ninety-eight Canadian."""
    dollars = int(cad)
    cents = int(round((cad - dollars) * 100))
    if cents == 100:
        dollars += 1
        cents = 0
    ones = [
        "zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine",
        "ten", "eleven", "twelve", "thirteen", "fourteen", "fifteen", "sixteen",
        "seventeen", "eighteen", "nineteen",
    ]
    tens = ["", "", "twenty", "thirty", "forty", "fifty", "sixty", "seventy", "eighty", "ninety"]

    def under100(n: int) -> str:
        if n < 20:
            return ones[n]
        t, o = divmod(n, 10)
        return tens[t] if o == 0 else f"{tens[t]}-{ones[o]}"

    def under1000(n: int) -> str:
        if n < 100:
            return under100(n)
        h, rest = divmod(n, 100)
        if rest == 0:
            return f"{ones[h]} hundred"
        return f"{ones[h]} hundred {under100(rest)}"

    if 1000 <= dollars < 2000:
        # Match prior PhoneZero month phrasing: sixteen ninety-eight
        left = f"sixteen {under100(dollars % 100)}"
    elif dollars >= 2000:
        th, rest = divmod(dollars, 1000)
        left = under100(th) + " thousand" + (f" {under1000(rest)}" if rest else "")
    else:
        left = under1000(dollars)

    if cents == 0:
        return f"{left} Canadian"
    return f"{left} {under100(cents)} Canadian"


def hours_phrase(hours: float, *, of_day: bool) -> str:
    """Friendly hours; never decimals. of_day: include 'of the twenty-four hours'."""
    if hours < 0.4:
        core = "a few minutes"
    elif hours < 0.85:
        core = "about half an hour"
    else:
        # round to nearest quarter for speech
        q = round(hours * 4) / 4
        whole = int(q)
        frac = q - whole
        if abs(frac) < 0.01:
            core = f"about {num_word(whole)} hours" if whole != 1 else "about one hour"
        elif abs(frac - 0.25) < 0.01:
            core = f"about {num_word(whole)} and a quarter hours" if whole else "about a quarter hour"
        elif abs(frac - 0.5) < 0.01:
            if whole == 0:
                core = "about half an hour"
            else:
                core = f"about {num_word(whole)} and a half hours"
        elif abs(frac - 0.75) < 0.01:
            core = f"about {num_word(whole)} and three-quarter hours" if whole else "about three-quarters of an hour"
            # prefer "nineteen and three-quarter hours"
            if whole:
                core = f"about {num_word(whole)} and three-quarter hours"
        else:
            core = f"about {num_word(round(hours))} hours"
    if of_day and hours >= 1:
        # "about twenty of the twenty-four hours"
        q = round(hours * 4) / 4
        whole = int(q)
        frac = q - whole
        if abs(frac) < 0.01:
            return f"about {num_word(whole)} of the twenty-four hours"
        if abs(frac - 0.5) < 0.01:
            return f"about {num_word(whole)} and a half of the twenty-four hours"
        if abs(frac - 0.75) < 0.01:
            return f"about {num_word(whole)} and three-quarter of the twenty-four hours"
        if abs(frac - 0.25) < 0.01:
            return f"about {num_word(whole)} and a quarter of the twenty-four hours"
    return core


def num_word(n: int) -> str:
    ones = [
        "zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine",
        "ten", "eleven", "twelve", "thirteen", "fourteen", "fifteen", "sixteen",
        "seventeen", "eighteen", "nineteen",
    ]
    tens = ["", "", "twenty", "thirty", "forty", "fifty", "sixty", "seventy", "eighty", "ninety"]
    if n < 20:
        return ones[n]
    t, o = divmod(n, 10)
    return tens[t] if o == 0 else f"{tens[t]}-{ones[o]}"


def worker_spoken(n: int) -> str:
    # 462 → four sixty-two
    s = str(n)
    return f"{num_word(int(s[0]))} {num_word(int(s[1:]))}" if len(s) == 3 else num_word(n)



def earning_day_start(n: datetime | None = None) -> datetime:
    """Current 8pm→8pm Toronto window start (last 8pm at or before now)."""
    n = n or now_et()
    eight = n.replace(hour=20, minute=0, second=0, microsecond=0)
    if n < eight:
        eight = eight - timedelta(days=1)
    return eight


def parse_fleet_ts(raw) -> datetime | None:
    if raw is None:
        return None
    if isinstance(raw, (int, float)):
        return datetime.fromtimestamp(raw, tz=ZoneInfo("America/Toronto"))
    s = str(raw).strip()
    try:
        if s.endswith("Z"):
            dt = datetime.fromisoformat(s.replace("Z", "+00:00"))
        else:
            dt = datetime.fromisoformat(s)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=ZoneInfo("America/Toronto"))
        return dt.astimezone(ZoneInfo("America/Toronto"))
    except Exception:
        return None


def fetch_snap() -> dict:
    return json.loads(http_get(SNAP_URL).decode())


def fetch_util_github() -> dict[int, dict]:
    """Latest row per NFT from worker-utilization.csv → closed/new seconds."""
    text = http_get(UTIL_URL).decode()
    rows = list(csv.DictReader(text.splitlines()))
    latest: dict[int, dict] = {}
    ts = None
    for row in rows:
        try:
            nft = int(row["nft"])
        except Exception:
            continue
        if nft not in WORKERS:
            continue
        # last occurrence wins (file is chronological)
        latest[nft] = {
            "yesterday_sec": float(row.get("yesterday_rendering_sec") or 0),
            "today_sec": float(row.get("today_rendering_sec") or 0),
            "ts": row.get("timestamp_toronto") or row.get("timestamp_utc"),
        }
        ts = row.get("timestamp_toronto") or ts
    return {"by_nft": latest, "ts": ts, "source": "github-worker-utilization.csv"}


def fetch_util_fleet() -> dict | None:
    if not FLEET_RAW.exists():
        return None
    days = sorted(FLEET_RAW.glob("*.jsonl"))
    if not days:
        return None
    path = days[-1]
    lines = path.read_text().strip().splitlines()
    if not lines:
        return None
    last = json.loads(lines[-1])
    analytics = (
        last.get("raw", {}).get("day", {}).get("data", {}).get("analytics")
        or last.get("analytics")
        or {}
    )
    by = {}
    for nft in WORKERS:
        a = analytics.get(str(nft)) or {}
        sec = a.get("workSecWorker") or a.get("work_sec")
        if sec is None:
            continue
        by[nft] = {"today_sec": float(sec)}
    if not by:
        return None
    return {
        "by_nft": by,
        "ts": last.get("ts_toronto") or last.get("ts_utc"),
        "source": f"fleet-collect {path.name}",
        "path_mtime": path.stat().st_mtime,
    }


def merge_util(gh: dict, fleet: dict | None) -> dict:
    """Closed hours from GitHub yesterday; new-day from Fleet only if collect is in the current 8pm window."""
    out = {}
    gh_ts = gh.get("ts")
    n = now_et()
    day_start = earning_day_start(n)
    elapsed_h = max((n - day_start).total_seconds() / 3600.0, 0.0)
    use_fleet_today = False
    fleet_reason = "no-fleet"
    if fleet:
        fts = parse_fleet_ts(fleet.get("ts")) or parse_fleet_ts(fleet.get("path_mtime"))
        if fts is None:
            fleet_reason = "unparsed-fleet-ts"
        elif fts < day_start:
            # e.g. 7:58pm collect after 8pm close still holds prior-day workSec
            fleet_reason = f"fleet-before-day-start ({fts.isoformat()} < {day_start.isoformat()})"
        else:
            # sanity: fleet hours cannot exceed elapsed window (+small slack)
            sample = max((fleet["by_nft"].get(nft, {}).get("today_sec") or 0) for nft in WORKERS)
            if sample / 3600.0 > elapsed_h + 0.35:
                fleet_reason = f"fleet-hours-exceed-elapsed ({sample/3600:.2f}h > {elapsed_h:.2f}h)"
            else:
                use_fleet_today = True
                fleet_reason = "fleet-ok"
    for nft in WORKERS:
        g = gh["by_nft"].get(nft, {})
        closed_h = (g.get("yesterday_sec") or 0) / 3600.0
        if use_fleet_today and nft in fleet["by_nft"]:
            new_h = fleet["by_nft"][nft]["today_sec"] / 3600.0
            new_src = fleet["source"]
        else:
            new_h = (g.get("today_sec") or 0) / 3600.0
            new_src = gh["source"]
        out[nft] = {
            "closed_h": round(closed_h, 2),
            "new_h": round(new_h, 2),
            "closed_source": gh["source"],
            "new_source": new_src,
        }
    return {
        "util": out,
        "gh_ts": gh_ts,
        "fleet_ts": (fleet or {}).get("ts"),
        "note": f"closed=GitHub yesterday_rendering_sec; new={'Fleet' if use_fleet_today else 'GitHub'} ({fleet_reason})",
    }


def cad_from_snap(snap: dict) -> dict:
    fx = float(snap["fx"])
    closed_usd = float(snap["yUsd"])
    new_usd = float(snap["dayUsd"])
    closed_cad = round(closed_usd * fx, 2)
    new_cad = round(new_usd * fx, 2)
    # days in current month (Toronto)
    n = now_et()
    import calendar

    days = calendar.monthrange(n.year, n.month)[1]
    month = round(closed_cad * days)
    return {
        "fx": fx,
        "closed_usd": closed_usd,
        "new_usd": new_usd,
        "closed_cad": closed_cad,
        "new_cad": new_cad,
        "month_est_cad": month,
        "dayLabel": snap.get("dayLabel"),
        "yLabel": snap.get("yLabel"),
        "days_in_month": days,
    }


def build_opener(cad: dict, util: dict) -> str:
    c = money_words(cad["closed_cad"])
    n = money_words(cad["new_cad"])
    m = money_words(float(cad["month_est_cad"]))
    # month often "sixteen ninety-eight Canadian" without cents — money_words handles
    parts = [
        "Hey Uzi, it's Novacore with your Sogni briefing.",
        "Quick reminder, your earning day runs eight pm to eight pm Toronto time.",
        f"The last full day, the one that closed at eight pm last night, came in at {c} take-home.",
        f"Today's day, which closes at eight tonight, is already at {n}, so it's tracking right alongside."
        if cad["new_cad"] >= 5
        else f"In the new day since eight pm, you're at {n} so far.",
        f"At the closed-day pace, October lands around {m}."
        if now_et().month == 10
        else f"At the closed-day pace, this month lands around {m}.",
        "On the workers,",
    ]
    # worker sentences
    first = True
    for nft in WORKERS:
        u = util["util"][nft]
        closed_p = hours_phrase(u["closed_h"], of_day=first)
        new_p = hours_phrase(u["new_h"], of_day=False)
        name = worker_spoken(nft)
        if first:
            parts.append(
                f"{name} was busy {closed_p} on the closed day, and {new_p} so far today."
            )
            first = False
        else:
            parts.append(
                f"{name} was {closed_p.replace('about ', 'about ', 1)}, and {new_p} so far."
            )
    # fix middle workers to shorter form
    # rebuild cleaner
    wlines = []
    for i, nft in enumerate(WORKERS):
        u = util["util"][nft]
        name = worker_spoken(nft)
        if i == 0:
            wlines.append(
                f"{name} was busy {hours_phrase(u['closed_h'], of_day=True)} on the closed day, "
                f"and {hours_phrase(u['new_h'], of_day=False)} so far today."
            )
        else:
            wlines.append(
                f"{name} was {hours_phrase(u['closed_h'], of_day=False)}, "
                f"and {hours_phrase(u['new_h'], of_day=False)} so far."
            )
    body = [
        "Hey Uzi, it's Novacore with your Sogni briefing.",
        "Quick reminder, your earning day runs eight pm to eight pm Toronto time.",
        f"The last full day, the one that closed at eight pm last night, came in at {c} take-home.",
    ]
    if cad["new_cad"] >= 5:
        body.append(
            f"Today's day, which closes at eight tonight, is already at {n}, so it's tracking right alongside."
        )
    else:
        body.append(f"In the new day since eight pm, you're at {n} so far.")
    month_name = now_et().strftime("%B")
    body.append(f"At the closed-day pace, {month_name} lands around {m}.")
    body.append("On the workers, " + wlines[0])
    body.extend(wlines[1:])
    body.append("That's the update. Anything you want me to look into?")
    # join with spaces; worker lines already full sentences
    opener = body[0]
    for line in body[1:]:
        if line.startswith("four ") or line.startswith("On the workers"):
            opener += " " + line
        else:
            opener += " " + line
    return opener


def write_brief(cad: dict, util: dict, opener: str) -> dict:
    baked_at = now_et().isoformat()
    figures = {
        "baked_at": baked_at,
        "earning_day": "8pm→8pm America/Toronto",
        "closed_day_cad": cad["closed_cad"],
        "new_day_cad": cad["new_cad"],
        "month_estimate_cad": cad["month_est_cad"],
        "fx": cad["fx"],
        "closed_usd": cad["closed_usd"],
        "new_usd": cad["new_usd"],
        "snap_day_label": cad["dayLabel"],
        "snap_y_label": cad["yLabel"],
        "util_hours": {
            str(k): {"closed_h": v["closed_h"], "new_h": v["new_h"]}
            for k, v in util["util"].items()
        },
        "util_source": {
            "closed": util["gh_ts"],
            "new": util.get("fleet_ts") or util["gh_ts"],
            "note": util["note"],
        },
    }
    task = {
        "kind": "phonezero-task",
        "spoken_name": "Novacore",
        "disclose_ai": False,
        "callee": {"name": "Uzi", "phone": TO},
        "callback": FROM,
        "goal": "Deliver Sogni 8pm→8pm Toronto earnings briefing with live CAD and friendly worker hours, soft check-in, then end.",
        "opener": opener,
        "constraints": [
            "disclose_ai off",
            "never say AI/PhoneZero/Ensia/NFT",
            "speak Combined CAD from snap",
            "friendly worker hours only",
            "load this file; speak opener as first words",
        ],
        "success": "Uzi heard closed CAD, new-day CAD, month estimate, and 462/463/478 hours; soft check-in done.",
        "voicemail": "Hey Uzi, Novacore with your Sogni numbers — I'll try you again shortly.",
        "playbook": [
            "speak opener from this file",
            "soft check-in",
            "goodbye end_call",
        ],
        "facts": {
            "closed_cad": cad["closed_cad"],
            "new_day_cad": cad["new_cad"],
            "month_est_cad": cad["month_est_cad"],
            "fx": cad["fx"],
            "util": {
                str(k): {"closed_h": v["closed_h"], "new_h": v["new_h"]}
                for k, v in util["util"].items()
            },
            "util_snapshot": util.get("fleet_ts") or util.get("gh_ts"),
            "earning_day": "8pm→8pm America/Toronto",
            "brief_repo": "novacoreaiservices/phonezero-brief",
        },
        "instructions_note": "human assistant briefing the boss; speak opener verbatim as first live words",
    }
    latest = {
        "baked_at": baked_at,
        "closed_cad": cad["closed_cad"],
        "new_day_cad": cad["new_cad"],
        "month_est_cad": cad["month_est_cad"],
        "raw": {
            "figures": "figures.json",
            "opener": "natural-greeting.txt",
            "task": "phonezero-task.json",
        },
    }
    BRIEF_DIR.mkdir(parents=True, exist_ok=True)
    (BRIEF_DIR / "figures.json").write_text(json.dumps(figures, indent=2) + "\n")
    (BRIEF_DIR / "natural-greeting.txt").write_text(opener.strip() + "\n")
    (BRIEF_DIR / "sms-transcript.txt").write_text(
        "Novacore call transcript: " + opener.strip() + "\n"
    )
    (BRIEF_DIR / "phonezero-task.json").write_text(json.dumps(task, indent=2) + "\n")
    (BRIEF_DIR / "latest.json").write_text(json.dumps(latest, indent=2) + "\n")
    # mirror into builder for local tools
    (BUILDER / "figures.json").write_text((BRIEF_DIR / "figures.json").read_text())
    (BUILDER / "natural-greeting.txt").write_text(opener.strip() + "\n")
    (BUILDER / "phonezero-task.json").write_text((BRIEF_DIR / "phonezero-task.json").read_text())
    return {"figures": figures, "task": task, "opener": opener}


def git_push_brief(message: str) -> str:
    # local identity for commits (repo-only)
    subprocess.run(
        ["git", "config", "user.email", "novacoreaiservices@users.noreply.github.com"],
        cwd=BRIEF_DIR,
        check=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "novacoreaiservices"],
        cwd=BRIEF_DIR,
        check=True,
    )
    subprocess.run(["git", "add", "-A"], cwd=BRIEF_DIR, check=True)
    st = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=BRIEF_DIR,
        capture_output=True,
        text=True,
        check=True,
    )
    if not st.stdout.strip():
        return "clean"
    subprocess.run(["git", "commit", "-m", message], cwd=BRIEF_DIR, check=True)
    # prefer gh so HTTPS auth works without an interactive prompt
    push = subprocess.run(
        ["gh", "auth", "setup-git"],
        cwd=BRIEF_DIR,
        capture_output=True,
        text=True,
    )
    subprocess.run(["git", "push", "-u", "origin", "HEAD"], cwd=BRIEF_DIR, check=True)
    sha = subprocess.check_output(
        ["git", "rev-parse", "--short", "HEAD"], cwd=BRIEF_DIR, text=True
    ).strip()
    return sha


def xai_key() -> str:
    k = os.environ.get("XAI_API_KEY") or os.environ.get("XAI_VOICE_KEY")
    if not k:
        raise SystemExit("missing XAI_API_KEY")
    return k


def telnyx_key() -> str | None:
    """Shell TELNYX_API_KEY is often missing/malformed on this box.
    Dials/SMS must use the Telnyx MCP connector (user-telnyx), not this env key.
    """
    k = os.environ.get("TELNYX_API_KEY")
    if not k:
        return None
    # known-bad short KEY01… stubs
    if len(k) < 40 or k.startswith("KEY01"):
        return None
    return k


def upload_collection(task_path: Path) -> dict:
    """Upload phonezero-task.json to financial collection; wait until processed when possible."""
    key = xai_key()
    # list + delete old phonezero-task docs
    list_url = f"{XAI_API}/collections/{FINANCIAL_COLLECTION}/documents?limit=50"
    req = urllib.request.Request(list_url, headers={"Authorization": f"Bearer {key}"})
    with urllib.request.urlopen(req, timeout=60) as r:
        listed = json.loads(r.read().decode())
    docs = listed.get("documents") or listed.get("data") or []
    for d in docs:
        name = d.get("file_name") or d.get("name") or d.get("filename") or ""
        fid = d.get("file_id") or d.get("id") or ""
        stale_names = (
            "phonezero-task",
            "natural-greeting",
            "briefing-transcript",
            "sms-transcript",
            "figures.json",
        )
        if fid and any(s in name.lower() for s in stale_names):
            for url in (
                f"{XAI_API}/collections/{FINANCIAL_COLLECTION}/documents/{fid}",
                f"{XAI_API}/files/{fid}",
            ):
                try:
                    urllib.request.urlopen(
                        urllib.request.Request(
                            url,
                            method="DELETE",
                            headers={"Authorization": f"Bearer {key}"},
                        ),
                        timeout=30,
                    )
                except Exception:
                    pass
    # upload via curl multipart (urllib multipart is painful)
    up = subprocess.run(
        [
            "curl",
            "-sS",
            "-X",
            "POST",
            f"{XAI_API}/files",
            "-H",
            f"Authorization: Bearer {key}",
            "-F",
            "purpose=assistants",
            "-F",
            "expires_after=86400",
            "-F",
            f"file=@{task_path};type=application/json;filename=phonezero-task.json",
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    uploaded = json.loads(up.stdout)
    file_id = uploaded["id"]
    attach = http_json(
        "POST",
        f"{XAI_API}/collections/{FINANCIAL_COLLECTION}/documents/{file_id}",
        token=key,
        body={
            "collection_id": FINANCIAL_COLLECTION,
            "file_id": file_id,
            "fields": {"kind": "phonezero-task"},
        },
    )
    status = "unknown"
    for _ in range(40):
        doc = http_json(
            "GET",
            f"{XAI_API}/collections/{FINANCIAL_COLLECTION}/documents/{file_id}",
            token=key,
        )
        status = doc.get("status")
        if status in (
            "DOCUMENT_STATUS_PROCESSED",
            "processed",
            "PROCESSED",
            2,
            "2",
        ):
            return {"ok": True, "file_id": file_id, "status": "processed", "attach": attach}
        if status in ("DOCUMENT_STATUS_FAILED", "failed", "FAILED", 3, "3"):
            return {"ok": False, "file_id": file_id, "status": "failed"}
        time.sleep(2)
    return {"ok": True, "file_id": file_id, "status": status, "note": "still processing"}


def dial() -> dict:
    key = telnyx_key()
    body = {
        "ApplicationSid": TEXML_APP,
        "From": FROM,
        "To": TO,
        "Url": OUTBOUND_XML,
        "UrlMethod": "GET",
        "Record": True,
    }
    # initiate_texml_calls style path
    req = urllib.request.Request(
        f"{TELNYX_API}/texml/calls/{TEXML_APP}",
        data=json.dumps(
            {
                "From": FROM,
                "To": TO,
                "Url": OUTBOUND_XML,
                "UrlMethod": "GET",
                "Record": True,
            }
        ).encode(),
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read().decode())


def send_sms(opener: str) -> dict:
    key = telnyx_key()
    text = "Novacore call transcript: " + opener.strip()
    req = urllib.request.Request(
        f"{TELNYX_API}/messages",
        data=json.dumps(
            {"from": FROM, "to": TO, "type": "SMS", "text": text}
        ).encode(),
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read().decode())


def main():
    ap = argparse.ArgumentParser(description="PhoneZero fast earnings brief runner")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--prep", action="store_true", help="bake + push + upload (no dial)")
    g.add_argument("--dial", action="store_true", help="prep + write dial/SMS payloads; shell dial only if key usable, else Telnyx MCP")
    g.add_argument("--push-only", action="store_true", help="bake + git push only")
    ap.add_argument("--skip-upload", action="store_true")
    args = ap.parse_args()

    snap = fetch_snap()
    cad = cad_from_snap(snap)
    gh = fetch_util_github()
    fleet = fetch_util_fleet()
    util = merge_util(gh, fleet)
    opener = build_opener(cad, util)
    brief = write_brief(cad, util, opener)
    sha = git_push_brief(
        f"brief: closed CA${cad['closed_cad']:.2f} / new CA${cad['new_cad']:.2f} @ {now_et():%Y-%m-%d %H:%M %Z}"
    )
    result = {
        "baked_at": brief["figures"]["baked_at"],
        "git_sha": sha,
        "closed_cad": cad["closed_cad"],
        "new_day_cad": cad["new_cad"],
        "month_est_cad": cad["month_est_cad"],
        "util": brief["figures"]["util_hours"],
        "repo": "https://github.com/novacoreaiservices/phonezero-brief",
        "raw_greeting": "https://raw.githubusercontent.com/novacoreaiservices/phonezero-brief/main/natural-greeting.txt",
    }

    if args.push_only:
        print(json.dumps(result, indent=2))
        return

    if not args.skip_upload:
        up = upload_collection(BRIEF_DIR / "phonezero-task.json")
        result["upload"] = up

    if args.dial:
        # Prefer Telnyx MCP connector — shell env key is unreliable on this box.
        key = telnyx_key()
        dial_request = {
            "application_id": TEXML_APP,
            "From": FROM,
            "To": TO,
            "Url": OUTBOUND_XML,
            "UrlMethod": "GET",
            "Record": True,
        }
        sms_request = {
            "from": FROM,
            "to": TO,
            "type": "SMS",
            "text": "Novacore call transcript: " + opener.strip(),
        }
        (BUILDER / "last-dial-request.json").write_text(json.dumps(dial_request, indent=2) + "\n")
        (BUILDER / "last-sms-request.json").write_text(json.dumps(sms_request, indent=2) + "\n")
        (BRIEF_DIR / "last-dial-request.json").write_text(json.dumps(dial_request, indent=2) + "\n")
        (BRIEF_DIR / "last-sms-request.json").write_text(json.dumps(sms_request, indent=2) + "\n")
        result["opener"] = opener
        result["dial_via"] = "telnyx_mcp"
        result["dial_request"] = dial_request
        result["sms_request"] = {"from": FROM, "to": TO, "type": "SMS", "chars": len(sms_request["text"])}
        if key:
            try:
                call = dial()
                result["call"] = call
                time.sleep(2)
                sms = send_sms(opener)
                result["sms"] = {
                    "id": (sms.get("data") or sms).get("id"),
                    "status": ((sms.get("data") or sms).get("to") or [{}])[0].get("status")
                    if isinstance((sms.get("data") or sms).get("to"), list)
                    else None,
                }
                result["dial_via"] = "shell_telnyx_key"
            except Exception as e:
                result["shell_dial_error"] = str(e)
                result["note"] = (
                    "Prep OK. Shell Telnyx dial failed — parent must dial+SMS via Telnyx connector "
                    "using last-dial-request.json / natural-greeting.txt."
                )
        else:
            result["note"] = (
                "Prep OK. No usable TELNYX_API_KEY in shell — parent must dial+SMS via "
                "Telnyx connector (initiate_texml_calls + send_messages) using "
                "last-dial-request.json and sms-transcript.txt / natural-greeting.txt."
            )

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    try:
        main()
    except urllib.error.HTTPError as e:
        err = e.read().decode(errors="replace")[:500]
        print(json.dumps({"error": str(e), "body": err}), file=sys.stderr)
        sys.exit(1)
