# Host the app at buyback.rajdhanitelecom.com

The tool is live on Netlify (site `rt-buyback-tool`, id `7b706fe7-9260-4d82-a0ff-263413316382`).
To serve it from your own domain as a subdomain, two quick steps — both need YOUR access
(Netlify dashboard + your domain's DNS). I can't do these from here (no DNS access, and no
domain-add tool in this session).

## Step 1 — Add the subdomain in Netlify (2 min)
1. app.netlify.com → project **rt-buyback-tool** → **Domain management** → **Add a domain**.
2. Enter: **buyback.rajdhanitelecom.com** → Verify → Add.
3. Netlify will show the DNS target — it will be **`rt-buyback-tool.netlify.app`** (a CNAME target).

## Step 2 — Add the DNS record (wherever rajdhanitelecom.com DNS lives)
Log in to your domain's DNS manager (GoDaddy / Hostinger / Cloudflare / BigRock — whoever hosts
rajdhanitelecom.com) and add:

| Type  | Name / Host | Value / Target             | TTL   |
|-------|-------------|----------------------------|-------|
| CNAME | `buyback`   | `rt-buyback-tool.netlify.app` | Auto / 3600 |

> If your DNS is on **Cloudflare**, set the record to **DNS only (grey cloud)** first so Netlify can
> issue SSL; you can turn the proxy on after the cert is live.

## Step 3 — SSL (automatic)
Once DNS propagates (5 min – a few hrs), Netlify auto-issues a Let's Encrypt certificate.
Then **https://buyback.rajdhanitelecom.com** is live with the padlock.

## After it's live
- The mobile app (`_mobile-app/`) already points at `https://buyback.rajdhanitelecom.com`, so it'll work once the subdomain resolves.
- The old `rt-buyback-tool.netlify.app` URL keeps working too (optional: set a redirect to the custom domain in Netlify).
- Tell me once the CNAME is added and I'll verify it resolves + SSL is good.

**Which DNS provider hosts rajdhanitelecom.com?** Tell me and I'll give the exact click-path for that provider.
