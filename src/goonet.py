import asyncio
import re
from typing import Optional
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

# CGI 検索結果（goo_used_search.cgi）は UTF-8 の div.section マークアップ。
# 通常一覧（/usedcar/, bodytype-, pref-）は EUC-JP の div.search-card マークアップ。
CGI_BASE = "https://www.goo-net.com/cgi-bin/fsearch/goo_used_search.cgi"


def _decode(resp: httpx.Response) -> str:
    """Content-Type の charset でデコードする。不明時は EUC-JP を試し、それも失敗したら
    tuple: Euc-jp 破損を避けるため UTF-8 と EUC-JP の両対応で返す。"""
    ct = resp.headers.get("content-type", "")
    charset = None
    m = re.search(r"charset=([\w-]+)", ct, re.I)
    if m:
        charset = m.group(1).strip().lower()
    for enc in ([charset] if charset else []) + ["utf-8", "euc-jp"]:
        if not enc:
            continue
        try:
            return resp.content.decode(enc)
        except (UnicodeDecodeError, LookupError):
            continue
    return resp.content.decode("utf-8", "replace")


async def fetch_page(client: httpx.AsyncClient, url: str) -> Optional[str]:
    for attempt in range(3):
        try:
            resp = await client.get(url, follow_redirects=True)
            if resp.status_code == 429 or resp.status_code >= 500:
                await asyncio.sleep(2 ** attempt)
                continue
            # 200 / 3xx / 4xx: goo-net は「結果0件」を 404 + 正常HTML で返すため、
            # 4xx も本文をデコード対象とする（429/5xx のみ再試行）。
            return _decode(resp)
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


def _price_from_em(em) -> Optional[int]:
    """CGI カードの <em>345.9</em>万円 → 3,459,000。"""
    if em is None:
        return None
    txt = em.get_text(strip=True).replace(",", "")
    try:
        return int(float(txt) * 10000)
    except (TypeError, ValueError):
        return None


def _make_detail_url(href: Optional[str]) -> Optional[str]:
    if not href:
        return None
    if href.startswith("http"):
        return href
    return "https://www.goo-net.com" + href


def _parse_card_search_card(card) -> dict:
    """通常一覧の div.search-card マークアップ用パーサー。"""
    detail_link = card.select_one('a[href*="/usedcar/spread/"]')
    if not detail_link:
        return {}
    href = detail_link.get("href", "") or ""
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

    shop_elem = card.select_one('a[href*="/usedcar_shop/"]')
    shop = shop_elem.get_text(strip=True) if shop_elem else None

    return {
        "itemId": item_id,
        "title": title,
        "maker": maker,
        "price": price,
        "imageUrl": image_url,
        "detailUrl": _make_detail_url(href),
        "shop": shop,
        "source": "goo-net",
    }


def _parse_card_section(card) -> dict:
    """CGI 検索結果の div.section_body マークアップ用パーサー。"""
    detail_link = card.select_one('a[href*="/usedcar/spread/"]')
    if not detail_link:
        return {}
    href = detail_link.get("href", "") or ""
    id_match = re.search(r"/usedcar/spread/goo/\d+/(\d+)\.html", href)
    item_id = id_match.group(1) if id_match else None

    title_anchor = card.select_one("h2 a.car_name") or detail_link
    ttl_ps = title_anchor.select("p.ttl") if title_anchor else []
    ttl_parts = [p.get_text(strip=True) for p in ttl_ps if p.get_text(strip=True)]
    title = " ".join(ttl_parts) if ttl_parts else None
    maker = ttl_parts[0] if ttl_parts else None

    card_text = card.get_text(" ", strip=True)

    price = _price_from_em(card.select_one(".total-price .num-red em"))
    if price is None:
        price = _extract_price_from_text(card_text, "支払総額")
    if price is None:
        price = _extract_price_from_text(card_text, "車両本体価格")

    img_tag = card.select_one("p.img2 img")
    image_url = None
    if img_tag:
        data_src = img_tag.get("data-src") or ""
        src = img_tag.get("src") or ""
        if "picture1.goo-net.com" in src:
            image_url = src
        elif "picture1.goo-net.com" in data_src:
            image_url = data_src
        else:
            image_url = data_src or None

    shop_elem = card.select_one('a[href*="/usedcar_shop/"]')
    shop = shop_elem.get_text(strip=True) if shop_elem else None

    return {
        "itemId": item_id,
        "title": title,
        "maker": maker,
        "price": price,
        "imageUrl": image_url,
        "detailUrl": _make_detail_url(href),
        "shop": shop,
        "source": "goo-net",
    }


def parse_page(html):
    soup = BeautifulSoup(html, "html.parser")
    results = []

    cards = soup.select("div.search-card")
    if cards:
        for card in cards:
            item = _parse_card_search_card(card)
            if item:
                results.append(item)
        return results

    cards = soup.select("div.section_body")
    for card in cards:
        item = _parse_card_section(card)
        if item:
            results.append(item)
    return results


def list_page(base: str, page: int) -> str:
    """ページ URL 生成。CGI 検索は ?page=N、通常一覧は /index-N.html。"""
    if page <= 1:
        return base
    if base.startswith(CGI_BASE):
        sep = "&" if "?" in base else "?"
        return f"{base}{sep}page={page}"
    return base.rstrip("/") + f"/index-{page}.html"
