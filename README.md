# JAO auction calendar

Timeline of JAO monthly auction gates (LT resale, bid gate, dispute submission) per corridor, with a
delivery-month picker. Live page: https://g-mil.github.io/auctions_calendar/

- `python jao_calendar.py` fetches the current month's and every already-published future month's
  auctions for the corridors in `corridors.txt` (JAO API, stdlib only), merges them into
  `data/auctions.json` and writes `index.html` (from `template.html`). `--render` skips the fetch.
- API key: `JAO_API_KEY` environment variable or a `.env` file next to the script (`JAO_API_KEY=...`, git-ignored).
- `update.cmd` runs the fetch, commits and pushes; Windows Task Scheduler runs it on the 1st of each
  month (task "JAO auction calendar update"). Log: `update.log`.
- History before Oct 2026 was seeded from the grbg-ftr JAO results files.
