# Google OAuth Demo Video: Requirements and Script

**Prepared by:** Jan
**Date:** August 6, 2026
**Supersedes:** `DEMO_VIDEO_GUIDELINE.txt` and `DEMO_VIDEO_GUIDE_FOR_JAKE.md`
**Record on:** https://app.velvetelves.com

---

## Why the first video failed, and what actually has to change

The first video followed `DEMO_VIDEO_GUIDE_FOR_JAKE.md` and covered the OAuth mechanics correctly: both consent screens including the separate Calendar one, the unverified-app warning, an inbound email matched to a deal, Approve and send, the Sent folder, and disconnect. All six configured scopes were demonstrated.

Google still rejected it:

> Your demo video does not sufficiently demonstrate **the functionality of your app**.

Note the wording. Not the functionality of the *integration*, which was covered, but of the **app**. Pair that with the second item they raised in the same category, a demand for login credentials so they can use the product themselves, and the underlying doubt is clear:

**They are not yet convinced Velvet Elves is a substantial, working product.**

That is the standard concern behind a restricted Gmail scope. Reviewers see many thin applications built mainly to obtain mailbox access, so they need to see a real product in which reading transaction email is an obviously necessary part of something larger.

The flaw in the previous guide was that every scene was about the Google integration. Sign in was explicitly "keep it short", and the product itself barely appeared. A reviewer watching it sees an application whose apparent purpose is connecting Gmail.

**The fix is a change of emphasis, not more OAuth detail.** Roughly the first third of the video must establish the product on its own terms. The scopes are then shown inside that context, where the need for them is self-evident.

---

## 1. Prerequisites

Do not record until all of these are true.

1. **The scope string fix is deployed.** The backend currently requests the shorthand `email` and `profile` while the Console declares `.../auth/userinfo.email` and `.../auth/userinfo.profile`. Google asked for a strict string match. Record only after the corrected scopes are live.
2. **A reviewer test account exists** on `app.velvetelves.com` with no phone verification, no card and no MFA. This is the same account handed to Trust and Safety, so what they see when they log in should match the video.
3. **The account looks like a working brokerage, not a demo shell.** Several transactions in different states, each with a property address, named parties, generated tasks with real due dates, documents, and deadlines on the calendar. One empty test deal is the single most likely cause of a second rejection.
4. **A throwaway Google account** to connect. Its inbox and Sent folder will be on camera.
5. **A second mailbox** to send the inbound test message from.

---

## 2. Hard requirements

**The product must be demonstrated before any Google permission is requested.** This is the change from the last attempt.

**Every configured scope must be demonstrated**, and they span two separate consent screens, so both must appear:

- Gmail connect grants `openid`, `userinfo.email`, `userinfo.profile`, `gmail.send`, `gmail.readonly`
- Calendar connect grants `openid`, `userinfo.email`, `calendar.events`

**Both consent screens must be legible.** Hold on each long enough to read every permission, scrolling slowly if the list does not fit.

**The "Google hasn't verified this app" screen must be shown.** Google's own guidance says this is expected.

**The address bar must be visible throughout.**

**Each scope must be followed through to its user-facing result.** Granting a permission is not demonstrating it.

**No real client data anywhere**, including background tabs and notification toasts.

---

## 3. Format

- YouTube, **Unlisted**. Private means the reviewer cannot open it.
- **12 to 15 minutes.** Longer than before, because the product now has to be shown as well as the integration. Do not pad it, but do not rush the product section to save time.
- 1080p minimum so scope descriptions are readable.
- English narration, or on-screen captions before each scene.
- No background music.
- Cuts are fine for waiting, never across a consent screen.

---

## Part 1: The product (about 5 minutes)

This part exists to answer one question before Google is mentioned at all: is this a real application that real estate professionals would use?

### Scene 1: Identity (30 seconds)

`velvetelves.com`, then `velvetelves.com/privacy`, pausing on the Google user data section.

Say: Velvet Elves is transaction coordination software for real estate agents and brokerages.

### Scene 2: Sign in and the pipeline (60 seconds)

Sign in at `app.velvetelves.com`. Land on the dashboard.

Show the **Active Transactions** list with several real-looking deals. Point out the filter tabs, the counts, deals at different stages.

Say: this is an agent's book of business. Each row is a live transaction from contract to close.

### Scene 3: Inside a transaction (2 minutes)

This is the most important scene in Part 1. Open one deal's workspace and walk the tabs:

- **Timeline**: the deadlines derived from the contract, and how each was calculated
- **Tasks**: the generated task plan, grouped by urgency, with owners and due dates
- **Documents** and **Compliance**: the checklist of what the file requires, what is in and what is missing
- **People**: the buyer, seller, agents, lender and title company on the deal

Say: when a signed contract is uploaded, the system reads it and builds the deadlines, the task plan and the document checklist automatically. This is the work the product does.

### Scene 4: The AI assistant and the approval model (90 seconds)

