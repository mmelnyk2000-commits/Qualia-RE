# Alert triage runbook

What each scheduled check does. The rent scale, tax estimates and red-flag list live in `buffalo/triage.py`; the buy box is in `buffalo/criteria.md`.

Shortlist page: https://claude.ai/artifact/9jaZ98Mnsz8mPJk8EviP7V (database collection `listings`, one document per listing, id = address slug; run state in `meta/triage`).

1. **Find new alerts.** Gmail search `from:redfin.com newer_than:2d -subject:verify`. Read `meta/triage` and skip message ids already in `processedIds`.
2. **Extract listings.** Read each new message as plain text. An alert can hold several listings. For each one take: address, ZIP, price, beds, baths, sqft, the Redfin link, and any remarks or description text. Try WebFetch on the listing link for the description, annual taxes and unit breakdown; if it's blocked, continue with what the email gives. Never invent a field: leave it out.
3. **Neighborhood.** Assign one of: Woodlawn, Caz Park, Larkinville, First Ward, Lackawanna, Abbott-McKinley, South Abbott, South Park, Triangle, from the street and ZIP. If it could be two, use the lower-ranked one and add a note. If you can't tell, leave it blank (triage then prices it like Triangle).
4. **Triage.** Write the listings to a JSON file in the scratchpad and run `python3 buffalo/triage.py <file>`.
5. **Save cards.** One ArtifactData batch to collection `listings`:
   - new id: `set` the card;
   - existing id with a different price: `update` price and all computed fields (pin `if_version`), add a note "Price changed from $X";
   - existing id, same price: skip. Never overwrite `status: "dismissed"`.
6. **Record the run.** Update `meta/triage` with the processed message ids (keep the latest 300) and `lastRun` (ISO time).
7. **Report.** If nothing new arrived, end the turn silently. Otherwise reply in one short paragraph: how many listings, each one's tier and score (address, neighborhood, price, cash flow/mo, top red flag), unicorns first.

Limits to state honestly: photos are not reviewed; taxes marked UNVERIFIED are estimates until the real bill is pulled; neighborhood is inferred from the address.
