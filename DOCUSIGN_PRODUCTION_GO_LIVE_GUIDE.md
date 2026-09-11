# DocuSign production Go-Live guide (live account)

Use this when Settings → **Email & E-signature** on production can only
connect a **demo** DocuSign account, and you need a **live** account so
signed documents are legally valid (no “DEMONSTRATION DOCUMENT”
watermark).

Companion for sandbox / local / EC2-dev setup:
[DOCUSIGN_SETUP_GUIDE.md](DOCUSIGN_SETUP_GUIDE.md).

No application code change is required. The Connect button always follows
the **backend** DocuSign environment. Until production is pointed at
live DocuSign, the popup can only complete a demo login.

**Recorded production state (20 Aug 2026):**
`/velvet-elves/prod/backend` still had
`DOCUSIGN_OAUTH_BASE_URL=https://account-d.docusign.com` and
`DOCUSIGN_BASE_URL=https://demo.docusign.net/restapi`. Re-check those
values before starting; they are the reason a live password cannot be
used on `https://app.velvetelves.com`.

Official DocuSign references:

- [Go-Live](https://developers.docusign.com/platform/go-live/)
- [eSignature Go-Live](https://developers.docusign.com/docs/esign-rest-api/go-live/)
- [Integration Keys and Go Live FAQ](https://support.docusign.com/s/articles/DocuSign-Developer-FAQs-Integration-Keys-and-Go-Live?language=en_US)

---

## 1. Why Connect is stuck on demo

There are two layers. Both must be production before a live user works.

| Layer | What it is | Current production state |
| --- | --- | --- |
| **App (Integration Key)** | The “Velvet Elves” OAuth app that Connect uses | Still the **developer** key (`account-d.docusign.com`) |
| **User account** | Jake’s (and each agent’s) DocuSign login, so envelopes send as that person | Can only be a **demo** user until the app is live |

Demo and production are separate DocuSign worlds:

| Environment | Admin | OAuth host | REST API host |
| --- | --- | --- | --- |
| Demo (keep for staging / local) | `https://apps-d.docusign.com/admin` or `https://admindemo.docusign.com` | `https://account-d.docusign.com` | `https://demo.docusign.net` |
| Production (target) | `https://apps.docusign.com/admin` or `https://admin.docusign.com` | `https://account.docusign.com` | Regional, e.g. `https://na3.docusign.net` — never `demo.docusign.net` |

Signing into a paid live account in the current popup will not make
envelopes legally live. The popup is still the demo identity server.

After promotion, DocuSign **copies** the Integration Key GUID into
production; it does **not** move it. The demo secret, redirect URIs, and
Connect webhooks are **not** copied. Staging and local stay on demo.

---

## 2. Ask Jake (client / project owner) for these

These are account, billing, and identity items. The developer sandbox
cannot finish this alone.

### 2.1 A paid production DocuSign account (blocking)

- **Paid, API-eligible plan.** DocuSign requires **Business Pro or
  higher**. Trial, free, and developer/demo accounts **cannot** receive
  a promoted key.
- **Not** the developer account at `account-d.docusign.com` /
  `apps-d.docusign.com`.
- Confirm the account can send **eSignature API** envelopes (the product
  Velvet Elves uses).

Project billing notes already assume a ~$45/month DocuSign line; confirm
the live invoice is a **production** plan, not only a developer sandbox.

### 2.2 An Administrator on that live account

Go-Live opens a popup that must be signed in as an **Administrator** of
the **production** account. Jake should either:

- do that login himself during the promotion call, or
- name a DocuSign admin and have that person available for 15–30 minutes.

### 2.3 Corporate email on that admin user

DocuSign often **rejects** Go-Live when the production admin is
`@gmail.com` / `@yahoo.com` / similar. The promoting admin should use an
address on the brokerage domain.

### 2.4 Identity verification, if DocuSign asks

Some promotions require photo ID + selfie. Jake (or the admin) must
complete that; the developer cannot do it for him.

### 2.5 Confirm the integration type (one sentence from Jake)

For Velvet Elves as **Jake’s brokerage product** (his team connects
DocuSign; envelopes go out under their users):

> **Private custom integration** — internal app for our own DocuSign
> account and users.

Choose **Public / Embedded / Partner** only if other brokerages will
connect **their own** DocuSign accounts. That path needs the DocuSign
Partner program and a different license. Do not pick it unless Jake
explicitly wants a multi-brokerage ISV.

### 2.6 A 30–60 minute working session (or async equivalents)

Jake (or his DocuSign admin) must:

1. Sign into **production** when Go-Live asks.
2. After approval, stay in **production Admin** so the developer can add
   the production redirect URI, generate a **new** secret, and create
   Connect.
   - If he will not grant admin access: he generates the secret and HMAC
     key, copies each **once** into a password manager, and sends them
     to the developer. DocuSign will not show those values again.

### 2.7 Who must reconnect after cutover

Every production user who already clicked Connect (Jake, Audri, agents)
must **Disconnect → Connect** on Settings → Email & E-signature
**after** the backend swap. Old tokens are demo tokens and stay invalid
for live envelopes.

### 2.8 Optional but useful

- Privacy policy URL if DocuSign asks: `https://velvetelves.com/privacy`.
- Confirmation that **staging should stay on demo** (recommended).

**Do not ask Jake to “create a new Integration Key in production” as the
first path.** The existing demo app **Velvet Elves** was already
**Ready to Submit / Promote to production** (verified 2026-04-21).
Promoting that key is the intended path. A brand-new production key is
only a fallback if promotion is refused.

---

## 3. What the solo developer does

Work in this order. Do **not** update AWS secrets until DocuSign shows
the key as **Live** on the **production** Apps and Keys page.

### 3.A Confirm the consoles

Use the table in §1. Production work happens on `account.docusign.com` /
`admin.docusign.com`. Do not change production to the demo hosts.

### 3.B Promote the existing Integration Key (Go-Live)

1. Sign in to the **developer** Apps and Keys page.
2. Open the **Velvet Elves** app.
3. Set **Integration type** to **Private custom integration** (unless
   Jake chose otherwise).
4. Start **Go Live** / **Promote to production**.
5. When the production login popup appears, **Jake (admin) signs into
   the paid live account**. Disable popup blockers first.
6. If DocuSign approves instantly, the same Integration Key GUID appears
   on the **production** Apps and Keys page with status **Live**. If it
   goes to review, wait (often 24–48 hours; can be 1–3 business days).
7. Leave the **demo** key in place for staging. Do not delete it.

### 3.C Configure the key in production (nothing copies automatically)

In **production** Apps and Keys → Velvet Elves → Edit:

1. **Redirect URI** — exact string, no trailing slash:

   ```text
   https://api.prod.velvetelves.com/api/v1/integrations/docusign/callback
   ```

   Do **not** register `https://app.velvetelves.com/...`. The SPA is
   `app.velvetelves.com`; the OAuth callback must hit the **API**.

2. **Secret key** — click Add Secret / Generate. Copy it immediately.
   This is **not** the demo `DOCUSIGN_SECRET_KEY`. Same GUID, new secret.

3. OAuth type remains **Authorization Code Grant**. Scopes stay
   `signature` (already sent by the backend; no extra admin toggle).

4. Copy **Account Base URI** from the production “My Account Information”
   panel (example: `https://na3.docusign.net` — use whatever that
   account actually shows). Production hosts are regional (`na1`–`na4`,
   `eu`, `ca`, `au`, …), never `demo.docusign.net`.

### 3.D Production DocuSign Connect (required for auto “Signed”)

Without this, documents stay on **Sent for Signature** until someone
clicks **Refresh Signature Status**.

In **production** Admin → Integrations → Connect (not the demo Connect
page):

1. **+ Add Configuration → Custom**
   - Name: `Velvet Elves — production`
   - URL to Publish:
     `https://api.prod.velvetelves.com/api/v1/esign/webhooks/docusign`
   - Enable Log: On
   - Require Acknowledgement: On
   - Include Documents: On
   - Send Message Format: **JSON** (XML will fail)
2. Envelope events: **Completed**, **Declined**, **Voided** (Sent /
   Delivered optional).
3. Associated Users: **All Users** on Jake’s production account (covers
   agents on that same account).
4. **Connect Keys** → generate HMAC secret → copy once.
5. Edit the configuration → **Include HMAC Signature** On → Save.

If later other brokerages connect **separate** DocuSign accounts, each
of those accounts needs its own Connect config (or a partner Connect
setup). For Jake’s team on one brokerage account, one production Connect
config is enough.

### 3.E Point production ECS at live DocuSign

Update AWS Secrets Manager secret **`/velvet-elves/prod/backend`**
(us-east-2). Do not hand-edit a file on a running task. Then **force a
new ECS deployment** so tasks reload secrets (`velvet-elves-prod-backend`).
A secret change is ignored by already-running tasks.

Set:

```text
DOCUSIGN_INTEGRATION_KEY=<same GUID as today>
DOCUSIGN_SECRET_KEY=<NEW production secret from 3.C>
DOCUSIGN_OAUTH_BASE_URL=https://account.docusign.com
DOCUSIGN_REDIRECT_URI=https://api.prod.velvetelves.com/api/v1/integrations/docusign/callback
DOCUSIGN_WEBHOOK_SECRET=<NEW production HMAC from 3.D>
DOCUSIGN_BASE_URL=https://<Account Base URI from prod Apps and Keys>/restapi
DOCUSIGN_SCOPES=signature
```

Example if Account Base URI is `https://na3.docusign.net`:

```text
DOCUSIGN_BASE_URL=https://na3.docusign.net/restapi
```

OAuth already uses `DOCUSIGN_OAUTH_BASE_URL`. After a user connects, the
API host comes from DocuSign `/oauth/userinfo` (`base_uri` stored on the
integration row). `DOCUSIGN_BASE_URL` is the fallback used when no
per-user URI exists (including `is_demo` detection before connect).

Leave **`/velvet-elves/stage/backend`** on `account-d` /
`demo.docusign.net` and the **demo** secret.

### 3.F Users reconnect (developer coordinates; they click)

On **https://app.velvetelves.com** → Settings → **Email & E-signature**:

1. If DocuSign shows Connected: **Disconnect**.
2. **Connect**.
3. The popup host must be **`account.docusign.com`** (no `-d`). If it is
   still `account-d`, the ECS task did not pick up the new secret —
   check the secret JSON keys and force another deployment.
4. Sign in with the **live** DocuSign user (the paid account), click
   Allow Access.

Each person who sends envelopes must do this. Tokens are per-user.

### 3.G Prove it is live

1. Send a throwaway document for signature from All Documents.
2. Signed PDF must **not** say **DEMONSTRATION DOCUMENT**. The in-app
   demo banner (`is_demo`) must be gone.
3. Within ~30 seconds, Connect Logs for **Velvet Elves — production**
   show **Success 200**, and the row flips to **Signed**.
4. Health check: `https://api.prod.velvetelves.com/api/v1/health` still
   200 after the ECS bounce.

If Connect logs **401**, the HMAC in Secrets Manager does not match. If
**no log**, the envelope was still sent on demo or Connect is on the
wrong account.

---

## 4. Split of labor

| Step | Jake | Solo developer |
| --- | --- | --- |
| Buy/confirm paid production DocuSign (Business Pro+) | Yes | Remind; do not use demo |
| Production admin + corporate email | Yes | — |
| Integration type = Private custom (unless he wants ISV) | Decide | Select in Go-Live form |
| Sign into production during Promote | Yes (or his admin) | Start Go-Live from demo Apps and Keys |
| ID verification if prompted | Yes | — |
| New production secret + HMAC | Approve access, or copy values once | Generate in prod Admin, store in Secrets Manager |
| Redirect URI + Connect JSON webhook | Access to prod Admin | Configure exact URLs in §3.C and §3.D |
| Update `/velvet-elves/prod/backend` + ECS redeploy | — | Yes |
| Disconnect / Connect on production Settings | Jake + every sending user | Send the reconnect instructions |
| Test envelope, watermark, webhook | Optional witness | Required before calling it done |

---

## 5. What will not work

- Connecting a live password while the popup is still
  `account-d.docusign.com`.
- Copying the **demo** secret or HMAC into production.
- Registering the callback on `app.velvetelves.com` instead of
  `api.prod.velvetelves.com`.
- Switching staging to production URLs (breaks demo QA).
- Expecting old Connected rows to start sending live envelopes without
  Disconnect → Connect.
- Writing application code for this cutover.

Until Go-Live is **Live**, production Admin has the new secret and
Connect config, and ECS has been bounced onto
`https://account.docusign.com`, Settings → Email & E-signature can only
attach a demo account.

---

## 6. Production URLs (copy-paste)

| Purpose | URL |
| --- | --- |
| App (users click Connect here) | `https://app.velvetelves.com/settings/connections` |
| OAuth callback (register in DocuSign) | `https://api.prod.velvetelves.com/api/v1/integrations/docusign/callback` |
| Connect webhook (register in DocuSign Connect) | `https://api.prod.velvetelves.com/api/v1/esign/webhooks/docusign` |
| Production OAuth host | `https://account.docusign.com` |
| AWS secret | `/velvet-elves/prod/backend` (us-east-2) |
| ECS service to bounce | `velvet-elves-prod-backend` |

Staging equivalents stay on demo. Do not reuse the production callback
or webhook on the demo Integration Key as a substitute for Go-Live.
