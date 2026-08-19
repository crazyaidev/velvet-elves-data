# Google OAuth Reviewer Testing Guidelines

**Prepared for:** Google Trust and Safety / Third-Party Data Safety reviewers
**Application:** Velvet Elves
**Legal entity:** Orange Door, LLP, doing business as Velvet Elves (Indiana, USA)
**Date:** August 18, 2026
**Environment:** Production only — `https://app.velvetelves.com`
**Support:** `support@velvetelves.com`

---

## 1. Purpose of this document

This guide lets a reviewer sign in to the live Velvet Elves application, walk the product, and exercise every Google scope declared on the OAuth consent screen — without phone verification, payment, or other blockers.

Velvet Elves is transaction coordination software for real estate agents and brokerages. Gmail and Google Calendar are optional connections a signed-in user makes from inside the product. Google user data is used only for the features demonstrated below.

A demonstration video of the same production workspace is linked in Section 2. The test account below is the account shown in that video.

Typical review time: about 15–20 minutes.

---

## 2. Test credentials and demonstration video

Use the credentials in the table below. They open the same production workspace shown in the demonstration video. Sign in with **email and password** on the Velvet Elves **Welcome back** form. Do not click the **Google** button on the login page — that is a separate identity login, not the Gmail integration under review.

| Item | Value |
| --- | --- |
| Application URL | https://app.velvetelves.com |
| Sign-in email | Insert before sending |
| Password | Insert before sending |
| Demonstration video (public YouTube) | Insert before sending |

**Authentication blockers removed**

- No phone-number verification
- No two-factor / SMS / authenticator prompt
- No credit card, purchase, or billing step is required to review the product or the Google integrations
- Do not create a new transaction. Existing deals in this workspace are sufficient, and new-file creation is unrelated to OAuth review

If a first-time product tour overlay appears after sign-in, dismiss it and continue with the steps below.

---

## 3. Browser setup

1. Use Google Chrome (desktop).
2. Allow pop-ups for `https://app.velvetelves.com`. Gmail and Calendar connect in a Google OAuth popup. If the popup is blocked, Chrome will show a blocked-popup icon in the address bar — click it, allow pop-ups, and try **Connect** again.
3. Keep the address bar visible.
4. Sign out of extra Google accounts in the browser, or use a clean Chrome profile, so the account chooser is unambiguous.

The app is still pending Google verification, so the **"Google hasn't verified this app"** warning is expected. On that screen click **Advanced**, then **Go to Velvet Elves (unsafe)**. Please do not treat that warning as a product defect.

---

## 4. Public pages (no login)

These pages are on the authorized domain and match the OAuth consent-screen branding.

| Page | URL |
| --- | --- |
| Home | https://velvetelves.com/ |
| Privacy policy (Google user data) | https://velvetelves.com/privacy#google |
| Data deletion | https://velvetelves.com/data-deletion |
| Terms | https://velvetelves.com/legal |

On the privacy page, the section **Google user data (Gmail and Calendar)** names the read, send, and calendar features, states that mailbox modification is not requested, and includes the Limited Use disclosure.

---

## 5. Scopes under review

Velvet Elves uses **one** production OAuth client and **two** user-initiated consents. Code, Cloud Console Data Access, and the live consent screens request these exact strings.

**Consent 1 — Connect Gmail** (`Settings → Email & E-signature → Connect` on Gmail)

| Scope | Classification | User-facing result |
| --- | --- | --- |
| `openid` | Basic | Identifies the Google account the user connected |
| `https://www.googleapis.com/auth/userinfo.email` | Basic | Shows the connected mailbox address in Settings |
| `https://www.googleapis.com/auth/userinfo.profile` | Basic | Shows the connected account name in Settings |
| `https://www.googleapis.com/auth/gmail.readonly` | Restricted | Reads inbound mail so it can be matched to a transaction, logged, and used to draft a reply |
| `https://www.googleapis.com/auth/gmail.send` | Sensitive | Sends one transaction-specific message, only after the user clicks **Approve & send** |

