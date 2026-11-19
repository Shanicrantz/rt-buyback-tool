#!/bin/bash
# Fetch abest.in product pages (plain GET, same page a browser opens), save gzipped raw HTML for evidence.
D="$(cd "$(dirname "$0")" && pwd)"; OUT="$D/research/abest/html"; mkdir -p "$OUT"
while read -r u; do
  f="$OUT/$(basename "$u").html.gz"; [ -s "$f" ] && continue
  code=$(curl -sL -A "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130 Safari/537.36" --max-time 30 -o "$OUT/tmp.html" -w "%{http_code}" "$u")
  if [ "$code" = 200 ]; then gzip -c "$OUT/tmp.html" > "$f"; else echo "$code $u" >> "$D/research/abest/errors.txt"; fi
  echo "$(date -u +%FT%TZ) $code $u" >> "$D/research/abest/fetch.log"
  sleep 0.7
done < "$D/research/abest/urls.txt"
rm -f "$OUT/tmp.html"
