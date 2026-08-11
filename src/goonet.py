import asyncio
import re
import httpx
from bs4 import BeautifulSoup

KNOWN_MAKERS = [
    "メルセデス・ベンツ",
    "フォルクスワーゲン",
    "レクサス",
    "トヨタ",
    "日産",
    "ホンダ",
    "スズキ",
    "ダイハツ",
    "マツダ",
    "スバル",
    "三菱",
    "ベンツ",
    "ＢＭＷ",
    "BMW",
    "アウディ",
    "ポルシェ",
]

async def fetch_page(client: httpx.AsyncClient, url: str):
    for attempt in range(3):
        try:
            resp = await client.get(url, follow_redirects=True)
            if resp.status_code == 200:
                resp.encoding = "euc-jp"
                return resp.text
            if resp.status_code == 429 or resp.status_code >= 500:
                await asyncio.sleep(2 ** attempt)
                continue
            return None
        except (httpx.HTTPError, OSError):
            await asyncio.sleep(2 ** attempt)
            continue
    return None

def _extract_price_from_text(text, label):
    pos = text.find(label)
    if pos == -1:
        return None
    after = text[pos:]
    after = after.replace(" ", "").replace("\u3000", "")
    m = re.search(r'([\d,]+\.?\d*)\s*万円', after)
    if not m:
        return None
    value_str = m.group(1).replace(',', '')
    try:
        return int(float(value_str) * 10000)
    except (TypeError, ValueError):
        return None

def parse_page(html):
    soup = BeautifulSoup(html, "html.parser")
    results = []
    cards = soup.select("div.search-card")
    for card in cards:
        detail_link = card.select_one('a[href*="/usedcar/spread/"]')
        if not detail_link:
            continue
        href = detail_link.get("href", "")
        id_match = re.search(r"/usedcar/spread/goo/\d+/(\d+)\.html", href)
        item_id = id_match.group(1) if id_match else None

        title_elem = card.select_one("h3.search-card__title a") or card.find("h3")
        title = title_elem.get_text(strip=True) if title_elem else None

        card_text = card.get_text(" ", strip=True)

        maker = None
        for known in KNOWN_MAKERS:
            if known in card_text:
                maker = known
                break
        if maker is None and title:
            maker = title.split()[0]

        price = _extract_price_from_text(card_text, "支払総額")
        if price is None:
            price = _extract_price_from_text(card_text, "車両本体価格")

        img_tag = card.find("img")
        image_url = None
        if img_tag:
            src = img_tag.get("src") or ""
            if "picture1.goo-net.com" in src:
                image_url = src
            else:
                image_url = img_tag.get("data-src") or None

        detail_url = None
        if href:
            if href.startswith("http"):
                detail_url = href
            else:
                detail_url = "https://www.goo-net.com" + href

        shop_elem = card.select_one('a[href*="/usedcar_shop/"]')
        shop = shop_elem.get_text(strip=True) if shop_elem else None

        results.append({
            "itemId": item_id,
            "title": title,
            "maker": maker,
            "price": price,
            "imageUrl": image_url,
            "detailUrl": detail_url,
            "shop": shop,
            "source": "goo-net",
        })
    return results

def list_page(base: str, page: int) -> str:
    if page <= 1:
        return base
    return base.rstrip("/") + f"/index-{page}.html"
