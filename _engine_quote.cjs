// Real-engine A1 for every entry of a DB file, using computeA1() exactly as shipped in index.html.
// usage: node _engine_quote.cjs <db.json> [YYYY-MM-DD] [index.html]  -> prints {"key": a1, ...}
const fs = require('fs'), vm = require('vm'), path = require('path');
const dir = __dirname;
const dbPath = process.argv[2] || path.join(dir, 'phone_db.json');
const [y, m, d] = (process.argv[3] || '2026-10-01').split('-').map(Number);
const html = fs.readFileSync(process.argv[4] || path.join(dir, 'index.html'), 'utf8');
const engine = html.slice(html.indexOf('const TIER_FACTOR'), html.indexOf('// ============ UI STATE'));
if (!engine.includes('function computeA1')) throw new Error('engine slice does not contain computeA1');
const ctx = vm.createContext({});
vm.runInContext(engine + `;globalThis.quote=e=>computeA1(e,new Date(${y},${m - 1},${d}))[0];`, ctx);
const db = JSON.parse(fs.readFileSync(dbPath, 'utf8'));
const out = {};
for (const [k, e] of Object.entries(db)) if (k !== '_meta') out[k] = ctx.quote(e);
process.stdout.write(JSON.stringify(out));
