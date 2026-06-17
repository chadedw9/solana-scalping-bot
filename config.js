/**
 * Central config for the Swipey affiliate funnel.
 *
 * Everything you tweak between campaigns lives here so you never have to touch
 * the tracker or lander code. Values can be overridden with environment
 * variables (handy for hosting platforms) — see each field below.
 */

module.exports = {
  // ── Offer ────────────────────────────────────────────────────────────────
  // Your RAW affiliate link from swipey.partners. Get this AFTER Phase 0
  // (signing up + verifying payouts). The {SUB} token is replaced at click
  // time with the incoming sub-ID so you can attribute conversions per source.
  //
  // Example the network gives you might look like:
  //   https://track.swipey.partners/click?aff=YOURID&sub={SUB}
  // Put it here (or set OFFER_URL in the environment).
  offerUrl:
    process.env.OFFER_URL ||
    'https://www.swipey.partners/?aff=REPLACE_ME&sub={SUB}',

  // The token inside offerUrl that gets replaced with the sub-ID value.
  subToken: '{SUB}',

  // ── Defaults for incoming clicks ─────────────────────────────────────────
  // Used when the ad network doesn't pass ?sub= / ?src= macros.
  defaultSub: 'nosub',
  defaultSrc: 'direct',

  // ── Server ───────────────────────────────────────────────────────────────
  port: Number(process.env.PORT) || 3000,

  // Where click events are appended (one JSON object per line).
  logFile: process.env.LOG_FILE || `${__dirname}/data/clicks.jsonl`,

  // Protects the /stats dashboard. Set STATS_TOKEN in the environment before
  // going live so randoms can't read your numbers. If empty, /stats is open
  // (fine for local testing only).
  statsToken: process.env.STATS_TOKEN || '',

  // ── Lander A/B content ───────────────────────────────────────────────────
  // The lander reads ?v=a or ?v=b and swaps the headline. Add more variants
  // here and the lander picks them up automatically.
  landerVariants: {
    a: {
      headline: 'Meet an AI companion who actually remembers you',
      subhead:
        'Chat, connect, and get to know AI personalities built to feel real — free to start.',
      cta: 'Start chatting free',
    },
    b: {
      headline: 'Your AI girlfriend is waiting',
      subhead:
        'Real conversations, your pace, your rules. Create your match in under a minute.',
      cta: 'Create your match',
    },
  },
};