Open the AI assistant on the deal. Ask it something in plain English about the transaction. Show it proposing an action.

**Approve the proposal and show the result land on the deal.**

Say clearly: the assistant proposes, and a person approves every change. Nothing happens on its own. This is the principle that governs the email features shown next.

---

## Part 2: The Google integration (about 6 minutes)

Now that the product is established, the scopes are shown as part of it.

### Scene 5: Connect Gmail (2 minutes), the critical scene

Settings → Email & E-signature → **Connect** on Gmail.

Show the account chooser, then the unverified-app screen, then Advanced and continue.

**Stop on the consent screen.** Read each permission aloud as it appears. Do not rush.

Return to the app, show **Connected** with the address, then **Test connection** and its result.

Say: for each permission, the feature in the product it enables.

### Scene 6: `gmail.readonly` end to end (2 minutes)

Send an email from the second mailbox to the connected account, referencing the property address of one of the seeded deals.

Then show, in order:

1. **Intelligence → Email → Inbox**, with the message present
2. That it was **matched to the correct transaction** with no manual filing
3. The **deal's own Email tab** carrying the same message
4. The transaction's **communication history**, showing the message logged as a permanent record
5. The AI's reading of it: the category label and what it extracted

Say: inbound mail is read so it can be matched to the right deal, logged as that transaction's correspondence record, and used as context for a reply. Neither the matching nor the drafting is possible without the message body.

### Scene 7: The draft, and human approval (60 seconds)

Open the prepared draft. Show recipient, subject, body, and the panel showing what it was based on.

Say plainly: **the AI drafts and sends nothing. No email leaves the system without a person reading and approving it.**

Click **Edit**, change wording, show the edit persisting.

### Scene 8: `gmail.send` end to end (60 seconds)

Click **Approve & send**. Show the confirmation.

Then show the message in the connected account's **Sent folder**, sent from the user's own address, and the same message logged back on the deal's Email tab.

Say: sending happens only on that click, one transaction-specific message at a time, from the user's own mailbox, and the record is written back to the deal.

### Scene 9: `calendar.events` end to end (2 minutes)

**Do not skip or rush this.** It is a separate consent and a separate scope.

Workflow → **Closing Calendar** → **Connect calendar** → **Google Calendar**.

**Show the second consent screen in full**, exactly as in Scene 5.

Click **Add my closings**, switch to Google Calendar in another tab, and show the transaction deadline written there. If practical, change a date in the app and show the calendar entry update.

Say: the deadlines built in Scene 3 are written to the user's own calendar at their request, and kept in step when a date changes.

---

## Part 3: Control and data handling (about 90 seconds)

### Scene 10: Disconnect

Settings → Email & E-signature → **Disconnect** on Gmail. Show the confirmation dialog explaining the consequence, then confirm. Show the disconnected state.

Say: access can be revoked at any time from inside the product, and from the user's Google Account.

### Scene 11: Data handling statement

Say: Google user data is used only to provide the features just shown. It is not sold, not transferred, not used for advertising, and not used to train generalized AI models. Users can disconnect at any time and request deletion.

---

## 4. Scope evidence checklist

Check every row before uploading.

| Scope | Consent screen | Feature evidence |
| --- | --- | --- |
| `openid` | Both | Scene 5, account identity established |
| `.../auth/userinfo.email` | Both | Scene 5, connected address shown in Settings |
| `.../auth/userinfo.profile` | Gmail | Scene 5, connected account name shown |
| `.../auth/gmail.readonly` | Gmail | Scene 6, message matched, logged, read by the AI |
| `.../auth/gmail.send` | Gmail | Scene 8, approved reply in the Sent folder and on the deal |
| `.../auth/calendar.events` | Calendar | Scene 9, deadline written into Google Calendar |

And the separate test, which is what failed last time:

**Could a reviewer who watched only Part 1 describe what this product does for a real estate agent, without mentioning Google?** If not, Part 1 is too thin and the video will fail again for the same reason.

---

## 5. What causes rejection

- **Showing the integration without showing the product.** This is what sank the first attempt.
- **A demo account with no real-looking data.** An empty workspace demonstrates nothing.
- **Any configured scope not demonstrated**, most likely the Calendar connect.
- **Only one consent screen shown.** There are two.
- **Granting a permission without showing what it does.**
- **Saying or implying the AI sends email on its own.** Always "it drafts, a person approves".
- **Editing out the unverified-app warning.**
- **Consent screen text too small to read.**
- **Real client data visible anywhere.**
- **A Private video** the reviewer cannot open.

---

## 6. After recording

1. Upload as **Unlisted**.
2. Open the link in a private window while signed out of YouTube. If it does not play, the reviewer cannot watch it.
3. Reply to the existing **Trust and Safety email thread** with the link, the reviewer test credentials, and step-by-step navigation instructions.

Do not start a new request in the Console. The review is live and the email thread is the channel.
