import asyncio
import datetime
import json
import sys
import urllib.parse

import httpx

try:
    from apify import Actor
except Exception:
    Actor = None

from goonet import fetch_page, parse_page, list_page

async def run(actor_input, actor):
    search_keyword = actor_input.get("searchKeyword") or ""
    prefecture = actor_input.get("prefecture")
    max_items = int(actor_input.get("maxItems", 100))
    max_pages = int(actor_input.get("maxPages", 5))

    BODY_TYPES = ["BUS", "COMPACT", "COUPE", "KEI", "KEITRUCK", "MINIVAN", "OPEN", "SEDAN", "SUV", "WAGON"]
    body_type_raw = actor_input.get("bodyType") or ""
    body_type = body_type_raw.strip().upper()

    proxy_url = None
    if actor is not None:
        proxy_config = await Actor.create_proxy_configuration(
            actor_proxy_input=actor_input.get("proxyConfiguration") or None
        )
        if proxy_config:
            proxy_url = await proxy_config.new_url()

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "ja,en;q=0.9",
    }

    normal_base = "https://www.goo-net.com/usedcar/"
    if body_type in BODY_TYPES:
        normal_base = f"https://www.goo-net.com/usedcar/bodytype-{body_type}/"
    elif prefecture is not None:
        try:
            pref_code = str(int(prefecture)).zfill(2)
            normal_base = f"https://www.goo-net.com/usedcar/pref-{pref_code}/"
        except (TypeError, ValueError):
            pass

    keyword_url = None
    if search_keyword:
        encoded = urllib.parse.quote(search_keyword)
        keyword_url = f"https://www.goo-net.com/usedcar/search/?keyword={encoded}"

    base_url = keyword_url if keyword_url else normal_base

    async with httpx.AsyncClient(proxy=proxy_url, headers=headers, timeout=30.0) as client:
        collected = 0
        for page in range(1, max_pages + 1):
            if collected >= max_items:
                break
            url = list_page(base_url, page)
            html = await fetch_page(client, url)
            if html is None and keyword_url and page == 1:
                base_url = normal_base
                url = list_page(base_url, page)
                html = await fetch_page(client, url)
            if html is None:
                break
            items = parse_page(html)
            if not items:
                break
            for item in items:
                now_utc = datetime.datetime.now(datetime.timezone.utc)
                item["scrapedAt"] = now_utc.isoformat(timespec="milliseconds").replace("+00:00", "Z")
                if actor is not None:
                    await actor.push_data(item)
                else:
                    print(json.dumps(item, ensure_ascii=False))
                collected += 1
                if collected >= max_items:
                    break
            if collected >= max_items:
                break

    if actor is not None:
        await Actor.exit()

async def main():
    if Actor is not None:
        async with Actor:
            actor_input = await Actor.get_input() or {}
            await run(actor_input, Actor)
    else:
        raw = ""
        if not sys.stdin.isatty():
            raw = sys.stdin.read().strip()
        actor_input = json.loads(raw) if raw else {}
        await run(actor_input, None)

if __name__ == "__main__":
    asyncio.run(main())