**Consent 2 — Connect Google Calendar** (`Workflow → Closing Calendar → Connect calendar → Google Calendar`)

| Scope | Classification | User-facing result |
| --- | --- | --- |
| `openid` | Basic | Identifies the Google account the user connected |
| `https://www.googleapis.com/auth/userinfo.email` | Basic | Shows the connected calendar account |
| `https://www.googleapis.com/auth/calendar.events` | Sensitive | Writes that user's transaction deadlines to their own Google Calendar, at their request |

No other Google scopes are requested. In particular the app does **not** request `https://mail.google.com/`, `gmail.modify`, `gmail.metadata`, `gmail.compose`, or `calendar.readonly` / `calendar`.

---

## 6. Why these scopes, and why narrower ones are not enough

Google asked for a justification that ties each scope to a user-facing feature. The walkthrough in Section 8 is that evidence. In short:

**`gmail.readonly`.** Inbound transaction email is matched to the correct deal, stored on that deal's communication record, shown in **Intelligence → Email → Inbox**, and used as context for a suggested reply. Matching uses the message body (property address, party names, dates). Drafting a reply requires the same body. `gmail.metadata` cannot supply that content, so it cannot implement the feature.

**`gmail.send`.** After a person reads the draft and clicks **Approve & send** (or **Send edited reply**), Velvet Elves calls `users.messages.send` so the reply leaves from the user's own Gmail address, one message at a time. The AI drafts; it does not send. There is no bulk send and no send without that click. A send-less scope cannot deliver this feature.

**`calendar.events`.** Closing dates and related deadlines already exist in the transaction file. When the user connects Google Calendar and clicks **Add my closings**, those dates are created or updated on the user's calendar. The app does not read or process unrelated calendar data. `calendar.readonly` cannot write events; a broader calendar scope is unnecessary.

Google user data is not sold, not used for advertising, not used to determine creditworthiness, and not used to train generalized or foundation AI models.

---

## 7. What you should see in the product (orientation)

Velvet Elves is a working brokerage workspace, not a Gmail wrapper. Before connecting Google, please confirm the product itself:

After sign-in you land on a **Dashboard**. The dark left sidebar is grouped as **Deals**, **Workflow**, and **Intelligence**.

**Deals → Active Transactions** (`https://app.velvetelves.com/transactions`) lists live files with property addresses, stages, and closing dates.

Opening any deal opens a workspace with tabs including **Timeline**, **Tasks**, **Documents**, **Compliance**, **Contacts**, **Email**, and **Activity**. A signed contract on a file is what the system uses to build deadlines, the task plan, and the document checklist.

You do not need to create, edit, or delete anything in this orientation. Existing seeded transactions are enough.

---

## 8. Step-by-step test

Follow these steps in order. Direct URLs are included so a step cannot get lost in navigation.

### Step A — Sign in

1. Open `https://app.velvetelves.com`.
2. On **Welcome back**, enter the **Email address** and **Password** from Section 2.
3. Click **Sign In**.
4. Confirm you land in the signed-in app (Dashboard or Active Transactions). The address bar remains on `app.velvetelves.com`.

### Step B — Confirm the book of business

1. In the left sidebar, under **Deals**, click **Active Transactions** (or go to `https://app.velvetelves.com/transactions`).
2. Note that several transactions are listed, at different stages, each with a property address.
3. Open one deal. Copy its **property address** — you will put that address in a test email in Step D.
4. Optionally click **Timeline**, **Tasks**, **Documents**, and **Contacts** on that deal so the file is visible as a real transaction, not an empty shell.

### Step C — Connect Gmail (consent screen 1)

Gmail and Calendar are **separate** consents. This step is Gmail only.

