"""Official vivo India spare-part prices (www.vivo.com/in/support/accessory). Model ids are read from the saved
page HTML; for each model, the same price request the page makes when the model is clicked (one per model,
sequential). Each response saved gzipped with sha256 and timestamp."""
import json, gzip, hashlib, re, time, sys, requests
from pathlib import Path
from datetime import datetime, timezone
sys.path.insert(0, '/Users/shane/Documents/Claude/Projects/rt buyback tool')
import _market_refresh_runner as m
W = Path(__file__).resolve().parent; m.WORK = W; R = W / 'research'
PAGE = 'https://www.vivo.com/in/support/accessory'; API = 'https://www.vivo.com/in/support/queryPriceByProductId'
raw, meta = m.fetch(PAGE)
lis = re.findall(r'<li[^>]*class="[^"]*select-model-item[^"]*"[^>]*data-id="(\d+)"[^>]*>(.*?)</li>', raw, re.S)
models = list(dict.fromkeys((i, re.sub('<[^>]+>', '', t).strip()) for i, t in lis))
out = []
for pid, name in models:
    at = datetime.now(timezone.utc).isoformat(timespec='milliseconds')
    try:
        r = requests.post(API, data={'id': pid}, timeout=20); body = r.content; status = r.status_code
    except requests.RequestException as ex:
        out.append(dict(brand='vivo', model=name, id=pid, observed_at=at, error=str(ex)[:150])); continue
    sha = hashlib.sha256(body).hexdigest(); snap = f'vivo-{pid}-{sha[:16]}.json.gz'; (R / snap).write_bytes(gzip.compress(body))
    out.append(dict(brand='vivo', model=name, id=pid, observed_at=at, http_status=status, source_url=PAGE, api_url=API, list_page_evidence=meta['snapshot'], evidence_file=snap, sha256=sha))
    time.sleep(0.8)
(W / 'vivo-raw.json').write_text(json.dumps(out, indent=1))
print(len(out), sum(1 for x in out if x.get('http_status') == 200))
