#!/usr/bin/env python3
"""
Scrapes the ADCB Accounts FX Rate page and writes a clean JSON feed
(rates.json) for consumption by a digital signage CMS / API endpoint.

Source page: https://www.adcb.com/en/personal/accounts/money-transfer/fx-rate
"""

import io
import json
import re
import sys
from datetime import datetime, timezone

import pandas as pd
import requests

SOURCE_URL = "https://www.adcb.com/en/personal/accounts/money-transfer/fx-rate"
OUTPUT_FILE = "rates.json"

HEADERS = {
    # A normal browser UA avoids basic bot-blocking on some CDNs/WAFs.
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}


def fetch_html(url: str) -> str:
    resp = requests.get(url, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    return resp.text


def extract_as_of_date(html: str) -> str | None:
    """Pulls the 'As of Date:DD-MM-YYYY' string shown above the main table."""
    match = re.search(r"As of Date:\s*([0-9]{2}-[0-9]{2}-[0-9]{4})", html)
    return match.group(1) if match else None


def parse_rates_table(html: str) -> list[dict]:
    """
    Finds the main FX rates table among all tables on the page and
    returns a cleaned list of {currency_name, currency_code, buy_rate, sell_rate}.
    """
    tables = pd.read_html(io.StringIO(html))

    candidate = None
    for df in tables:
        cols = [str(c).strip().lower() for c in df.columns]
        joined = " ".join(cols)
        if "currency" in joined and "buy" in joined and "sell" in joined:
            # The main table is the longest match (segment tables further
            # down the page only list 3 currencies each).
            if candidate is None or len(df) > len(candidate):
                candidate = df

    if candidate is None:
        raise ValueError("Could not locate the FX rates table on the page")

    candidate.columns = [str(c).strip() for c in candidate.columns]

    rename_map = {}
    for c in candidate.columns:
        lc = c.lower()
        if "currency name" in lc:
            rename_map[c] = "currency_name"
        elif "currency code" in lc:
            rename_map[c] = "currency_code"
        elif "buy" in lc:
            rename_map[c] = "buy_rate"
        elif "sell" in lc:
            rename_map[c] = "sell_rate"
    candidate = candidate.rename(columns=rename_map)

    required = {"currency_name", "currency_code", "buy_rate", "sell_rate"}
    if not required.issubset(candidate.columns):
        raise ValueError(f"Unexpected table columns: {list(candidate.columns)}")

    candidate = candidate[list(required)]

    rates = []
    for _, row in candidate.iterrows():
        name = str(row["currency_name"]).strip()
        code = str(row["currency_code"]).strip()
        try:
            buy = float(row["buy_rate"])
            sell = float(row["sell_rate"])
        except (ValueError, TypeError):
            continue  # skip footer/disclaimer rows that aren't real data

        if not code or code.lower() == "nan" or len(code) > 5:
            continue

        rates.append(
            {
                "currency_name": name,
                "currency_code": code.upper(),
                "buy_rate": round(buy, 5),
                "sell_rate": round(sell, 5),
            }
        )

    if not rates:
        raise ValueError("Parsed table but found zero valid currency rows")

    return rates


def main() -> None:
    try:
        html = fetch_html(SOURCE_URL)
        rates = parse_rates_table(html)
        as_of_date = extract_as_of_date(html)
    except Exception as exc:  # noqa: BLE001
        print(f"ERROR scraping ADCB FX rates: {exc}", file=sys.stderr)
        sys.exit(1)

    payload = {
        "source": "ADCB",
        "source_url": SOURCE_URL,
        "base_currency": "AED",
        "as_of_date": as_of_date,
        "scraped_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "count": len(rates),
        "rates": rates,
    }

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)

    print(f"Wrote {len(rates)} rates to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