1. In the left sidebar, click **Settings** (near the bottom).
2. Open the **Email & E-signature** card. Direct URL: `https://app.velvetelves.com/settings/connections`.
3. If Gmail already shows **Connected**, click **Disconnect**, read the confirmation (inbound sync and send will stop), and confirm **Disconnect**. This is required so the consent screen can be shown again.
4. On Gmail, click **Connect**. Allow the popup if Chrome blocks it.
5. Choose a Google account you control (a throwaway Gmail is fine). This is the mailbox the app will read and send from.
6. If **Google hasn't verified this app** appears, click **Advanced**, then **Go to Velvet Elves (unsafe)**.
7. **Stop on the consent screen.** Confirm the app name is **Velvet Elves**. Scroll so every permission is readable. You should see identity (email / profile) plus Gmail read and Gmail send. You should **not** see mailbox modify, full `mail.google.com` access, or Calendar on this screen.
8. Allow / continue.
9. Return to Velvet Elves. Gmail should show **Connected** with the mailbox address.
10. Click **Test connection** and confirm a successful result.

### Step D — `gmail.readonly` and `gmail.send` end to end

**D1. Send a test inbound message**

From any second mailbox you control (not the connected Gmail), send a short message:

- **To:** the connected Gmail address shown in Settings
- **Subject:** `Question about [property address] closing`
- **Body:** `Hi, can you confirm the closing date for [property address]? Thank you.`

Replace `[property address]` with the address you copied in Step B. The body must mention that address so the app can match the message to the deal.

Wait up to two minutes, then continue. Inbound delivery uses Gmail push; a short delay is normal.

**D2. Read and match (`gmail.readonly`)**

1. In the left sidebar, under **Intelligence**, click **Email**. Direct URL: `https://app.velvetelves.com/ai-emails`.
2. Open the **Inbox** tab. Click **Refresh** if the message is not yet listed.
3. Click the row. The right pane shows the original message. If a reply was drafted, the row is tagged **Reply ready** and the pane includes **Original message** and a suggested reply. The row should show the deal address, not **Not linked**.
4. Confirm the same message on the deal: open the transaction from Step B → **Email** tab → **Inbox**.
5. On that deal, open **Activity** and **Communications**. The inbound message should be logged (for example **Matched by party**, Received, Gmail).
6. Note the category chip (a closing-date question is typically **Question**) and that the body was read — matching and drafting are not possible from metadata alone.

**D3. Human approval, then send (`gmail.send`)**

1. Stay on **Intelligence → Email**. Open **Outbox** if the draft is not already in the Inbox reading pane.
2. Confirm recipient, subject, and body. The on-screen line is **Nothing sends until you approve it**.
3. Click **Edit**, change a word, and confirm the edit persists. This shows a person controls the final text.
4. Click **Approve & send** (or **Send edited reply** if you are still in edit mode).
5. Confirm the message in **Intelligence → Email → Sent**.
6. Confirm the same message on the deal's **Email** tab (**Sent**).
7. Optionally open the connected Gmail **Sent** folder. The message should have been sent from the user's own address.

Velvet Elves does not send this message — or any Gmail message — until that click.

### Step E — Connect Google Calendar (consent screen 2)

This is a **second** OAuth grant. Calendar is not included in the Gmail consent.

1. In the left sidebar, under **Workflow**, click **Closing Calendar**. Direct URL: `https://app.velvetelves.com/calendar`.
2. If Google Calendar is already connected, disconnect it from the **Calendars** menu so the consent screen can be shown again.
3. Click **Connect calendar**, then **Google Calendar**. Allow the popup if Chrome blocks it.
4. Complete Google sign-in. If the unverified-app warning appears, use **Advanced** → **Go to Velvet Elves (unsafe)** again.
5. **Stop on this second consent screen.** Confirm it requests Calendar event access (`calendar.events`) plus identity. It should **not** request Gmail scopes or full calendar read of unrelated events.
6. Allow / continue and return to Closing Calendar.

### Step F — `calendar.events` end to end

1. Still on Closing Calendar, click **Add my closings**.
2. Confirm a success message that closings were synced to Google.
3. In another tab, open `https://calendar.google.com` as the same Google account and find the transaction deadline / closing event that was just written.

