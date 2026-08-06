# RT Buyback — iOS + Android App: Build & Store Submission Runbook

The app is a **Capacitor** native shell that loads the live site
(`https://buyback.rajdhanitelecom.com`). Rate updates flow through automatically —
**no app re-submission needed when rates change.** Only re-submit for app-shell changes.

---

## ⚠️ What only YOU can do (I can't, by design)
| Step | Why it needs you | Cost |
|---|---|---|
| Apple Developer account | Requires your Apple ID + payment + accepting Apple's legal agreement | **$99 / year** |
| Google Play Console account | Requires your Google account + payment + agreement | **$25 one-time** |
| Signing (Apple certs / Android keystore) | Tied to your identity; must be created & stored by you | — |
| Uploading builds + store listing + hitting "Submit" | Publishing under your name; entering store credentials | — |

I scaffolded the project, config, icons, and these exact steps. You (or me guiding you live on your Mac) run the build + submit.

---

## Part A — One-time local setup (your Mac)
```bash
cd "_mobile-app"
npm install
npx cap init "RT Buyback" com.rajdhanitelecom.buyback --web-dir=www
npx cap add ios
npx cap add android
npx cap sync
```
Copy app icons from the repo root (`icon-512.png`, `apple-touch-icon.png`) into the generated
`ios/` and `android/` icon sets (or run an icon generator like `@capacitor/assets`).

---

## Part B — Android → Google Play  (easiest, highest approval)
1. Open the project: `npx cap open android` (opens Android Studio).
2. Build → Generate Signed Bundle → **Android App Bundle (.aab)**. Create a **keystore** when prompted and **back it up safely** (losing it = can't update the app ever).
3. Go to **Google Play Console** → Create app → fill listing (name, description, screenshots, privacy policy URL).
4. Upload the `.aab` → Production track → Submit for review.
5. Review is usually **hours–2 days**. TWA/webview shells are accepted by Google.

> Alternative (cleaner for a PWA): **Bubblewrap / PWABuilder** can generate a signed Play AAB straight from `https://buyback.rajdhanitelecom.com` — https://www.pwabuilder.com

---

## Part C — iOS → App Store
1. Open the project: `npx cap open ios` (opens Xcode).
2. Signing & Capabilities → select your Apple Developer **Team**; set bundle id `com.rajdhanitelecom.buyback`.
3. Set version + build number, add app icon.
4. Product → Archive → Distribute App → App Store Connect → Upload.
5. In **App Store Connect**: create the app, fill listing + screenshots + privacy, attach the build, Submit for review.
6. Review is usually **1–3 days**.

> ⚠️ **Apple risk (guideline 4.2.2):** a pure "loads a website" wrapper can be rejected for
> "minimum functionality." Mitigations if rejected: (a) ship the app **fully offline-bundled**
> instead of remote-URL (I can refactor the app so the phone DB is fetched separately, keeping
> rates fresh without re-submission), and (b) add a native touch (native share sheet for quotes,
> Face ID lock instead of the web password). Ask me and I'll implement whichever Apple wants.

---

## Recommended order
1. **Ship the PWA first** (already done — "Add to Home Screen" gives a full app on both platforms today, zero cost/review).
2. **Google Play** next (cheap, fast, reliable).
3. **Apple App Store** last (most friction; be ready for the 4.2.2 conversation).

App id: `com.rajdhanitelecom.buyback` · Name: **RT Buyback** · Loads: `https://buyback.rajdhanitelecom.com`
