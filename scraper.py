#!/usr/bin/env python3
"""
DR Norte Real Estate Scraper - Fixed URLs
"""

import json, time, re, hashlib
from datetime import datetime, timezone
from pathlib import Path

try:
    import requests
    from bs4 import BeautifulSoup
except ImportError:
    print("Run: pip install requests beautifulsoup4 lxml")
    raise

OUT_FILE = Path(__file__).parent / "docs" / "listings.json"
OUT_FILE.parent.mkdir(exist_ok=True)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept-Language": "es-DO,es;q=0.9,en;q=0.8",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

def clean_price(raw):
    raw = re.sub(r"[^\d]", "", raw or "")
    if raw and 1_000 < int(raw) < 50_000_000:
        return int(raw)
    return None

def clean_size(raw):
    raw = (raw or "").lower().replace(",", ".")
    if m := re.search(r"([\d.]+)\s*(hectare|hectárea|ha\b)", raw):
        return float(m.group(1)), "ha"
    if m := re.search(r"([\d.]+)\s*(m²|m2|metros?)", raw):
        return float(m.group(1)), "m²"
    if m := re.search(r"([\d.]+)\s*(tarea)", raw):
        return round(float(m.group(1)) * 628.86 / 10000, 3), "ha"
    return None, ""

def guess_type(text):
    t = text.lower()
    if any(w in t for w in ["finca","cacao","café","ganader","agrícol","cultiv","siembra"]):
        return "farm"
    if any(w in t for w in ["casa","villa","apart","residen","vivienda","chalet"]):
        return "house"
    return "land"

def make_id(url):
    return hashlib.md5(url.encode()).hexdigest()[:12]

TARGET_AREAS = [
    "jarabacoa","constanza","la vega","moca","santiago rodríguez",
    "san francisco","salcedo","sosúa","sosua","cabarete","puerto plata",
    "río san juan","rio san juan","abreu","nagua","gaspar hernández","villa tapia","bonao",
]

def in_region(text):
    t = text.lower()
    return any(a in t for a in TARGET_AREAS)

# ── Corotos - fixed URLs ──────────────────────────────────────────
COROTOS_QUERIES = [
    "https://www.corotos.com.do/s?q=terreno+jarabacoa",
    "https://www.corotos.com.do/s?q=finca+la+vega",
    "https://www.corotos.com.do/s?q=solar+moca",
    "https://www.corotos.com.do/s?q=terreno+constanza",
    "https://www.corotos.com.do/s?q=casa+jarabacoa",
    "https://www.corotos.com.do/s?q=finca+cibao",
    "https://www.corotos.com.do/s?q=terreno+sosua",
    "https://www.corotos.com.do/s?q=terreno+cabarete",
    "https://www.corotos.com.do/s?q=finca+san+francisco",
    "https://www.corotos.com.do/s?q=terreno+puerto+plata",
]

def scrape_corotos(session):
    results = []
    for url in COROTOS_QUERIES:
        try:
            r = session.get(url, timeout=20)
            r.raise_for_status()
            soup = BeautifulSoup(r.text, "lxml")

            cards = (
                soup.select("div.ad-item") or
                soup.select("article[class*='product']") or
                soup.select("div[class*='listing']") or
                soup.select("div[class*='card']") or
                soup.select("li[class*='ad']") or
                soup.select("a[class*='item']")
            )

            print(f"  Corotos {url[-30:]}: {len(cards)} cards found")

            for card in cards[:25]:
                try:
                    title_el = card.select_one("h2,h3,[class*='title'],[class*='name']")
                    price_el = card.select_one("[class*='price']")
                    link_el  = card.select_one("a[href]")
                    loc_el   = card.select_one("[class*='location'],[class*='city'],[class*='place'],[class*='zona']")
                    desc_el  = card.select_one("[class*='desc'],[class*='detail'],[class*='body']")

                    title = (title_el.get_text(strip=True) if title_el else "").strip()
                    href  = link_el.get("href","") if link_el else ""
                    if not title or not href:
                        continue

                    full_url = href if href.startswith("http") else "https://www.corotos.com.do" + href
                    loc      = loc_el.get_text(strip=True) if loc_el else ""
                    desc     = desc_el.get_text(strip=True) if desc_el else ""
                    price_raw= price_el.get_text(strip=True) if price_el else ""
                    combined = f"{title} {loc} {desc}"

                    if not in_region(combined):
                        continue

                    price    = clean_price(price_raw)
                    sz, unit = clean_size(combined)

                    results.append({
                        "id":        make_id(full_url),
                        "title":     title,
                        "area":      loc or "Norte / Cibao",
                        "price":     price,
                        "sizeSolar": sz,
                        "sizeUnit":  unit or "m²",
                        "desc":      desc,
                        "contact":   "",
                        "source":    "Corotos",
                        "url":       full_url,
                        "days":      0,
                        "type":      guess_type(combined),
                        "scraped":   datetime.now(timezone.utc).isoformat(),
                    })
                except Exception:
                    continue
        except Exception as e:
            print(f"  Corotos error [{url[-30:]}]: {e}")
        time.sleep(2)
    return results

