"""Official OnePlus India repair prices (service.oneplus.com/in/spare-parts-price, linked from oneplus.in Repair Pricing).
Model list copied from that page's own device list; for each model the same price request the page makes when the
model is opened (one request per model, sequential). Each response is saved gzipped with its sha256 and timestamp."""
import json, gzip, hashlib, time, sys, requests
from pathlib import Path
from datetime import datetime, timezone
W = Path(__file__).resolve().parent; R = W / 'research'; R.mkdir(exist_ok=True)
API = 'https://ind-sow-cms.oneplus.com/oppo-api/basic/v1/getPartPriceNew'
PAGE = 'https://service.oneplus.com/in/spare-parts-price#/'
out = []
for line in (W / 'oneplus_models.txt').read_text().splitlines():
    name, code = line.split('|')
    body = {"region": "in", "isoLanguageCode": "en-US", "sourceRoute": "1", "brandCode": "12", "marketingModelCode": code, "regionIsoCode2": "in"}
    at = datetime.now(timezone.utc).isoformat(timespec='milliseconds')
    try:
        r = requests.post(API, json=body, timeout=20); raw = r.content; status = r.status_code
    except requests.RequestException as ex:
        out.append(dict(brand='OnePlus', model=name, code=code, observed_at=at, error=str(ex)[:150])); continue
    sha = hashlib.sha256(raw).hexdigest(); snap = f'oneplus-{code[:12]}-{sha[:16]}.json.gz'; (R / snap).write_bytes(gzip.compress(raw))
    out.append(dict(brand='OnePlus', model=name, code=code, observed_at=at, http_status=status, source_url=PAGE, api_url=API, evidence_file=snap, sha256=sha))
    time.sleep(1.0)
(W / 'oneplus-raw.json').write_text(json.dumps(out, indent=1))
print(len(out), sum(1 for x in out if x.get('http_status') == 200))
