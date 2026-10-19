# Buffalo Rental Agent

A Claude Code agent and deal calculator for buying and running 1-4 unit rentals in Buffalo, NY, with a focus on keeping property-tax burden low relative to rent.

## Web page (easiest)

`buffalo/desk.html` is the Buffalo Rental Desk: a deal calculator plus an "Ask the agent" chat. It's published as a private claude.ai artifact at https://claude.ai/artifact/9jaZ98Mnsz8mPJk8EviP7V and works on a phone. The chat runs on your Claude account and can re-run the calculator, but it can't browse the web. Use the Claude Code agent below for live lookups of listings, tax rates and laws.

The page also has a map of Buffalo and inner-ring suburb ZIP codes. City ZIPs and suburbs are shaded differently, because inside the city one homestead rate applies while each suburb stacks its own town, village and school rates. Saved deals show as pass/watch/red on their ZIP. Tap a ZIP to see your deals there or ask the agent about it. ZIP shapes come from 2010 Census ZCTAs (via OpenDataDE/State-zip-code-GeoJSON), simplified by `buffalo/build_map.py`.

## Using the agent

In Claude Code, from this repo, ask for it by name:

```
Use the buffalo-rental agent to screen doubles under $200k in North Buffalo and Kenmore
Use the buffalo-rental agent to underwrite 123 Example St, Buffalo NY 14216
Use the buffalo-rental agent to compare FHA house-hack vs 25% down investor loan
Use the buffalo-rental agent to build my rental registry + lead compliance checklist
```

The definition lives in `.claude/agents/buffalo-rental.md`. It covers criteria, neighborhood screening, finding deals, underwriting, financing, offer/contract, NY closing, make-ready and city compliance, leasing under NY law, and ongoing management.

Files it maintains:
- `buffalo/criteria.md` - your buy box (budget, cash flow target, financing, units)
- `buffalo/deals/<address>.md` - one analysis per property, with sources

## Deal calculator

```
python3 buffalo/deal_analyzer.py --price 189000 --rents 1150 1050 \
    --taxes 4100 --insurance 2100 --down-pct 25 --rate 7.25
```

Key options (`--help` for all):
- `--taxes` annual taxes from the actual bill, **with the seller's STAR/senior/veteran exemptions removed**
- `--tax-rate-per-1000` total rate per $1,000; models taxes reassessed at the purchase price (downside case)
- `--mgmt-pct 0` if self-managing; `--utilities` for owner-paid utilities per month
- `--vacancy-pct`, `--maint-pct`, `--capex-pct`, `--closing-pct`, `--rehab`, `--term`

It reports NOI, cash flow, cap rate, cash-on-cash, DSCR, GRM, the 1% rule, effective tax rate and taxes-to-rent ratio. It flags deals with taxes over 15% (watch) or 20% (red) of gross rent, or DSCR under 1.2, and solves for the max offer that hits DSCR 1.2 and 8% cash-on-cash.

## Why "low tax" is about the ratio, not the neighborhood

Inside Buffalo city limits the homestead tax rate is the same everywhere, so differences come from how each property is assessed relative to its price and rent. Suburbs (towns, villages, school districts) each set their own rates. Compare properties on **taxes / price** and **taxes / rent**. Don't go by neighborhood reputation.

This is decision support, not legal, tax, lending or brokerage advice. Have a NY real estate attorney, lender and CPA confirm the specifics.
