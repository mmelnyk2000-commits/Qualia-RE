#!/usr/bin/env python3
"""
South Buffalo listing triage.

Reads one or more listings as JSON (a list, or one object), estimates rent
from bedrooms and neighborhood, underwrites each with deal_analyzer, scans
the listing text for red flags, and prints one triage card per listing as
JSON. Cards with positive monthly cash flow go on the shortlist.

Listing fields (only address and price are required):
  address, zip, neighborhood, price, beds, baths, units (default 2),
  unit_beds [list], rents [list of actual monthly rents], taxes (annual),
  description, url, source, alert_date

Example:
  python3 buffalo/triage.py listings.json
  echo '{"address":"12 Example St","neighborhood":"Caz Park","price":189000,"beds":5,"baths":2}' | python3 buffalo/triage.py -
"""

import json
import re
import sys
from argparse import Namespace
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from deal_analyzer import analyze, max_offer  # noqa: E402

# Rent model: first bedroom at Woodlawn rate scaled by neighborhood, plus a
# flat amount for each additional bedroom (location moves the base, not the
# bedroom premium). Floor is 80%, near the HUD 2-bed Fair Market Rent. Ranking and the Woodlawn/Caz Park anchors are the
# owner's; the steps between are assumptions to tune in criteria.md.
BASE_FIRST_BED = 1000
BASE_EXTRA_BED = 200
NEIGHBORHOODS = {
    # name: (rent multiplier, tax jurisdiction)
    "Woodlawn": (1.00, "Town of Hamburg"),
    "Caz Park": (0.90, "City of Buffalo"),
    "Larkinville": (0.88, "City of Buffalo"),
    "First Ward": (0.86, "City of Buffalo"),
    "Lackawanna": (0.86, "City of Lackawanna"),
    "Abbott-McKinley": (0.84, "City of Buffalo"),
    "South Abbott": (0.83, "City of Buffalo"),
    "South Park": (0.82, "City of Buffalo"),
    "Triangle": (0.80, "City of Buffalo"),
}
ALIASES = {
    "cazenovia": "Caz Park", "caz": "Caz Park", "cazenovia park": "Caz Park",
    "old first ward": "First Ward", "abbott mckinley": "Abbott-McKinley",
    "mckinley": "Abbott-McKinley", "south abbott": "South Abbott",
    "south park": "South Park", "the triangle": "Triangle",
    "larkin": "Larkinville", "woodlawn": "Woodlawn", "lackawanna": "Lackawanna",
}
UNKNOWN_MULTIPLIER = 0.80  # unknown neighborhood: price it like the weakest one

# Tax estimate when the listing gives no tax figure: share of price.
# UNVERIFIED placeholders, always replaced by the real bill before an offer.
TAX_ESTIMATE = {"City of Buffalo": 0.012, "City of Lackawanna": 0.030, "Town of Hamburg": 0.028}

UNDERWRITING = dict(
    other_income=0, tax_rate_per_1000=0, insurance=2100, vacancy_pct=8, maint_pct=8,
    capex_pct=8, mgmt_pct=9, utilities=0, other_expenses=600, down_pct=25, rate=7.0,
    term=30, closing_pct=4, rehab=0,
)

# Score: monthly cash flow after everything, in points. $500/mo = 100.
# A strong duplex lands near 100; 3+ unit "unicorns" can break above it.
DOLLARS_PER_POINT = 5
PASS_MIN = 40  # $200/mo total, about $100 per door

# Red flags in listing text: (pattern, severity, what it usually means)
RED_FLAGS = [
    (r"\bas[- ]is\b", "high", "Sold as-is: seller won't repair; expect hidden defects"),
    (r"cash only|cash buyers? only|no financing|won'?t (finance|qualify)|not financeable", "high", "Cash only: likely won't pass a lender's appraisal or inspection"),
    (r"investor special|contractor special|handyman|tlc|needs (some )?work|fixer|bring your (tools|imagination)|sweat equity", "high", "Needs significant rehab"),
    (r"fire damage|\bfire\b|smoke damage", "high", "Fire or smoke damage"),
    (r"foundation|structural|settl(ing|ement)|bowing|sagging", "high", "Possible foundation or structural problem"),
    (r"water in (the )?basement|wet basement|seepage|water damage|leak", "high", "Water intrusion"),
    (r"\bmold\b|mildew", "high", "Mold"),
    (r"knob[- ]and[- ]tube|knob & tube|60 ?amp|fuse box|fuses", "high", "Old electrical (knob-and-tube or fuses): insurance and rewiring cost"),
    (r"no (interior )?access|no showings|drive[- ]by only|exterior only|sight unseen", "high", "No interior access: you can't inspect"),
    (r"\bauction\b|in rem|tax foreclosure|sheriff", "high", "Auction or tax-foreclosure sale: little or no due diligence window"),
    (r"short sale|bank approval|subject to (lender|bank)", "medium", "Short sale: slow, uncertain closing"),
    (r"estate sale|probate|executor|surrogate", "medium", "Estate sale: likely as-is, possible court approval delay"),
    (r"highest and best|multiple offers", "medium", "Multiple offers: price may run past your numbers"),
    (r"tenant[- ]occupied|tenants? in place|do not disturb|month[- ]to[- ]month", "medium", "Occupied: limited showings; check leases, deposits and rents"),
    (r"below market rents?|under ?market rents?|rents? (can|could) be raised|upside", "medium", "Current rents are low; NY rules limit how fast you can raise them"),
    (r"\bvacant\b", "low", "Vacant: no rent history; check winterization and vandalism"),
    (r"boiler|old (furnace|roof)|roof (needs|is old)|original (windows|roof|furnace)", "medium", "Major system near end of life"),
    (r"oil tank|underground tank", "medium", "Oil tank: removal or contamination risk"),
    (r"lead|pre[- ]?1978", "low", "Lead paint: Buffalo lead-safe rules apply to rentals"),
    (r"violation|code (issue|enforcement)|condemned|uninhabitable", "high", "Open code violations or condemned"),
    (r"(no|not a legal|illegal|unpermitted) (co|c of o|certificate of occupancy)|converted (single|1)[- ]family|attic (unit|apartment)", "high", "Legal unit count may not match what's advertised"),
    (r"flood|flood zone", "medium", "Flood risk: check FEMA map and insurance"),
    (r"shared (utilities|meters?)|one meter|single meter", "medium", "Shared meters: you'd pay the tenants' utilities"),
    (r"rent ?to ?own|lease ?option|owner financing", "low", "Unusual terms: have the attorney review"),
]


