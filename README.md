# ADCB FX Rate Feed for Digital Signage

Scrapes ADCB's public FX rate page on a schedule and publishes a clean
`rates.json` file — a lightweight "API" your CMS can poll.

## Setup (5 minutes)

1. **Create a new GitHub repo** (can be private or public — private repos
   also serve raw files fine as long as the repo itself is public, or you
   generate a token for private access. Simplest: make the repo public).
2. Push these files to the repo root:
   - `scrape_adcb_fx.py`
   - `.github/workflows/update-fx.yml`
3. In the repo, go to **Settings → Actions → General → Workflow permissions**
   and enable **"Read and write permissions"** (needed so the workflow can
   commit the updated JSON back to the repo).
4. Go to the **Actions** tab and manually run **"Update ADCB FX Rates"**
   once (workflow_dispatch) to generate the first `rates.json`.
5. After that first run, it updates itself automatically every 30 minutes.

## The feed URL

Once `rates.json` exists in the repo, it's publicly available at:

```
https://raw.githubusercontent.com/<your-username>/<your-repo>/main/rates.json
```

Point your Signzware CMS data/JSON widget at that URL, with a refresh
interval matching (or slightly longer than) the 30-minute cron schedule.

### Optional: cleaner URL via GitHub Pages
If you'd rather have a proper `https://<user>.github.io/<repo>/rates.json`
URL with correct `application/json` headers (raw.githubusercontent.com
serves it as `text/plain`, which most JSON-fetching widgets handle fine
regardless), enable GitHub Pages in **Settings → Pages** and set the
source to the `main` branch, then reference the Pages URL instead.

## JSON shape

```json
{
  "source": "ADCB",
  "source_url": "https://www.adcb.com/en/personal/accounts/money-transfer/fx-rate",
  "base_currency": "AED",
  "as_of_date": "02-09-2026",
  "scraped_at_utc": "2026-09-02T10:15:03+00:00",
  "count": 33,
  "rates": [
    {
      "currency_name": "US DOLLAR",
      "currency_code": "USD",
      "buy_rate": 3.654,
      "sell_rate": 3.692
    }
  ]
}
```

- `buy_rate` / `sell_rate` are AED per unit of the listed currency.
- `as_of_date` reflects the date ADCB itself shows on the page.
- `scraped_at_utc` is when this specific run pulled the data.

## Adjusting the schedule

Edit the cron line in `.github/workflows/update-fx.yml`. GitHub Actions
free tier scheduled workflows aren't guaranteed to the exact minute (can
run a few minutes late), which is fine for a signage refresh use case.

## Notes

- ADCB has no official public API — this relies on scraping their page,
  so if they redesign the page structure the parser may need a small
  tweak (it's built to find the table by column headers, not by CSS
  classes, so it's reasonably resistant to minor layout changes).
- Rates are indicative per ADCB's own disclaimer — don't use this feed
  for anything beyond display purposes.
