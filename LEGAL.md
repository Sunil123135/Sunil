# Legal & data-quality notes

## What this workaround is

A **self-built observational dataset** of air freight price signals from free public endpoints and optional manual quote entry. It is designed so you own the time series going forward.

## What this workaround is not

- Not a substitute for TAC Index / Baltic BAI / WorldACD / Xeneta / Freightos Terminal paid history
- Not audited transactional forwarder→airline settlement data
- Not a license to scrape paywalled dashboards

## Allowed sources used by the collectors

1. **Freightos public Shipping Calculator** (`ship.freightos.com/api/shippingCalculator`)
   - Public marketplace estimate ranges; requires attribution to https://www.freightos.com
   - Subject to Freightos MSA / Data Terms; use politely (delay + stop on HTTP 429)
2. **FRED CSV downloads** and **EIA jet fuel XLS** — U.S. government / Fed public data
3. **SHAQ SFX** free JSON — cite per their license; indicative China-origin forwarder index
4. **Drewry public marketing page** — single composite snapshot only; full history is paid
5. **Manual quotes** you lawfully obtain from forwarders / eCargoRates UI (human entry)

## Do not automate

- TAC Index / dashboard.tacindex.com authenticated data
- WorldACD participant extracts
- Xeneta Air platform
- Freightos Terminal subscriber charts/API without a commercial license
