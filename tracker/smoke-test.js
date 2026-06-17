/**
 * End-to-end smoke test for the funnel. No network/ad spend required.
 *
 * Boots the app on an ephemeral port and verifies:
 *   1. The lander serves HTML.
 *   2. /go logs a click and 302s to the offer with the sub-ID passed through.
 *   3. Distinct ?src= values are attributable separately in /stats.
 *
 * Run: npm run smoke
 */

const assert = require('assert');
const http = require('http');
const fs = require('fs');
const path = require('path');

// Use a throwaway log file so we don't pollute real data.
const tmpLog = path.join(__dirname, '..', 'data', 'clicks.smoke.jsonl');
process.env.LOG_FILE = tmpLog;
process.env.OFFER_URL = 'https://example.com/offer?aff=TEST&sub={SUB}';
process.env.PORT = '0'; // ephemeral

try { fs.unlinkSync(tmpLog); } catch {}

const app = require('./server');

function get(port, urlPath) {
  return new Promise((resolve, reject) => {
    http
      .get({ host: '127.0.0.1', port, path: urlPath }, (res) => {
        let body = '';
        res.on('data', (c) => (body += c));
        res.on('end', () => resolve({ status: res.statusCode, headers: res.headers, body }));
      })
      .on('error', reject);
  });
}

(async () => {
  const server = app.listen(0);
  await new Promise((r) => server.once('listening', r));
  const port = server.address().port;

  try {
    // 1. Lander serves HTML
    const lander = await get(port, '/');
    assert.strictEqual(lander.status, 200, 'lander should return 200');
    assert.ok(/<html/i.test(lander.body), 'lander should be HTML');
    console.log('✓ lander serves HTML');

    // 2. /go redirects with sub passthrough
    const go = await get(port, '/go?sub=abc123&src=exoclick&v=b');
    assert.strictEqual(go.status, 302, '/go should 302');
    assert.ok(
      go.headers.location.includes('sub=abc123'),
      'redirect should carry the sub-ID: ' + go.headers.location
    );
    console.log('✓ /go redirects with sub-ID passthrough →', go.headers.location);

    // 3. Distinct sources are attributable
    await get(port, '/go?sub=def456&src=trafficstars&v=a');
    await get(port, '/go?sub=ghi789&src=exoclick&v=a');
    await new Promise((r) => setTimeout(r, 50)); // let appends flush

    const stats = JSON.parse((await get(port, '/stats')).body);
    assert.strictEqual(stats.total, 3, 'should have 3 clicks, got ' + stats.total);
    assert.strictEqual(stats.bySrc.exoclick, 2, 'exoclick should have 2 clicks');
    assert.strictEqual(stats.bySrc.trafficstars, 1, 'trafficstars should have 1 click');
    console.log('✓ stats attributes clicks per source:', JSON.stringify(stats.bySrc));

    console.log('\nALL SMOKE TESTS PASSED');
  } finally {
    server.close();
    try { fs.unlinkSync(tmpLog); } catch {}
  }
})().catch((err) => {
  console.error('\nSMOKE TEST FAILED:', err.message);
  process.exit(1);
});
