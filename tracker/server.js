/**
 * Swipey affiliate funnel — bridge lander + click tracker + stats.
 *
 * Routes:
 *   GET  /            → serves the bridge lander (lander/index.html)
 *   GET  /go          → logs the click and 302-redirects to the offer
 *   GET  /stats       → JSON aggregate of clicks (token-protected)
 *   GET  /healthz     → liveness check
 *
 * Funnel:  ad creative → /  (lander) → /go (tracker) → Swipey offer
 *
 * No database, no native deps: click events are appended to a JSONL file so
 * this runs anywhere Node runs. Good enough for a sub-$500 test; graduate to
 * BeMob/Voluum if you scale.
 */

const express = require('express');
const fs = require('fs');
const path = require('path');
const config = require('../config');

const app = express();
app.set('trust proxy', true); // respect X-Forwarded-For behind a proxy/CDN

// Ensure the data directory exists before we try to append to it.
fs.mkdirSync(path.dirname(config.logFile), { recursive: true });

/** Append one click event as a JSON line. */
function logClick(event) {
  fs.appendFile(config.logFile, JSON.stringify(event) + '\n', (err) => {
    if (err) console.error('[tracker] failed to log click:', err.message);
  });
}

/** Best-effort geo: most adult networks/CDNs pass a country header. */
function countryOf(req) {
  return (
    req.headers['cf-ipcountry'] || // Cloudflare
    req.headers['x-geo-country'] || // some CDNs / network macros
    req.query.geo || // network macro fallback, e.g. &geo={country}
    'XX'
  ).toString().toUpperCase();
}

// ── Bridge lander ──────────────────────────────────────────────────────────
app.use(express.static(path.join(__dirname, '..', 'lander')));

// ── Click tracker / redirect ────────────────────────────────────────────────
app.get('/go', (req, res) => {
  const sub = (req.query.sub || config.defaultSub).toString().slice(0, 128);
  const src = (req.query.src || config.defaultSrc).toString().slice(0, 128);
  const variant = (req.query.v || '').toString().slice(0, 16);

  logClick({
    ts: new Date().toISOString(),
    sub,
    src,
    variant,
    country: countryOf(req),
    ip: req.ip,
    ua: (req.headers['user-agent'] || '').slice(0, 256),
    ref: (req.headers['referer'] || '').slice(0, 256),
  });

  const dest = config.offerUrl.replace(config.subToken, encodeURIComponent(sub));
  res.redirect(302, dest);
});

// ── Stats dashboard (token-protected) ───────────────────────────────────────
app.get('/stats', (req, res) => {
  if (config.statsToken && req.query.token !== config.statsToken) {
    return res.status(401).json({ error: 'unauthorized: pass ?token=' });
  }

  let lines = [];
  try {
    lines = fs
      .readFileSync(config.logFile, 'utf8')
      .split('\n')
      .filter(Boolean);
  } catch {
    return res.json({ total: 0, bySrc: {}, byVariant: {}, byCountry: {} });
  }

  const bySrc = {};
  const byVariant = {};
  const byCountry = {};
  for (const line of lines) {
    let e;
    try {
      e = JSON.parse(line);
    } catch {
      continue;
    }
    bySrc[e.src] = (bySrc[e.src] || 0) + 1;
    byVariant[e.variant || '-'] = (byVariant[e.variant || '-'] || 0) + 1;
    byCountry[e.country || 'XX'] = (byCountry[e.country || 'XX'] || 0) + 1;
  }

  res.json({
    total: lines.length,
    note: 'Clicks only. Pull conversions/revenue from the Swipey dashboard and match by sub-ID to compute EPC.',
    bySrc,
    byVariant,
    byCountry,
  });
});

app.get('/healthz', (_req, res) => res.json({ ok: true }));

if (require.main === module) {
  app.listen(config.port, () => {
    console.log(`[tracker] funnel up on http://localhost:${config.port}`);
    console.log(`[tracker]   lander → http://localhost:${config.port}/`);
    console.log(`[tracker]   click  → http://localhost:${config.port}/go?sub=test&src=demo`);
    console.log(`[tracker]   stats  → http://localhost:${config.port}/stats`);
    if (config.offerUrl.includes('REPLACE_ME')) {
      console.warn('[tracker] WARNING: offerUrl still has a placeholder — set OFFER_URL before going live.');
    }
  });
}

module.exports = app;
