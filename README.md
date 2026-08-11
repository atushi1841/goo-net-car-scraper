# Goo-net Japan Used Cars Scraper

Scrape used car listings from **[goo-net.com](https://www.goo-net.com/)** — one of Japan's largest used car portals — with prices, maker, and dealer information.

## Why This Data

- Japan exported a record **1.71 million used vehicles in 2025** (JUMVEA) — a massive global market
- Used car exporters (BE FORWARD, carused.jp, SBT Japan, etc.) constantly need fresh inventory and pricing data
- **JDM (Japanese Domestic Market)** models are highly valued worldwide
- Zero dedicated cross-listing competitor on Apify Store at launch

## Features

- ✅ Server-side rendered pages (no browser needed — fast & cheap)
- ✅ Nationwide inventory (47 prefectures) with pagination
- ✅ Model name, price (JPY), maker, image, dealer shop, and detail URL per listing
- ✅ Prefecture filter (e.g. `01` = Hokkaido, `13` = Tokyo, `47` = Okinawa)
- ✅ EUC-JP encoding handled automatically
- ✅ Runs on Apify proxy — no IP blocking issues

## Input

| Field | Type | Default | Description |
|---|---|---|---|
| `searchKeyword` | string | empty | Car model / brand keyword (e.g. `ハイエース`, `アクア`). Empty = full scan |
| `prefecture` | string | empty | Prefecture code `01`–`47`. Empty = all Japan |
| `maxItems` | integer | 100 | Maximum number of listings to collect |
| `maxPages` | integer | 5 | Maximum number of pages to crawl |
| `proxyConfiguration` | object | auto | Apify proxy (auto) |

## Output

Each item contains: `itemId`, `title`, `maker`, `price` (JPY), `imageUrl`, `detailUrl`, `shop`, `source`, `scrapedAt`.

Example:
```json
{
  "itemId": "988026080400207235003",
  "title": "ハイエースバン スーパーGL",
  "maker": "トヨタ",
  "price": 2796000,
  "detailUrl": "https://www.goo-net.com/usedcar/spread/goo/15/988026080400207235003.html",
  "shop": "ハイエース／キャラバン専門店 ファイントラスト土岐店",
  "source": "goo-net"
}
```

## Use Cases

- 🚗 Used car exporters & importers (inventory tracking, pricing research)
- 📊 Market researchers (JDM market trends, price analysis)
- 🔍 JDM enthusiasts hunting specific models

## Pricing

Pay per result: **$0.002 per item** ($2 per 1,000 listings).

## Legal

- Respects goo-net's robots.txt (search endpoints excluded; category pages allowed)
- For research and legitimate business use. Check goo-net's terms before commercial use.
- Rate-limited by design (3 retries, exponential backoff).

## Tech

- Python 3.11 + httpx + BeautifulSoup
- Apify Actor SDK v3
- EUC-JP decode support
