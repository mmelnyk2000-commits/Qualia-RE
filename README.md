# 🌴 DR Norte Propiedades

Mobile-first real estate search app for the Dominican Republic north coast and Cibao valley — Jarabacoa, Constanza, La Vega, Moca, Sosúa, Cabarete, and surrounding areas.

**Free to run forever. Scrapes automatically every morning. Works on any phone.**

---

## What this does

- Scrapes property listings from Corotos.com.do and MercadoLibre DR every day at 7am DR time
- Publishes fresh listings to a URL your phone app fetches automatically
- You open the app on your phone like any website — or add it to your home screen as an icon

---

## First-time setup (~10 minutes)

### What you need
- A free [GitHub account](https://github.com/join)
- Git installed ([download here](https://git-scm.com))

### Step 1 — Run the setup script

Open Terminal (Mac) or Command Prompt (Windows) in this folder and run:

```bash
bash setup.sh
```

It will ask for your GitHub username and a repo name, then tell you exactly what to do next.

### Step 2 — Create the GitHub repo

Go to **https://github.com/new** and create a repo with the same name you chose in setup.sh. Leave it public. Don't initialize with README.

### Step 3 — Push the code

Copy-paste the git commands that setup.sh printed. They look like:

```bash
git init
git add .
git commit -m "🌴 Initial DR Norte Propiedades"
git branch -M main
git remote add origin https://github.com/YOUR-USERNAME/YOUR-REPO.git
git push -u origin main
```

### Step 4 — Turn on GitHub Pages

1. Go to your repo on GitHub
2. Click **Settings** → **Pages** (left sidebar)
3. Under "Source": Deploy from branch → Branch: **main** → Folder: **/docs**
4. Click **Save**
5. Wait about 2 minutes

### Step 5 — Open on your phone

Your app is now live at:
```
https://YOUR-USERNAME.github.io/YOUR-REPO-NAME
```

**To add it to your home screen:**
- **iPhone**: Open in Safari → Share button → "Add to Home Screen"
- **Android**: Open in Chrome → menu (⋮) → "Add to Home screen"

It now works like a real app with its own icon.

---

## How the scraper works

GitHub Actions (free, included with every GitHub account) runs `scraper.py` every morning at 7am DR time. It:

1. Scrapes Corotos and MercadoLibre DR for listings in your target region
2. Writes `docs/listings.json` with fresh results
3. Commits and pushes the file back to the repo
4. GitHub Pages serves it at your app's URL
5. Your phone app fetches it automatically when you open the app

If scraping is blocked that day, it falls back to the seed listings automatically. Nothing breaks.

**To trigger a manual scrape:** Go to your repo → Actions tab → "Scrape DR Listings" → "Run workflow"

---

## Files in this folder

```
.github/workflows/scrape.yml   — GitHub Actions schedule (runs daily)
docs/index.html                — The phone app (served by GitHub Pages)
docs/listings.json             — Latest scraped listings (auto-updated)
scraper.py                     — The scraper (run by GitHub Actions)
setup.sh                       — One-time setup wizard
README.md                      — This file
```

---

## Adding listings manually

Open `docs/listings.json` and add entries following this format:

```json
{
  "id": "manual001",
  "title": "Finca en Jarabacoa",
  "area": "Jarabacoa",
  "price": 95000,
  "sizeSolar": 2.5,
  "sizeUnit": "ha",
  "desc": "Description here",
  "contact": "809-555-0000",
  "source": "Manual",
  "url": "",
  "days": 0,
  "type": "farm"
}
```

Types: `land`, `farm`, `house`

Commit and push — the app updates within seconds.

---

## Cost

**$0.** GitHub Actions free tier gives you 2,000 minutes/month. This scraper uses about 3 minutes per day = ~90 minutes/month. Well within limits.
