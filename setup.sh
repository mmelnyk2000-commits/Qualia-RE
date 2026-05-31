#!/bin/bash
# ─────────────────────────────────────────────────────────────────
#  DR Norte Propiedades — One-time GitHub setup
#  Run this once: bash setup.sh
# ─────────────────────────────────────────────────────────────────
set -e

BOLD="\033[1m"
GREEN="\033[32m"
YELLOW="\033[33m"
CYAN="\033[36m"
RESET="\033[0m"

echo ""
echo -e "${BOLD}🌴 DR Norte Propiedades — GitHub Setup${RESET}"
echo "────────────────────────────────────────"
echo ""

# ── Step 1: Check git ────────────────────────────────────────────
if ! command -v git &>/dev/null; then
  echo "Git is not installed. Install it from https://git-scm.com and re-run this script."
  exit 1
fi

# ── Step 2: Get GitHub username ──────────────────────────────────
echo -e "${CYAN}Step 1 of 4: Your GitHub username${RESET}"
echo "(Don't have GitHub? Sign up free at https://github.com/join)"
echo ""
read -p "GitHub username: " GH_USER
GH_USER=$(echo "$GH_USER" | tr -d '[:space:]')
if [ -z "$GH_USER" ]; then echo "Username required."; exit 1; fi

# ── Step 3: Repo name ────────────────────────────────────────────
echo ""
echo -e "${CYAN}Step 2 of 4: Repository name${RESET}"
echo "This will be the name of your GitHub repo."
read -p "Repo name [dr-norte-propiedades]: " REPO_NAME
REPO_NAME=${REPO_NAME:-dr-norte-propiedades}
REPO_NAME=$(echo "$REPO_NAME" | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9-]/-/g')

PAGES_URL="https://${GH_USER}.github.io/${REPO_NAME}"
JSON_URL="${PAGES_URL}/listings.json"

echo ""
echo -e "  App URL  : ${GREEN}${PAGES_URL}${RESET}"
echo -e "  JSON URL : ${GREEN}${JSON_URL}${RESET}"

# ── Step 4: Wire the URL into index.html ─────────────────────────
echo ""
echo -e "${CYAN}Step 3 of 4: Wiring URLs into app…${RESET}"
sed -i.bak "s|LISTINGS_JSON_URL_PLACEHOLDER|${JSON_URL}|g" docs/index.html
rm -f docs/index.html.bak
echo "  ✓ docs/index.html updated"

# ── Step 5: Generate seed listings.json ──────────────────────────
echo ""
echo -e "${CYAN}Step 4 of 4: Generating initial listings.json…${RESET}"
if command -v python3 &>/dev/null; then
  python3 -c "
import json, sys
from datetime import datetime, timezone
from pathlib import Path

