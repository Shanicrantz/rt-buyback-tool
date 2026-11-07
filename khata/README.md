# RT Khata

Khata-style receivables screen for Rajdhani Telecom: who owes how much, how old the
dues are, and one-tap WhatsApp / SMS payment reminders. Data comes live from
NiryatBooks (Rajdhani Telecom org) on every open and every 5 minutes while open.

```
khata/
  public/index.html              the page (no customer data in it)
  netlify/functions/khata.mjs    PIN check + read-only NiryatBooks bridge, at /api/khata
  netlify.toml                   site config (publish = public, functions)
  test_khata.mjs                 node khata/test_khata.mjs  (synthetic data only)
```

## Why a separate Netlify site

The weekly buyback refresh publishes exactly the seven buyback runtime files to
`rt-buyback-tool`. A Netlify deploy replaces the whole site, so a khata page or function
on that site would vanish on the next refresh. On its own site (`rt-khata`) the weekly
runs cannot touch it. The buyback header gets a "Khata" link once this site is live.

## How data flows

1. Staff open the page and enter the PIN. The PIN is checked on the server
   (`KHATA_PIN`); 8 wrong tries lock that IP for 15 minutes.
2. `summary` → one `get_aging` call (receivables) → customers grouped, biggest first.
3. `contacts` → phone + vendor flag for up to 10 names per call (`list_contacts`,
   exact-name match, customer-tagged contact preferred). Cached 10 min per warm instance.
4. `customer` → `list_invoices` + `list_payments` for the contact that owns the open bills.

The browser never sees the NiryatBooks token and never names a tool; the function
only ever calls `get_aging`, `list_contacts`, `list_invoices`, `list_payments`.
All responses are `Cache-Control: no-store` and use POST, so no service worker
or browser cache keeps customer data.

Reminders open WhatsApp (`wa.me`) or SMS with the message filled in; staff press Send.
Nothing is sent automatically. Numbers typed by staff and the "yaad dilaya" log are
stored in that device's browser only.

## One-time setup

1. **NiryatBooks token.** In NiryatBooks (Rajdhani Telecom), issue an MCP token for a
   user that can read Money reports and Contacts (the Accountant / bookkeeper role is
   enough). Avoid an admin token: the bridge only reads, but a viewer token keeps the
   blast radius small if it ever leaks.
2. **Netlify site.** Already created on 2026-11-07: `rt-khata`
   (https://rt-khata.netlify.app, site id `b0f35f1b-0734-4b66-a16c-00b6e27f9e87`).
   Redeploy from this folder — always pass the site id, because the parent folder is
   linked to `rt-buyback-tool`:
   ```
   cd khata
   netlify deploy --prod --dir=public --functions=netlify/functions --site b0f35f1b-0734-4b66-a16c-00b6e27f9e87
   ```
3. **Environment variables** (Netlify → rt-khata → Site configuration → Environment
   variables), then redeploy:

   | Name | Required | Value |
   |---|---|---|
   | `NB_RT_TOKEN` | yes | the token from step 1 |
   | `KHATA_PIN` | yes | staff PIN, 6+ digits |
   | `RT_UPI_ID` | no | shop UPI ID shown in messages |
   | `RT_SHOP_PHONE` | no | shop number shown in messages |
   | `NB_RT_MCP_URL` | no | defaults to `https://niryatbooks.com/api/mcp/rajdhani-telecom-c86r` |

Until the two required variables are set, the page shows a setup card instead of data.

## Known limits

- NiryatBooks `get_aging` returns the customer *name*, not the contact id, so phones are
  matched by exact display name. Adding `contact_id` and `phone` to its rows would make
  the list a single call and remove the name matching.
- On 2026-11-07 only 351 of 10,138 RT customers had a phone number in NiryatBooks
  (10 of the 27 contacts with dues). Staff can type a number per device; it should also
  be added to the NiryatBooks contact.
- NiryatBooks allows 60 calls/minute per token. A cold open costs about one call per
  customer with dues (~27 today).