The dates being written are the same contract deadlines visible on the deal **Timeline** in Step B. The user requested the write; the app does not silently copy the whole calendar.

### Step G — Disconnect

1. Return to `https://app.velvetelves.com/settings/connections`.
2. On Gmail, click **Disconnect**.
3. Read the confirmation dialog (inbound sync and send stop), then confirm **Disconnect**.
4. Confirm Gmail shows as not connected.

Users can also revoke Velvet Elves from `https://myaccount.google.com/connections`. Either path stops further Google API access. Stored transaction records can be deleted by emailing `support@velvetelves.com`, as described at `https://velvetelves.com/data-deletion`.

---

## 9. Scope evidence checklist

Use this as a quick pass/fail against the Console configuration.

| Scope | Where the consent appears | What to confirm in the app |
| --- | --- | --- |
| `openid` | Gmail and Calendar consents | Account identity established after connect |
| `.../auth/userinfo.email` | Gmail and Calendar consents | Connected address shown in Settings / Calendar |
| `.../auth/userinfo.profile` | Gmail consent | Connected account name shown |
| `.../auth/gmail.readonly` | Gmail consent | Inbound message matched, original visible, logged on the deal |
| `.../auth/gmail.send` | Gmail consent | **Approve & send** delivers one message to Sent (in-app and Gmail) |
| `.../auth/calendar.events` | Calendar consent | **Add my closings** writes a deadline into Google Calendar |

---

## 10. Navigation cheat sheet

| What | Sidebar path | Direct URL |
| --- | --- | --- |
| Sign in | — | https://app.velvetelves.com |
| Active Transactions | Deals → Active Transactions | https://app.velvetelves.com/transactions |
| Connect / disconnect Gmail | Settings → Email & E-signature | https://app.velvetelves.com/settings/connections |
| Inbox / Outbox / Sent | Intelligence → Email | https://app.velvetelves.com/ai-emails |
| Deal mail and history | Open a deal → Email / Activity | (from the transactions list) |
| Google Calendar | Workflow → Closing Calendar | https://app.velvetelves.com/calendar |

Buttons used in this review, by label: **Sign In**, **Connect**, **Disconnect**, **Test connection**, **Refresh**, **Edit**, **Approve & send**, **Send edited reply**, **Connect calendar**, **Google Calendar**, **Add my closings**.

---

## 11. Data handling (Limited Use)

Google user data is used only to provide the features in Section 8.

- Not sold
- Not used for advertising or retargeting
- Not used to determine creditworthiness
- Not used to train generalized, foundation, or frontier AI models
- Subprocessors that may see feature-scoped content (for draft generation) are named on the privacy policy
- The user can disconnect at any time and can request deletion through `support@velvetelves.com`

Verbatim Limited Use statement (also on `https://velvetelves.com/privacy#google`):

Velvet Elves' use and transfer of information received from Google APIs to any other app will adhere to the Google API Services User Data Policy, including the Limited Use requirements.

---

## 12. If something does not appear immediately

| Symptom | What to do |
| --- | --- |
| OAuth popup does not open | Allow pop-ups for `app.velvetelves.com`, then click **Connect** again |
| Inbound test email not in Inbox | Wait up to two minutes, click **Refresh** on **Intelligence → Email**. Confirm the message was sent to the **connected** Gmail address and that the body contains the deal's property address |
| Message shows **Not linked** | Resend with the exact street address from the deal you opened in Step B |
| Consent screen skipped | Gmail or Calendar was still connected. **Disconnect**, then **Connect** again |
| Unverified-app warning | Expected until Google approves the app. Use **Advanced** → **Go to Velvet Elves (unsafe)** |
| Prompted for payment or a new transaction | Stop. Review does not require creating a file or entering a card. Return to **Active Transactions** and use an existing deal |

Questions during review: `support@velvetelves.com`.
