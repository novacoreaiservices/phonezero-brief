# Muse hourly note (PhoneZero money SoT)

PhoneZero night brief money SoT = **novacoreaiservices/sogni-income-history**:

- `hourly-income.csv` last row: **`yesterday_total_*` / `today_*`** for the **00:00 UTC** window
  (= **7pm→7pm America/Toronto in winter EST**, 8pm→8pm in summer EDT)
- `snap.json`: fx + Combined/PAYG labels (`yUsd`/`dayUsd`/`yPayg`/`dayPayg`) — same UTC window
- `sogni-monthly-income-forecast.md`: month when available
- `worker-utilization.csv`: `yesterday_rendering_sec` / `today_rendering_sec` (UTC `date_utc`)

Do **not** overwrite the brief with a fixed local-8pm slice or live-only snap CAD that disagrees with the just-closed 00:00 UTC day.
Legacy `*_8pm_*` columns remain in the CSV for the old fixed-8pm Toronto slice; PhoneZero no longer briefs from them by default.

Ontario DST: fall back Nov 1 2026 → EST; earning day spoken as seven-to-seven until spring forward.