def neighborhood_of(raw):
    if not raw:
        return None
    key = raw.strip().lower()
    for name in NEIGHBORHOODS:
        if key == name.lower():
            return name
    return ALIASES.get(key)


def split_beds(total, units):
    units = max(1, units)
    base, extra = divmod(int(total), units)
    return [base + (1 if i < extra else 0) for i in range(units)]


def rent_for(beds, mult):
    if beds <= 0:
        return 0
    return round(BASE_FIRST_BED * mult + BASE_EXTRA_BED * (beds - 1))


def scan(text):
    found, t = [], (text or "").lower()
    for pattern, severity, meaning in RED_FLAGS:
        m = re.search(pattern, t)
        if m:
            found.append({"severity": severity, "flag": meaning, "match": m.group(0)})
    return found


def slug(s):
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")[:80]


def triage(listing):
    notes = []
    price = float(listing["price"])
    units = int(listing.get("units") or 2)
    hood = neighborhood_of(listing.get("neighborhood"))
    mult, juris = NEIGHBORHOODS.get(hood, (UNKNOWN_MULTIPLIER, "City of Buffalo"))
    if not hood:
        notes.append("Neighborhood unknown: rent priced like Triangle (the lowest).")

    if listing.get("rents"):
        rents = [float(r) for r in listing["rents"]]
        rent_source = "listing"
    else:
        unit_beds = listing.get("unit_beds") or split_beds(listing.get("beds") or 2 * units, units)
        rents = [rent_for(b, mult) for b in unit_beds]
        rent_source = f"model: {hood or 'unknown'} base at {mult:.0%} of Woodlawn + ${BASE_EXTRA_BED}/extra bed, beds per unit {unit_beds}"

    if listing.get("taxes"):
        taxes = float(listing["taxes"])
        tax_source = "listing (check for seller's STAR/senior exemptions)"
    else:
        taxes = price * TAX_ESTIMATE[juris]
        tax_source = f"UNVERIFIED estimate: {TAX_ESTIMATE[juris]:.1%} of price for {juris}"

    a = Namespace(price=price, rents=rents, taxes=taxes, **UNDERWRITING)
    r = analyze(a)
    mo = max_offer(a)
    flags = scan(" ".join(str(listing.get(k) or "") for k in ("description", "remarks", "title")))

    cash_mo = r["cash_flow"] / 12
    score = round(cash_mo / DOLLARS_PER_POINT)
    if score <= 0:
        tier = "fail"
    elif score > 100:
        tier = "unicorn"
    elif score >= PASS_MIN:
        tier = "pass"
    else:
        tier = "watch"
    if tier in ("pass", "unicorn") and any(f["severity"] == "high" for f in flags):
        tier = "watch"
        notes.append("Capped at Watch: high-severity red flag in the listing text.")

    return {
        "id": slug(listing["address"]),
        "address": listing["address"], "zip": str(listing.get("zip") or ""),
        "neighborhood": hood or "Unknown", "jurisdiction": juris,
        "price": price, "beds": listing.get("beds"), "baths": listing.get("baths"), "units": units,
        "rents": rents, "rentSource": rent_source, "taxes": round(taxes), "taxSource": tax_source,
        "cashFlowMo": round(cash_mo), "coc": round(r["coc"] * 100, 1), "dscr": round(r["dscr"], 2),
        "capRate": round(r["cap_rate"] * 100, 2), "taxToRent": round(r["tax_to_rent"] * 100, 1),
        "maxOffer": mo, "priceVsMax": round(price - mo) if mo else None,
        "score": score, "tier": tier, "status": "rejected" if tier == "fail" else "shortlist",
        "redFlags": flags, "notes": notes,
        "url": listing.get("url", ""), "source": listing.get("source", ""), "alertDate": listing.get("alert_date", ""),
        "photosReviewed": False,
    }


def main():
    src = sys.argv[1] if len(sys.argv) > 1 else "-"
    data = json.load(sys.stdin if src == "-" else open(src))
    listings = data if isinstance(data, list) else [data]
    print(json.dumps([triage(x) for x in listings], indent=2))


if __name__ == "__main__":
    main()
