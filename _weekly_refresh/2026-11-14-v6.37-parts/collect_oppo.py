"""Official OPPO India repair prices (support.oppo.com/in/spare-parts-price/). Model codes were taken from the
responses the page itself loaded when each model was opened in the browser (no site code read). For each code, the
same price request the page makes (one per model, sequential); each response saved gzipped with sha256/timestamp.
Every response names its own model, so a code can never be attached to the wrong model."""
import json, gzip, hashlib, time, requests
from pathlib import Path
from datetime import datetime, timezone
W = Path(__file__).resolve().parent; R = W / 'research'
API = 'https://ind-sow-cms-app.oppo.com/oppo-api/basic/v1/getPartPriceNew'; PAGE = 'https://support.oppo.com/in/spare-parts-price/'
codes = [c for c in (W / 'oppo_codes.txt').read_text().replace('\n', ',').split(',') if c.strip()]
out = []
for code in dict.fromkeys(codes):
    body = {"region": "in", "marketingModelCode": code, "regionIsoCode2": "in", "isoLanguageCode": "en", "sourceRoute": "1"}
    at = datetime.now(timezone.utc).isoformat(timespec='milliseconds')
    try:
        r = requests.post(API, json=body, timeout=20); raw = r.content; status = r.status_code
    except requests.RequestException as ex:
        out.append(dict(brand='OPPO', code=code, observed_at=at, error=str(ex)[:150])); continue
    sha = hashlib.sha256(raw).hexdigest(); snap = f'oppo-{code[:12]}-{sha[:16]}.json.gz'; (R / snap).write_bytes(gzip.compress(raw))
    try: name = json.loads(raw)['data']['serviceModelInfoVO']['marketingModelName'].strip()
    except Exception: name = None
    out.append(dict(brand='OPPO', model=name, code=code, observed_at=at, http_status=status, source_url=PAGE, api_url=API, evidence_file=snap, sha256=sha))
    time.sleep(0.8)
(W / 'oppo-raw.json').write_text(json.dumps(out, indent=1))
print(len(out), sum(1 for x in out if x.get('http_status') == 200 and x.get('model')))
