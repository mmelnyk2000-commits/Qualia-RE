# Buy box

Used by the buffalo-rental agent and the alert triage. Edit freely.

## Search (Redfin saved search, instant email alerts to miweifree@gmail.com)
- Area: South Buffalo (City of Buffalo ZIPs 14220, 14210, 14206; Lackawanna 14218 is a separate city with its own taxes)
- Type: duplex / two-family
- Size: 4+ beds total, 2+ baths
- Price: under $250,000

## Underwriting defaults (Assumption: confirm with real rent comps and the actual tax bill)
- Rent per unit when the listing doesn't state it: first bedroom = $1,000 x neighborhood scale, plus a flat $200 for each additional bedroom (the scale applies to the base only)
- Neighborhood scale for the base. Woodlawn and Caz Park are your anchors; the floor is 80% (Triangle), close to the HUD 2-bed Fair Market Rent of about $975; the steps between are assumptions to adjust:

  | Neighborhood | Base scale | 1-bed | 2-bed | 3-bed | Taxes billed by |
  |---|---|---|---|---|---|
  | Woodlawn | 100% | $1,000 | $1,200 | $1,400 | Town of Hamburg |
  | Caz Park | 90% | $900 | $1,100 | $1,300 | City of Buffalo |
  | Larkinville | 88% | $880 | $1,080 | $1,280 | City of Buffalo |
  | First Ward | 86% | $860 | $1,060 | $1,260 | City of Buffalo |
  | Lackawanna | 86% | $860 | $1,060 | $1,260 | City of Lackawanna |
  | Abbott-McKinley | 84% | $840 | $1,040 | $1,240 | City of Buffalo |
  | South Abbott | 83% | $830 | $1,030 | $1,230 | City of Buffalo |
  | South Park | 82% | $820 | $1,020 | $1,220 | City of Buffalo |
  | Triangle | 80% | $800 | $1,000 | $1,200 | City of Buffalo |

  Unknown neighborhood is priced like Triangle. Total beds are split evenly across units unless the listing gives the split.
- Taxes when the listing doesn't state them (UNVERIFIED until the real bill is pulled): 1.2% of price in the City of Buffalo, 3.0% in Lackawanna, 2.8% in Hamburg
- Vacancy 8%, maintenance 8%, CapEx 8%, management 9%, insurance $2,100/yr, other $600/yr
- Financing: 25% down, 7.0%, 30 years, closing 4%

## Score and tiers
- Score = monthly cash flow after taxes, insurance, management, vacancy, maintenance and CapEx reserves, and the mortgage, at $5 per point ($500/mo = 100)
- UNICORN (magenta): over 100, usually 3+ units
- PASS (green): 40-100 ($200/mo and up, about $100 per door)
- WATCH (yellow): 1-39
- FAIL (red): 0 or below
- A high-severity red flag in the listing text (as-is, cash only, fire, foundation, no interior access, etc.) caps Pass and Unicorn at Watch; the score itself is unchanged

## Rent scale notes
Market check (Trulia, ZIP 14220, June 2026): 1-bed $965, 2-bed $1,150-1,200, 3-bed $1,350. The $200 step per bedroom matches. The Woodlawn and Caz Park base runs about 5-10% low (conservative). The floor was raised from 60% to 80% (Triangle 2-bed now $1,000, near the HUD Fair Market Rent of about $975) and the scale now applies only to the base rent.
