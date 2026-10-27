# phonezero-brief

Live Sogni earnings brief for PhoneZero (Telnyx → xAI voice agent).

**Purpose:** one small public repo that always holds the spoken briefing data for Uzi’s Novacore call. The nightly (and ad-hoc) runner pulls CAD + worker hours from [`sogni-income-history`](https://github.com/novacoreaiservices/sogni-income-history), bakes the opener, pushes here, uploads `phonezero-task.json` to the xAI collection, then dials — **no Live console republish**.

## Always-current files (main)

| File | What |
| --- | --- |
| `figures.json` | Closed / new-day / month CAD + util hours + sources |
| `natural-greeting.txt` | Exact spoken opener |
| `phonezero-task.json` | xAI collection brief (`kind: phonezero-task`) |
| `sms-transcript.txt` | Same opener, SMS-ready |
| `latest.json` | Tiny pointer: baked_at + key CAD numbers |

Raw URLs (no auth):

- https://raw.githubusercontent.com/novacoreaiservices/phonezero-brief/main/figures.json
- https://raw.githubusercontent.com/novacoreaiservices/sogni-income-history/main/snap.json (CAD SoT)

## Runner

```bash
# bake + push + upload collection (no call)
python3 /workspace/phonezero-builder/run_earnings_call.py --prep

# full: prep + dial Uzi + SMS transcript
python3 /workspace/phonezero-builder/run_earnings_call.py --dial

# bake + push only (no xAI upload, no dial)
python3 /workspace/phonezero-builder/run_earnings_call.py --push-only
```

Earning day: **8pm→8pm America/Toronto**. CAD SoT: `snap.json` take-home Combined (`yUsd`/`dayUsd` × `fx`). Prefer Fleet `/workspace/sogni-hourly-earnings` collect for *today* util when newer than GitHub `worker-utilization.csv`.

## Voice agent (stable Live)

Welcome stays short / generic. Instructions tell the agent to `collections_search` `phonezero-task.json` and speak the `opener` field. Numbers change only via this repo + collection upload — never by republishing Live.

## Telnyx dial / SMS

Shell `TELNYX_API_KEY` on the bot computer is often missing or malformed. **Dial and SMS go through the Telnyx MCP connector** (`initiate_texml_calls` + `send_messages`), not curl with the env key. The runner's `--prep` always works for bake/push/upload; `--dial` preps and writes `last-dial-request.json` / `last-sms-request.json` for the connector.
