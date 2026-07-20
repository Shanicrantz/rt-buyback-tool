import json

DB_PATH = 'phone_db.json'
HTML_PATH = 'index.html'
TODAY = '2026-07-03'

db = json.load(open(DB_PATH))

NEW = {
    # OnePlus N6 (budget N-series, Dimensity 6360 Apex, 8000mAh) — distinct from Nord 6
    'oneplus_n6_4_128': {
        'display_name': 'OnePlus N6 (4GB/128GB)', 'tier': 'C',
        'discontinued': False, 'launch_date': '2026-06-30',
        'resale_target_a1': 15500, 'calibration_status': 'estimated', 'calibration_date': TODAY,
        'live_source': 'OnePlus N6 launched India Jun 30 2026 (budget N-series, MediaTek Dimensity 6360 Apex, 8000mAh, distinct from Nord 6). 4GB/128GB MRP Rs 22,999 (Smartprix/TelecomTalk). Sale Jul 4 Amazon. A1 resale estimated conservative.',
    },
    'oneplus_n6_6_128': {
        'display_name': 'OnePlus N6 (6GB/128GB)', 'tier': 'C',
        'discontinued': False, 'launch_date': '2026-06-30',
        'resale_target_a1': 16500, 'calibration_status': 'estimated', 'calibration_date': TODAY,
        'live_source': 'OnePlus N6 6GB/128GB MRP Rs 24,999 (Smartprix/TelecomTalk, Jun 30 2026). Dimensity 6360 Apex, 8000mAh. A1 resale estimated conservative.',
    },
    # Oppo Reno 16 5G (Snapdragon 7 Gen 4, 6.32in AMOLED)
    'oppo_reno_16_8_256': {
        'display_name': 'Oppo Reno 16 5G 8/256GB', 'tier': 'A',
        'discontinued': False, 'launch_date': '2026-07-02',
        'resale_target_a1': 41000, 'calibration_status': 'estimated', 'calibration_date': TODAY,
        'live_source': 'Oppo Reno 16 5G launched India Jul 2 2026 (Snapdragon 7 Gen 4). 8GB/256GB MRP Rs 61,999 (TelecomTalk/Digit/ETV Bharat). Sale Jul 9. A1 resale estimated ~66% of new.',
    },
    'oppo_reno_16_12_256': {
        'display_name': 'Oppo Reno 16 5G 12/256GB', 'tier': 'A',
        'discontinued': False, 'launch_date': '2026-07-02',
        'resale_target_a1': 45000, 'calibration_status': 'estimated', 'calibration_date': TODAY,
        'live_source': 'Oppo Reno 16 5G 12GB/256GB MRP Rs 67,999 (TelecomTalk/Digit, Jul 2 2026). Snapdragon 7 Gen 4. A1 resale estimated ~66% of new.',
    },
    # Oppo Reno 16C 5G (Dimensity 7300, 6.57in AMOLED)
    'oppo_reno_16c_8_128': {
        'display_name': 'Oppo Reno 16C 5G 8/128GB', 'tier': 'B',
        'discontinued': False, 'launch_date': '2026-07-02',
        'resale_target_a1': 29000, 'calibration_status': 'estimated', 'calibration_date': TODAY,
        'live_source': 'Oppo Reno 16C 5G launched India Jul 2 2026 (Dimensity 7300). 8GB/128GB MRP Rs 46,999 (TelecomTalk/Digit/ETV Bharat). Sale Jul 9. A1 resale estimated conservative (Dimensity 7300 depreciates faster than price implies).',
    },
    'oppo_reno_16c_8_256': {
        'display_name': 'Oppo Reno 16C 5G 8/256GB', 'tier': 'B',
        'discontinued': False, 'launch_date': '2026-07-02',
        'resale_target_a1': 31000, 'calibration_status': 'estimated', 'calibration_date': TODAY,
        'live_source': 'Oppo Reno 16C 5G 8GB/256GB MRP Rs 49,999 (TelecomTalk/Digit, Jul 2 2026). Dimensity 7300. A1 resale estimated conservative.',
    },
    'oppo_reno_16c_12_256': {
        'display_name': 'Oppo Reno 16C 5G 12/256GB', 'tier': 'B',
        'discontinued': False, 'launch_date': '2026-07-02',
        'resale_target_a1': 34000, 'calibration_status': 'estimated', 'calibration_date': TODAY,
        'live_source': 'Oppo Reno 16C 5G 12GB/256GB MRP Rs 55,999 (TelecomTalk/Digit, Jul 2 2026). Dimensity 7300. A1 resale estimated conservative.',
    },
}

# anti-duplicate guard
for k in NEW:
    assert k not in db, f'key already exists: {k}'

db.update(NEW)

# meta bump
meta = db['_meta']
meta['version'] = '4.9'
meta['last_calibration'] = TODAY
meta['v4_9_changelog'] = (
    "Weekly refresh (2026-07-03). Added 7 new India launch variants since last calibration: "
    "OnePlus N6 (Jun 30, budget Dimensity 6360 N-series, 4/128 + 6/128 — distinct from Nord 6); "
    "Oppo Reno 16 5G (Jul 2, Snapdragon 7 Gen 4, 8/256 + 12/256); "
    "Oppo Reno 16C 5G (Jul 2, Dimensity 7300, 8/128 + 8/256 + 12/256). "
    "All anchored on resale_target_a1 (estimated, conservative, resale<=~66-75% of new, implied buyback A1 < new). "
    "Price refresh: full-DB live verification was completed 8 days prior (v4.5, 2026-06-25); "
    "spot-check of top hot models (iPhone 15/16/16 Pro Max, Samsung S24/S25 Ultra) vs live July-2026 Cashify/market "
    "confirmed anchors still hold (<10% divergence) — no mass rewrite, no override changes (guardrail: conservative is safe). "
    "Skipped (not yet launched as of Jul 3): Nothing Phone 4b (Jul 7), Samsung Z Fold 8, Vivo S2, Moto Razr 70 Ultra."
)

json.dump(db, open(DB_PATH, 'w'), ensure_ascii=False, indent=2)
print('phone_db.json written. total entries:', len([k for k in db if not k.startswith('_')]))

# Update inlined DB line in index.html
compact = 'const DB = ' + json.dumps(db, ensure_ascii=False, separators=(',', ':')) + ';'
lines = open(HTML_PATH, encoding='utf-8').read().splitlines(keepends=True)
found = 0
for i, line in enumerate(lines):
    if line.strip().startswith('const DB = {'):
        nl = '\n' if line.endswith('\n') else ''
        lines[i] = compact + nl
        found += 1
assert found == 1, f'expected 1 DB line, found {found}'
open(HTML_PATH, 'w', encoding='utf-8').write(''.join(lines))
print('index.html DB line updated (found %d line)' % found)