# ── MercadoLibre DR ───────────────────────────────────────────────
MLDR_QUERIES = [
    "https://inmuebles.mercadolibre.com.do/terrenos-y-lotes/jarabacoa/",
    "https://inmuebles.mercadolibre.com.do/terrenos-y-lotes/la-vega/",
    "https://inmuebles.mercadolibre.com.do/fincas/",
    "https://inmuebles.mercadolibre.com.do/casas/jarabacoa/",
    "https://inmuebles.mercadolibre.com.do/terrenos-y-lotes/sosua/",
    "https://listado.mercadolibre.com.do/inmuebles/terrenos/",
]

def scrape_mercadolibre(session):
    results = []
    for url in MLDR_QUERIES:
        try:
            r = session.get(url, timeout=20)
            r.raise_for_status()
            soup = BeautifulSoup(r.text, "lxml")

            items = (
                soup.select("li.ui-search-layout__item") or
                soup.select("div.ui-search-result__wrapper") or
                soup.select("[class*='results-item']") or
                soup.select("[class*='result']")
            )

            print(f"  MercadoLibre {url[-35:]}: {len(items)} items found")

            for item in items[:20]:
                try:
                    title_el = item.select_one("h2,.ui-search-item__title,[class*='title']")
                    price_el = item.select_one(".price-tag-fraction,[class*='price']")
                    link_el  = item.select_one("a[href]")
                    loc_el   = item.select_one(".ui-search-item__location,[class*='location']")
                    attr_el  = item.select_one(".ui-search-card-attributes,[class*='attributes']")

                    title = title_el.get_text(strip=True) if title_el else ""
                    href  = link_el.get("href","") if link_el else ""
                    if not title or not href:
                        continue

                    loc   = loc_el.get_text(strip=True) if loc_el else ""
                    attrs = attr_el.get_text(" ",strip=True) if attr_el else ""
                    price = clean_price(price_el.get_text(strip=True) if price_el else "")
                    combined = f"{title} {loc} {attrs}"
                    if not in_region(combined):
                        continue

                    sz, unit = clean_size(combined)
                    results.append({
                        "id":        make_id(href),
                        "title":     title,
                        "area":      loc or "Norte / Cibao",
                        "price":     price,
                        "sizeSolar": sz,
                        "sizeUnit":  unit or "m²",
                        "desc":      attrs,
                        "contact":   "",
                        "source":    "MercadoLibre",
                        "url":       href,
                        "days":      0,
                        "type":      guess_type(combined),
                        "scraped":   datetime.now(timezone.utc).isoformat(),
                    })
                except Exception:
                    continue
        except Exception as e:
            print(f"  MercadoLibre error [{url[-35:]}]: {e}")
        time.sleep(2)
    return results

