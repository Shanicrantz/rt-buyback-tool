"""Convert compact browser exports (name|display|back|battery|rear|front|port|speaker|fingerprint|HH:MM:SS UTC) to JSON."""
import json, sys
src, dst, url = sys.argv[1], sys.argv[2], sys.argv[3]
keys = ['display', 'back_panel', 'battery', 'rear_camera', 'front_camera', 'charging_port', 'speaker']
out = {}
for line in open(src, encoding='utf-8'):
    f = line.rstrip('\n').split('|')
    if len(f) != 10: continue
    vals = {k: int(v) for k, v in zip(keys, f[1:8]) if v.strip()}
    out[f[0]] = dict(source_url=url, observed_at=f'2026-11-14T{f[9]}.000Z', values=vals, fingerprint=f[8])
json.dump(out, open(dst, 'w'), indent=1, ensure_ascii=False)
print(len(out), sum(1 for v in out.values() if v['values']))
