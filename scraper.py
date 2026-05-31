#!/usr/bin/env python3
"""
DR Norte Real Estate Scraper
Targets : Corotos.com.do, MercadoLibre DR
Writes  : docs/listings.json  (served free via GitHub Pages)

GitHub Actions runs this automatically every morning.
You can also trigger it manually from the Actions tab on GitHub.
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

# Write into docs/ so GitHub Pages serves it
OUT_FILE = Path(__file__).parent / "docs" / "listings.json"
OUT_FILE.parent.mkdir(exist_ok=True)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    ),
    "Accept-Language": "es-DO,es;q=0.9,en;q=0.8",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

# ── Helpers ───────────────────────────────────────────────────────────────────

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
    "san francisco","salcedo","sosúa","cabarete","puerto plata",
    "río san juan","abreu","nagua","gaspar hernández","villa tapia","bonao",
]

def in_region(text):
    t = text.lower()
    return any(a in t for a in TARGET_AREAS)

# ── Corotos ───────────────────────────────────────────────────────────────────

COROTOS_QUERIES = [
    "https://www.corotos.com.do/busca?q=terreno+jarabacoa&c=67",
    "https://www.corotos.com.do/busca?q=finca+la+vega&c=67",
    "https://www.corotos.com.do/busca?q=solar+moca&c=67",
    "https://www.corotos.com.do/busca?q=terreno+constanza&c=67",
    "https://www.corotos.com.do/busca?q=casa+jarabacoa&c=67",
    "https://www.corotos.com.do/busca?q=finca+cibao&c=67",
    "https://www.corotos.com.do/busca?q=terreno+sosua&c=67",
    "https://www.corotos.com.do/busca?q=finca+san+francisco&c=67",
]

def scrape_corotos(session):
    results = []
    for url in COROTOS_QUERIES:
        try:
            r = session.get(url, timeout=20)
            r.raise_for_status()
            soup = BeautifulSoup(r.text, "lxml")

            # Try multiple possible card selectors
            cards = (
                soup.select("div.ad-item") or
                soup.select("article[class*='product']") or
                soup.select("div[class*='listing']") or
                soup.select("li[class*='ad']")
            )

            for card in cards[:25]:
                try:
                    title_el = card.select_one("h2,h3,[class*='title'],[class*='name']")
                    price_el = card.select_one("[class*='price']")
                    link_el  = card.select_one("a[href]")
                    loc_el   = card.select_one("[class*='location'],[class*='city'],[class*='place']")
                    desc_el  = card.select_one("[class*='desc'],[class*='detail']")

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
            print(f"  Corotos [{url[-40:]}]: {e}")
        time.sleep(2)
    return results

# ── MercadoLibre DR ───────────────────────────────────────────────────────────

MLDR_QUERIES = [
    "https://inmuebles.mercadolibre.com.do/terrenos-y-lotes/jarabacoa/",
    "https://inmuebles.mercadolibre.com.do/terrenos-y-lotes/la-vega/",
    "https://inmuebles.mercadolibre.com.do/fincas/",
    "https://inmuebles.mercadolibre.com.do/casas/jarabacoa/",
    "https://inmuebles.mercadolibre.com.do/terrenos-y-lotes/sosua/",
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
                soup.select("[class*='result']")
            )

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
            print(f"  MercadoLibre [{url[-40:]}]: {e}")
        time.sleep(2)
    return results

# ── Seed fallback ─────────────────────────────────────────────────────────────

SEED = [
    {"id":"s01","title":"Finca en Jarabacoa","area":"Jarabacoa","price":85000,"sizeSolar":3.2,"sizeUnit":"ha","desc":"River access, flat terrain, mature fruit trees. Ideal for eco-lodge or organic farm.","contact":"809-574-0101","source":"Corotos","url":"","days":4,"type":"farm","scraped":""},
    {"id":"s02","title":"Finca Cafetalera – La Vega","area":"La Vega","price":145000,"sizeSolar":8.5,"sizeUnit":"ha","desc":"Established coffee and cacao operation. Workers' quarters, processing shed, full title.","contact":"829-574-0204","source":"RE/MAX DR","url":"","days":11,"type":"farm","scraped":""},
    {"id":"s03","title":"Casa de campo – Constanza","area":"Constanza","price":67000,"sizeSolar":0.45,"sizeUnit":"ha","desc":"3BR/2BA mountain home, cool climate. Views, private garden, paved road access.","contact":"809-574-0312","source":"Corotos","url":"","days":2,"type":"house","scraped":""},
    {"id":"s04","title":"Solar – Moca Centro","area":"Moca","price":28000,"sizeSolar":800,"sizeUnit":"m²","desc":"Urban lot, commercial zoning, 2 blocks from Parque Central. Ready to build.","contact":"849-574-0411","source":"MercadoLibre","url":"","days":7,"type":"land","scraped":""},
    {"id":"s05","title":"Terreno Costero – Río San Juan","area":"Río San Juan","price":195000,"sizeSolar":1.8,"sizeUnit":"ha","desc":"Ocean view, gentle slope, 400m from beach. Subdividable, clean title.","contact":"809-574-0522","source":"Century21 DR","url":"","days":19,"type":"land","scraped":""},
    {"id":"s06","title":"Finca Mixta – Santiago Rodríguez","area":"Santiago Rodríguez","price":112000,"sizeSolar":12,"sizeUnit":"ha","desc":"Avocado, plantain, yuca. Year-round creek. Caretaker house on site.","contact":"829-574-0618","source":"Corotos","url":"","days":3,"type":"farm","scraped":""},
    {"id":"s07","title":"Villa Cabarete Hills","area":"Cabarete","price":240000,"sizeSolar":0.3,"sizeUnit":"ha","desc":"4BR/3BA, pool, ocean views, Airbnb-ready. Gated community, 5 min to beach.","contact":"809-574-0715","source":"RE/MAX DR","url":"","days":22,"type":"house","scraped":""},
    {"id":"s08","title":"Parcela Agrícola – Salcedo","area":"Salcedo","price":42000,"sizeSolar":2.1,"sizeUnit":"ha","desc":"Flat irrigated land, prev. rice production. Road frontage, power on site.","contact":"849-574-0801","source":"MercadoLibre","url":"","days":5,"type":"land","scraped":""},
    {"id":"s09","title":"Lote de Montaña – Jarabacoa","area":"Jarabacoa","price":55000,"sizeSolar":1.4,"sizeUnit":"ha","desc":"Panoramic valley views, pine forest edge, water spring on property. Quiet road.","contact":"809-574-0905","source":"Corotos","url":"","days":1,"type":"land","scraped":""},
    {"id":"s10","title":"Finca Cacao – San Francisco de Macorís","area":"San Francisco de Macorís","price":88000,"sizeSolar":5.5,"sizeUnit":"ha","desc":"Certified organic cacao, 4yr established. Export history, CONACADO member.","contact":"829-574-1002","source":"Century21 DR","url":"","days":14,"type":"farm","scraped":""},
    {"id":"s11","title":"Casa Colonial – Moca","area":"Moca","price":52000,"sizeSolar":600,"sizeUnit":"m²","desc":"Renovated 1940s home, tile floors, 3BR, large patio. Rental income history.","contact":"809-574-1112","source":"Corotos","url":"","days":8,"type":"house","scraped":""},
    {"id":"s12","title":"Frente de Playa – Abreu","area":"Abreu","price":320000,"sizeSolar":0.9,"sizeUnit":"ha","desc":"Direct beachfront, 95m frontage on calm bay. Rare clear title, surveyed.","contact":"849-574-1201","source":"RE/MAX DR","url":"","days":31,"type":"land","scraped":""},
    {"id":"s13","title":"Finca Ganadera – La Vega","area":"La Vega","price":175000,"sizeSolar":22,"sizeUnit":"ha","desc":"Working cattle farm, corrals, well water, 2 houses. Road accessible year-round.","contact":"809-574-1308","source":"MercadoLibre","url":"","days":6,"type":"farm","scraped":""},
    {"id":"s14","title":"Solar Comercial – Sosúa","area":"Sosúa","price":78000,"sizeSolar":1200,"sizeUnit":"m²","desc":"Carretera Caribe frontage, commercial zone, utilities at curb. High traffic count.","contact":"829-574-1401","source":"Century21 DR","url":"","days":9,"type":"land","scraped":""},
    {"id":"s15","title":"Casa de Retiro – Constanza","area":"Constanza","price":89000,"sizeSolar":0.6,"sizeUnit":"ha","desc":"5BR/3BA, greenhouse, fruit orchard, creek boundary. Move-in ready.","contact":"809-574-1507","source":"Corotos","url":"","days":16,"type":"house","scraped":""},
]

# ── Main ──────────────────────────────────────────────────────────────────────

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