seed = [
  {'id':'s01','title':'Finca en Jarabacoa','area':'Jarabacoa','price':85000,'sizeSolar':3.2,'sizeUnit':'ha','desc':'River access, flat terrain, mature fruit trees. Ideal for eco-lodge or organic farm.','contact':'809-574-0101','source':'Corotos','url':'','days':4,'type':'farm'},
  {'id':'s02','title':'Finca Cafetalera – La Vega','area':'La Vega','price':145000,'sizeSolar':8.5,'sizeUnit':'ha','desc':'Established coffee and cacao. Workers quarters, processing shed, full title.','contact':'829-574-0204','source':'RE/MAX DR','url':'','days':11,'type':'farm'},
  {'id':'s03','title':'Casa de campo – Constanza','area':'Constanza','price':67000,'sizeSolar':0.45,'sizeUnit':'ha','desc':'3BR/2BA mountain home, cool climate. Views, private garden, paved road.','contact':'809-574-0312','source':'Corotos','url':'','days':2,'type':'house'},
  {'id':'s04','title':'Solar – Moca Centro','area':'Moca','price':28000,'sizeSolar':800,'sizeUnit':'m²','desc':'Urban lot, commercial zoning, 2 blocks from Parque Central.','contact':'849-574-0411','source':'MercadoLibre','url':'','days':7,'type':'land'},
  {'id':'s05','title':'Terreno Costero – Río San Juan','area':'Río San Juan','price':195000,'sizeSolar':1.8,'sizeUnit':'ha','desc':'Ocean view, gentle slope, 400m from beach. Subdividable, clean title.','contact':'809-574-0522','source':'Century21 DR','url':'','days':19,'type':'land'},
  {'id':'s06','title':'Finca Mixta – Santiago Rodríguez','area':'Santiago Rodríguez','price':112000,'sizeSolar':12,'sizeUnit':'ha','desc':'Avocado, plantain, yuca. Year-round creek. Caretaker house on site.','contact':'829-574-0618','source':'Corotos','url':'','days':3,'type':'farm'},
  {'id':'s07','title':'Villa Cabarete Hills','area':'Cabarete','price':240000,'sizeSolar':0.3,'sizeUnit':'ha','desc':'4BR/3BA, pool, ocean views, Airbnb-ready. Gated community, 5 min to beach.','contact':'809-574-0715','source':'RE/MAX DR','url':'','days':22,'type':'house'},
  {'id':'s08','title':'Lote de Montaña – Jarabacoa','area':'Jarabacoa','price':55000,'sizeSolar':1.4,'sizeUnit':'ha','desc':'Panoramic valley views, pine forest edge, water spring on property.','contact':'809-574-0905','source':'Corotos','url':'','days':1,'type':'land'},
  {'id':'s09','title':'Finca Cacao – San Francisco','area':'San Francisco de Macorís','price':88000,'sizeSolar':5.5,'sizeUnit':'ha','desc':'Certified organic cacao, 4yr established. Export history, CONACADO member.','contact':'829-574-1002','source':'Century21 DR','url':'','days':14,'type':'farm'},
  {'id':'s10','title':'Frente de Playa – Abreu','area':'Abreu','price':320000,'sizeSolar':0.9,'sizeUnit':'ha','desc':'Direct beachfront, 95m frontage on calm bay. Rare clear title, surveyed.','contact':'849-574-1201','source':'RE/MAX DR','url':'','days':31,'type':'land'},
]
out = Path('docs/listings.json')
out.write_text(json.dumps({'updated':datetime.now(timezone.utc).isoformat(),'count':len(seed),'source':'seed','listings':seed}, ensure_ascii=False, indent=2))
print(f'  Wrote {len(seed)} seed listings to {out}')
"
else
  echo "  (python3 not found — listings.json will be created by GitHub Actions on first run)"
fi

# ── Step 6: Init git repo ─────────────────────────────────────────
echo ""
echo -e "${BOLD}──────────────────────────────────────────${RESET}"
echo -e "${BOLD}Now: push this to GitHub${RESET}"
echo ""
echo "Run these commands one at a time:"
echo ""
echo -e "  ${YELLOW}git init${RESET}"
echo -e "  ${YELLOW}git add .${RESET}"
echo -e "  ${YELLOW}git commit -m \"🌴 Initial DR Norte Propiedades\"${RESET}"
echo -e "  ${YELLOW}git branch -M main${RESET}"
echo -e "  ${YELLOW}git remote add origin https://github.com/${GH_USER}/${REPO_NAME}.git${RESET}"
echo -e "  ${YELLOW}git push -u origin main${RESET}"
echo ""
echo -e "${BOLD}Then on GitHub:${RESET}"
echo "  1. Go to https://github.com/${GH_USER}/${REPO_NAME}/settings/pages"
echo "  2. Source → Deploy from branch → Branch: main → Folder: /docs → Save"
echo "  3. Wait ~2 minutes"
echo ""
echo -e "${BOLD}Your app will be live at:${RESET}"
echo -e "  ${GREEN}${PAGES_URL}${RESET}"
echo ""
echo -e "${BOLD}Scraper runs automatically every morning at 7am DR time.${RESET}"
echo "  To trigger it manually:"
echo "  → https://github.com/${GH_USER}/${REPO_NAME}/actions → 'Scrape DR Listings' → Run workflow"
echo ""
echo -e "  ${GREEN}✓ Setup complete!${RESET}"