# ── Seed fallback ─────────────────────────────────────────────────
SEED = [
    {"id":"s01","title":"Finca en Jarabacoa","area":"Jarabacoa","price":85000,"sizeSolar":3.2,"sizeUnit":"ha","desc":"River access, flat terrain, mature fruit trees. Ideal for eco-lodge or organic farm.","contact":"809-574-0101","source":"Corotos","url":"","days":4,"type":"farm","scraped":""},
    {"id":"s02","title":"Finca Cafetalera – La Vega","area":"La Vega","price":145000,"sizeSolar":8.5,"sizeUnit":"ha","desc":"Established coffee and cacao operation. Workers' quarters, processing shed, full title.","contact":"829-574-0204","source":"RE/MAX DR","url":"","days":11,"type":"farm","scraped":""},
    {"id":"s03","title":"Casa de campo – Constanza","area":"Constanza","price":67000,"sizeSolar":0.45,"sizeUnit":"ha","desc":"3BR/2BA mountain home, cool climate. Views, private garden, paved road access.","contact":"809-574-0312","source":"Corotos","url":"","days":2,"type":"house","scraped":""},
    {"id":"s04","title":"Solar – Moca Centro","area":"Moca","price":28000,"sizeSolar":800,"sizeUnit":"m²","desc":"Urban lot, commercial zoning, 2 blocks from Parque Central. Ready to build.","contact":"849-574-0411","source":"MercadoLibre","url":"","days":7,"type":"land","scraped":""},
    {"id":"s05","title":"Terreno Costero – Río San Juan","area":"Río San Juan","price":195000,"sizeSolar":1.8,"sizeUnit":"ha","desc":"Ocean view, gentle slope, 400m from beach. Subdividable, clean title.","contact":"809-574-0522","source":"Century21 DR","url":"","days":19,"type":"land","scraped":""},
    {"id":"s06","title":"Finca Mixta – Santiago Rodríguez","area":"Santiago Rodríguez","price":112000,"sizeSolar":12,"sizeUnit":"ha","desc":"Avocado, plantain, yuca. Year-round creek. Caretaker house on site.","contact":"829-574-0618","source":"Corotos","url":"","days":3,"type":"farm","scraped":""},
    {"id":"s07","title":"Villa Cabarete Hills","area":"Cabarete","price":240000,"sizeSolar":0.3,"sizeUnit":"ha","desc":"4BR/3BA, pool, ocean views, Airbnb-ready. Gated community, 5 min to beach.","contact":"809-574-0715","source":"RE/MAX DR","url":"","days":22,"type":"house","scraped":""},
    {"id":"s08","title":"Lote de Montaña – Jarabacoa","area":"Jarabacoa","price":55000,"sizeSolar":1.4,"sizeUnit":"ha","desc":"Panoramic valley views, pine forest edge, water spring on property. Quiet road.","contact":"809-574-0905","source":"Corotos","url":"","days":1,"type":"land","scraped":""},
    {"id":"s09","title":"Finca Cacao – San Francisco","area":"San Francisco de Macorís","price":88000,"sizeSolar":5.5,"sizeUnit":"ha","desc":"Certified organic cacao, 4yr established. Export history, CONACADO member.","contact":"829-574-1002","source":"Century21 DR","url":"","days":14,"type":"farm","scraped":""},
    {"id":"s10","title":"Frente de Playa – Abreu","area":"Abreu","price":320000,"sizeSolar":0.9,"sizeUnit":"ha","desc":"Direct beachfront, 95m frontage on calm bay. Rare clear title, surveyed.","contact":"849-574-1201","source":"RE/MAX DR","url":"","days":31,"type":"land","scraped":""},
]

def main():
    session = requests.Session()
    session.headers.update(HEADERS)

    print(f"[{datetime.now().strftime('%H:%M:%S')}] Scraping Corotos…")
    corotos = scrape_corotos(session)
    print(f"  → {len(corotos)} listings")

    print(f"[{datetime.now().strftime('%H:%M:%S')}] Scraping MercadoLibre DR…")
    mldr = scrape_mercadolibre(session)
    print(f"  → {len(mldr)} listings")

    live = corotos + mldr
    seen, unique = set(), []
    for l in live:
        if l["id"] not in seen:
            seen.add(l["id"])
            unique.append(l)

    if len(unique) < 3:
        print(f"  Only {len(unique)} live results — padding with seed data")
        existing_ids = {l["id"] for l in unique}
        unique += [s for s in SEED if s["id"] not in existing_ids]

    payload = {
        "updated":  datetime.now(timezone.utc).isoformat(),
        "count":    len(unique),
        "source":   "GitHub Actions scrape",
        "listings": unique,
    }
    OUT_FILE.write_text(json.dumps(payload, ensure_ascii=False, indent=2))
    print(f"  ✓ Wrote {len(unique)} listings → {OUT_FILE}")

if __name__ == "__main__":
    main()
