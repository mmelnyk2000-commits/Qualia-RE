#!/usr/bin/env python3
"""
Buffalo rental deal analyzer.
Underwrites a 1-4 unit rental with a focus on property-tax burden.

Example:
  python3 buffalo/deal_analyzer.py --price 189000 --rents 1150 1050 \
      --taxes 4100 --insurance 2100 --down-pct 25 --rate 7.25
"""

import argparse

# Screening thresholds used for the pass/flag verdicts
MAX_TAX_TO_RENT = 0.15      # taxes as share of gross rent; >0.20 is a red flag
RED_TAX_TO_RENT = 0.20
MIN_DSCR = 1.20
MIN_COC = 0.08


def monthly_payment(principal, annual_rate_pct, years):
    r = annual_rate_pct / 100 / 12
    n = years * 12
    if principal <= 0:
        return 0.0
    if r == 0:
        return principal / n
    return principal * r / (1 - (1 + r) ** -n)


def analyze(a):
    gross_rent = sum(a.rents) * 12 + a.other_income * 12
    vacancy = gross_rent * a.vacancy_pct / 100
    egi = gross_rent - vacancy

    # Downside case: taxes re-figured on purchase price at the effective rate
    taxes = a.taxes
    if a.tax_rate_per_1000:
        taxes = max(taxes, a.price * a.tax_rate_per_1000 / 1000)

    expenses = {
        "Property taxes": taxes,
        "Insurance": a.insurance,
        "Maintenance": gross_rent * a.maint_pct / 100,
        "CapEx reserve": gross_rent * a.capex_pct / 100,
        "Management": egi * a.mgmt_pct / 100,
        "Owner-paid utilities": a.utilities * 12,
        "Other (registry, lawn, snow, etc.)": a.other_expenses,
    }
    opex = sum(expenses.values())
    noi = egi - opex

    loan = a.price * (1 - a.down_pct / 100)
    debt_service = monthly_payment(loan, a.rate, a.term) * 12
    cash_flow = noi - debt_service
    cash_in = a.price * (a.down_pct + a.closing_pct) / 100 + a.rehab

    return {
        "gross_rent": gross_rent, "vacancy": vacancy, "egi": egi,
        "expenses": expenses, "opex": opex, "noi": noi,
        "loan": loan, "debt_service": debt_service,
        "cash_flow": cash_flow, "cash_in": cash_in,
        "cap_rate": noi / a.price,
        "coc": cash_flow / cash_in if cash_in else float("inf"),
        "dscr": noi / debt_service if debt_service else float("inf"),
        "grm": a.price / gross_rent,
        "rent_to_price": sum(a.rents) / a.price,
        "eff_tax_rate": taxes / a.price,
        "tax_to_rent": taxes / gross_rent,
        "price_per_unit": a.price / len(a.rents),
    }


def max_offer(a, target_dscr=MIN_DSCR, target_coc=MIN_COC):
    """Highest price (in $1k steps) that still meets DSCR and CoC targets."""
    best = None
    orig = a.price
    for price in range(int(orig * 1.3) // 1000 * 1000, 0, -1000):
        a.price = price
        r = analyze(a)
        if r["dscr"] >= target_dscr and r["coc"] >= target_coc:
            best = price
            break
    a.price = orig
    return best


def verdict(r):
    flags = []
    if r["tax_to_rent"] > RED_TAX_TO_RENT:
        flags.append(f"RED: taxes are {r['tax_to_rent']:.0%} of gross rent (>{RED_TAX_TO_RENT:.0%})")
    elif r["tax_to_rent"] > MAX_TAX_TO_RENT:
        flags.append(f"WATCH: taxes are {r['tax_to_rent']:.0%} of gross rent (>{MAX_TAX_TO_RENT:.0%})")
    if r["dscr"] < MIN_DSCR:
        flags.append(f"RED: DSCR {r['dscr']:.2f} below lender minimum ~{MIN_DSCR}")
    if r["coc"] < MIN_COC:
        flags.append(f"WATCH: cash-on-cash {r['coc']:.1%} below {MIN_COC:.0%} target")
    if r["cash_flow"] < 0:
        flags.append("RED: negative cash flow")
    return flags or ["PASS: meets tax, DSCR and cash-on-cash screens"]


def money(x):
    return f"-${-x:,.0f}" if x < 0 else f"${x:,.0f}"


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--price", type=float, required=True, help="purchase price")
    p.add_argument("--rents", type=float, nargs="+", required=True, help="monthly rent per unit")
    p.add_argument("--taxes", type=float, required=True, help="annual taxes, all levies, exemptions removed")
    p.add_argument("--tax-rate-per-1000", type=float, default=0,
                   help="total rate per $1,000 full value; if set, taxes = max(--taxes, price x rate) for the reassessment downside")
    p.add_argument("--insurance", type=float, default=1800, help="annual landlord insurance")
    p.add_argument("--other-income", type=float, default=0, help="monthly other income (parking, laundry)")
    p.add_argument("--vacancy-pct", type=float, default=8)
    p.add_argument("--maint-pct", type=float, default=8, help="maintenance, %% of gross rent")
    p.add_argument("--capex-pct", type=float, default=8, help="capital reserve, %% of gross rent")
    p.add_argument("--mgmt-pct", type=float, default=9, help="management, %% of collected rent (0 if self-managing)")
    p.add_argument("--utilities", type=float, default=0, help="monthly owner-paid utilities")
    p.add_argument("--other-expenses", type=float, default=600, help="annual other expenses")
    p.add_argument("--down-pct", type=float, default=25)
    p.add_argument("--rate", type=float, default=7.0, help="mortgage interest rate %%")
    p.add_argument("--term", type=int, default=30, help="loan term in years")
    p.add_argument("--closing-pct", type=float, default=4, help="closing costs, %% of price")
    p.add_argument("--rehab", type=float, default=0, help="upfront rehab / make-ready")
    a = p.parse_args()

    r = analyze(a)
    print(f"\nBUFFALO RENTAL ANALYSIS - {money(a.price)}, {len(a.rents)} unit(s)\n")
    print(f"Gross rent (annual)      {money(r['gross_rent'])}")
    print(f"Vacancy ({a.vacancy_pct:.0f}%)            -{money(r['vacancy'])}")
    print(f"Effective gross income   {money(r['egi'])}")
    for k, v in r["expenses"].items():
        print(f"  {k:<34}-{money(v)}")
    print(f"Net operating income     {money(r['noi'])}")
    print(f"Debt service ({a.down_pct:.0f}% down, {a.rate}%, {a.term}y)  -{money(r['debt_service'])}")
    print(f"Annual cash flow         {money(r['cash_flow'])}  ({money(r['cash_flow'] / 12)}/mo)")
    print(f"Cash invested            {money(r['cash_in'])}\n")
    print(f"Cap rate                 {r['cap_rate']:.2%}")
    print(f"Cash-on-cash             {r['coc']:.2%}")
    print(f"DSCR                     {r['dscr']:.2f}")
    print(f"GRM                      {r['grm']:.1f}")
    print(f"Rent/price (1% rule)     {r['rent_to_price']:.2%}")
    print(f"Price per unit           {money(r['price_per_unit'])}")
    print(f"Effective tax rate       {r['eff_tax_rate']:.2%}")
    print(f"Taxes / gross rent       {r['tax_to_rent']:.1%}\n")
    for f in verdict(r):
        print(f)
    mo = max_offer(a)
    print(f"\nMax offer meeting DSCR {MIN_DSCR} and CoC {MIN_COC:.0%}: "
          + (money(mo) if mo else "none at these rents/terms"))


if __name__ == "__main__":
    main()
