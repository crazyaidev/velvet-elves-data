# Vendor Workspace — Testing Guide (for non-developer testers)

> Companion to `VENDOR_WORKSPACE_SUPERIOR_PLAN.md`. This guide is written for a
> real-estate tester. Every step is done with the mouse and a little typing.
> Where a step says **Pass =**, that is what "working" looks like.
>
> Status: Phases 0–6 implemented. The Vendor Workspace is the vendor portal —
> there is no other version and no flag. Nothing is committed. AI auto-close is
> OFF by default (pending Jake's J3 decision); the portal works fully without it.

---

## 0 · Nothing to turn on — just log in

A vendor (or Jake testing as a vendor) simply logs in and lands on the workspace
directly. There is **no console step, no flag, and nothing to configure** — this
is the vendor portal. The old thin portal has been removed.

---

## 1 · Set up a vendor on a deal, then invite them (internal user)

This is what makes a vendor able to log in and see their work.

1. Open an **active transaction**.
2. Open a task and click **Email a vendor**.
3. If the deal has no vendor yet: pick a **vendor company** and a **contact**
   (or click **Add new** / **Add contact** to create them). Choose the role
   **Loan Officer** for a mortgage vendor, or **Title** for a title vendor.
4. On the compose screen, next to the **To:** line, click **Invite to portal**.
   - **Pass =** the button changes to **Invited to portal**, and the contact
     receives an invitation email.
5. (Optional) Send the vendor request email as normal — that is unchanged.

> The role you chose (Loan Officer vs Title) decides everything the vendor sees:
> a **mortgage** vendor is buyer-side and **never** sees the seller; a **title**
> vendor sees the full contact card.

---

## 2 · Vendor logs in and lands on Loan Files

As the invited vendor (accept the invite, set a password, sign in):

1. You land on **/portal/vendor** — a navy-railed portal with the greeting band
   titled by your role ("Mortgage Loan Officer" or "Title & Escrow").
2. Confirm the **greeting** uses your name, and the three stat tiles
   (Shared files / Open documents / Needs attention) match the one deal you
   were invited to.
3. Confirm the left rail shows just three items: **Loan Files (or Title Files) ·
   Documents · Tasks** (the home screen IS Loan Files — there is no separate
   Overview).
4. Each deal shows as a card with its address, milestone, three date tiles
   (Appraisal / Financing / Closing), a "Next step" callout, and a progress strip.
   - **Pass =** you see only the deal you were invited to, and no other
     brokerage deals exist anywhere in the portal.

---

## 3 · The scope wall: contacts (the most important check)

1. **Click the file card to expand it** in place, then look at the **Contacts**
   panel inside.

**If you are a MORTGAGE vendor:**
- **Pass =** you see the Buyer and the agents, and **the Seller is NOT shown
  anywhere**.

**If you are a TITLE vendor** (repeat §1–§2 inviting a second contact with role
**Title**):
- **Pass =** you see the full card **including the Seller**, read-only.

In both cases, you should never see other outside vendors (inspector, appraiser).

---

## 4 · The expanded card: dates, tasks, contacts, documents, updates

Expand a file card (or open it from a Needs-Attention link). Inside you see five
panels:

1. The **Progress** strip (milestone stages derived from your tasks; fewer
   stages, or none, when the deal has no milestone data — that is correct).
2. **Your tasks**, **Key dates**, and **Contacts** across the top.
3. The **Documents** area (upload / request) and the **Updates** panel (message
   your coordinator) below.
   - **Pass =** nothing here belongs to a different vendor or the other side of
     the deal.

---

## 5 · Documents: request one, get it shared (full loop)

**As the vendor:**
1. Go to **Documents** in the left rail.
2. Click **Request a document**. Tap a suggestion chip (e.g. "Pre-approval
   letter") or type what you need, then **Send request**.
   - **Pass =** the request appears under **Awaiting**.

**As the internal user** (other browser/session):
3. Open the same transaction → a task → **Email a vendor** to open the vendor
   screen. Near the top you will see **Document requests from this vendor**.
4. Find the request, pick an existing document from the dropdown, click **Share**.
   - **Pass =** the row shows **Shared "…"**.

**Back as the vendor:**
5. Reload **Documents**.
   - **Pass =** the document now appears under **Shared with you**, and the
     **Awaiting** item is gone.

---

## 6 · Tasks: ask to close one out, get it reviewed (full loop)

**As the vendor:**
1. Go to **Tasks**. On an open task, click **Mark done**.
2. Choose **Leave a note**: tap a reason chip (e.g. "Appraisal received") or
   type a short note. (Or choose **Upload a document** and attach a file.)
3. Click **Request to close**.
   - **Pass =** the task shows **In review**, with an **Undo** link next to it.
4. (Optional) Click **Undo** to retract it while it is still in review, then
   redo step 1.

**As the internal user:**
5. Open **Vendor proposals** from the left sidebar (under Intelligence).
6. At the top, the **Task close-out requests** section lists the vendor's
   request, with the note (or the uploaded document's name).
7. Click **Approve** to close the task — or **Reject**, type what is still
   needed, and **Send back**.
   - **Pass (approve) =** the request disappears from the queue.
   - **Pass (reject) =** same, with your reason recorded.

**Back as the vendor:**
8. Reload **Tasks**.
   - **Pass (after approve) =** the task now shows **Done**.
   - **Pass (after reject) =** the task shows the team's reason and a **Try
     again** link.

---

## 7 · AI verification (optional — only if a tenant turns it on)

By default AI does **not** close tasks; a human always decides (§6). A tenant
admin can opt in so confident requests close automatically. This is OFF until
Jake decides (J3), so most testers will skip this section.

If it is enabled for the tenant:
1. As the vendor, submit a clear close-out (note or matching document).
2. **Pass =** the task closes immediately and shows **Closed by AI · NN%**.
3. Submit a vague note on another task.
4. **Pass =** it does **not** auto-close; it goes to the internal review queue,
   where the reviewer sees an **AI** recommendation chip and decides.

If the AI provider is unavailable, the request simply waits for a human — it is
never closed on a guess.

---

## 8 · Things that should always be true

- A vendor can never reach an internal page by typing its URL (they are bounced).
- A vendor never sees a deal, task, document, or contact outside their scope.
- A mortgage vendor never sees the seller; a title vendor does.
- Every list has an honest empty state (no fake rows) when there is nothing yet.
- The footer boundary note appears on every vendor page.

---

## 9 · If something looks wrong

Note the page, what you did, and what you expected vs. saw. Common gotchas:
- **"Your role on this file is being set up"** → the vendor was invited but the
  vendor-company assignment/contact does not match their email yet; re-check §1.
- **No document/task shows for the vendor** → confirm it was shared (§5) or that
  a task actually exists on the deal for that role.

---

**End of guide.**
