# Swipey.ai Affiliate Funnel — Paid-Traffic Test Kit

A minimal, self-hostable funnel for testing the **Swipey.partners** affiliate
offer (Swipey.ai, an 18+ AI-companion platform) with paid adult traffic on a
**sub-$500 test budget**.

```
  ad creative  →  /  (bridge lander)  →  /go  (click tracker)  →  Swipey offer
                       A/B headline          logs + sub-ID            your aff link
                                             passthrough
```

The point of this kit is **measurement**: it logs every click with its source,
A/B variant, and geo so that — after you pull conversions from the Swipey
dashboard and match them by sub-ID — you can compute real **EPC** (earnings per
click) and compare it to your **CPC** (cost per click) from the ad network. That
EPC-vs-CPC number is the whole game.

> **Reality check:** A $500 budget is *tuition*, not profit. Expect to spend most
> of it buying data. Win or lose, the goal is to leave knowing whether any angle
> is profitable enough to scale.

---

## ⚠️ Do this BEFORE spending a dollar (Phase 0)

These are go/no-go checks. If any fail, **do not fund a campaign.**

1. **Sign up** at https://www.swipey.partners/ and read the terms: payout model
   (CPA vs. revshare), minimum payout, **scrub/chargeback policy**, allowed
   traffic sources, top-paying geos.
2. **Verify they actually pay** — search STM Forum, AffiliateFix, and Affpaying
   for proof of *received* payments, not just signups. Unverified adult programs
   are a classic place to get stiffed.
3. **Grab your raw affiliate link** (with the network's sub-ID macro) and the
   ad network's creative/geo policy.
4. **Sanity-check the offer's legal footing** (the "AI twins of real verified
   models" claim) before sending traffic to it.

---

## Setup

```bash
npm install
```

Set your real offer link (from Phase 0) and protect your stats page:

```bash
export OFFER_URL='https://track.swipey.partners/click?aff=YOURID&sub={SUB}'
export STATS_TOKEN='something-long-and-random'
npm start
```

Everything else lives in [`config.js`](./config.js) — offer URL, A/B lander copy,
port, and log location. Env vars override the file, which is convenient on hosts
like Render/Railway/Fly.

Local URLs:

| URL | What it does |
|---|---|
| `http://localhost:3000/` | Bridge lander (append `?v=a` or `?v=b`) |
| `http://localhost:3000/go?sub=test&src=demo` | Logs a click, 302 → offer |
| `http://localhost:3000/stats?token=…` | JSON click breakdown by source/variant/geo |
| `http://localhost:3000/healthz` | Liveness check |

---

## How attribution works

Ad networks pass **macros** in your destination URL — e.g. ExoClick uses
`{clickid}`, others use `{zoneid}` / `{country}`. Point your ad at the **lander**
and pass those macros as query params:

```
https://yourdomain.com/?v=b&sub={clickid}&src=exoclick&geo={country}
```

The lander forwards `sub`, `src`, `v`, and `geo` to `/go`, which logs them and
injects `sub` into your Swipey link (replacing the `{SUB}` token from `config.js`).
Because the **same sub-ID** travels click → offer, you can later match Swipey's
converting sub-IDs back to the source/variant that produced them.

---

## Reading results (the decision rule)

1. Pull total spend and CPC per source from the **ad network**.
2. Pull conversions/revenue per **sub-ID** from the **Swipey dashboard**.
3. Match sub-IDs to sources via `/stats` and compute **EPC = revenue ÷ clicks**
   for each source/variant.

After ~$150 of spend:

- **EPC > CPC on any angle** → push the reserve budget into that angle.
- **EPC < CPC everywhere** → kill it. The $150 bought you the answer cheaply.

Adjust EPC down for **scrubbing** — adult programs often reject a slice of
conversions, so your dashboard number is optimistic.

---

## Suggested $500 allocation

| Bucket | Amount | Purpose |
|---|---|---|
| Tracker/tooling | $0 | This kit (self-hosted) or free BeMob tier |
| Domain + hosting | ~$20 | Serve lander + tracker over HTTPS |
| Network test #1 | ~$150 | One network, one geo, A/B creatives |
| Network test #2 | ~$150 | Second geo/network — only if #1 shows signal |
| Scale the winner | ~$180 | Deploy only on a proven positive-ROI angle |

Recommended first network: **ExoClick** or **TrafficStars** (solid reporting, low
minimums). Recommended format: **native or banner** (cheaper and more
compliance-friendly than pop). Start in a **cheaper geo** to buy more data per
dollar, then retest winners in Tier-1.

---

## Testing

```bash
npm run smoke
```

Boots the app on an ephemeral port and verifies the lander serves, `/go` 302s
with the sub-ID intact, and `/stats` attributes clicks per source — no ad spend
needed. Also do a manual mobile check of the lander (most adult traffic is
mobile) before submitting creatives.

---

## Scope & honesty notes

- This kit handles the **funnel tech only**. Creating ad-network accounts and
  spending money are **manual steps you do** — they can't and shouldn't be
  automated for you.
- Keep **our** pages SFW and compliant (the lander is deliberately tasteful); the
  explicit content lives on Swipey's side.
- Never deposit more at a network than you can lose until you've been **paid out
  once**. Networks can reject creatives or hold funds.
- You're promoting **18+ AI content**. Make sure that's compatible with your own
  goals and local rules before you start.
