# Note for Muse / PhoneZero (2026-11-09)
PhoneZero briefing money SoT is again novacoreaiservices/sogni-income-history:
- hourly-income.csv last row: yesterday_8pm_* / day_8pm_* for the 8pm→8pm Toronto window
- snap.json: fx + Combined/PAYG labels (income-page/UTC-aligned; do not speak snap yUsd as the 8pm closed day)
- sogni-monthly-income-forecast.md: month estimate when outage-aware/forecast is available

Muse's hourly push of phonezero-brief figures.json / natural-greeting.txt / latest.json must
use run_earnings_call.py (cad_from_income_history) or the same income-history files — NOT
sogni-november-at-october-rate daily-earnings.csv. That October-rate book is optional
legacy (--oct-file) only and stopped updating after 05 Nov 2026.
