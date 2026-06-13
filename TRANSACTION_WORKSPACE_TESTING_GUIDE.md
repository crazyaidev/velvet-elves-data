# Transaction Workspace — Testing Guide

> Walk through this checklist after each deploy to verify the Transaction
> Workspace (TRANSACTION_PAGE_REDESIGN_SUPERIORITY_PLAN, Phases A–C). Every
> item lists **how to test** and the **expected result**, mouse-only — you
> never type anything except names. If a test fails, file a bug referencing
> the section heading (e.g. "TWG-3.2 Cascade apply").

**Test scope.** The per-deal workspace at `/transactions/<deal id>` for
Agent / Transaction Coordinator / Team Lead / Admin: header, KPI strip,
Tracking Dates, Deal Brief, the six tabs (Timeline · Compliance · Documents
· Tasks · People · Activity), the AI rail, the command bar, and the cascade.
Plus a regression pass on the portfolio page (unchanged behaviors).

**Prerequisites.**
- Backend migrations applied in order (plan §8.4): the three pending Part
  I/II migrations, then `20260819090000_requirement_evidence.sql` and
  `20260819100000_transaction_briefs.sql`. Phases A–B work without the last
  two; §6 (evidence) needs them.
- One deal created through the AI wizard from a contract PDF (so it has AI
  rows with citations), and one older deal created before the checklist
  feature (for the honest empty states).
- Test against the fresh backend on :8001 (the :8000 dev backend serves
  stale code).

**Conventions.** ✅ = expected present. ❌ = expected absent.

---

## 1 · Getting there

### 1.1 Open workspace from the portfolio card
**How to test.** On `/transactions`, find any deal card.

**Expected result.**
- ✅ The client-name title is a link; hovering underlines it; clicking it
  opens `/transactions/<id>` (the workspace), not the drawer.
- ✅ A small expand icon next to the chevron also opens the workspace.
- ✅ Expanding the drawer shows an "Open workspace" button first in the
  footer row.
- ✅ Everything else on the card is exactly as before (milestone bar, stage
  pill, AI banner, drawer columns) — Phase A adds nothing else to Jake's
  surface.

### 1.2 Deep links and the URL
**How to test.** In the workspace, click each tab, then copy the URL into a
new browser tab.

**Expected result.**
- ✅ Each tab writes `?tab=timeline|compliance|documents|tasks|people|activity`
  and the pasted URL lands on the same tab.
- ✅ A link with `?tab=tasks&task=<task id>` opens Tasks with that row
  outlined in orange; `?tab=compliance&requirement=<id>` does the same on
  Compliance.
- ✅ The breadcrumb reads `Deals › Transactions › <street address>` (the
  sidebar group the page lives in) and the "Transactions" crumb returns to
  the portfolio.
- ✅ The header bar stays put while the content below it scrolls; nothing on
  the page is cut off without a scrollbar.

### 1.3 Role gates
**How to test.** Open the same URL as each role.

**Expected result.**
- ✅ Agent, TC, Team Lead, Admin: the workspace (TC sees the same controls
  as Agent).
- ✅ Attorney: the Matter Workspace (unchanged).
- ✅ Client / FSBO / Vendor: cannot reach it (redirected / not found).

---

## 2 · The five questions (completion bar §2.2)

Open the wizard-created deal. With mouse clicks only, answer:

### 2.1 "What is the plan?"
**Expected result.** The Timeline tab lists, in date order: core dates
(acceptance, closing), term-derived deadlines (inspection etc.), and every
wizard deadline — each with its date and a plain-English basis line ("14
days after Date of Acceptance"). The mini-map shows one dot per dated row
(navy core, champagne derived, orange AI).

### 2.2 "Why does each deadline exist?"
**Expected result.** Every row shows its basis; AI rows carry the chip —
click it to see the contract snippet, page number, and confidence.

### 2.3 "What changed since I approved it?"
**Expected result.** The Activity tab lists date edits, status changes, and
cascade applies ("Closing Date moved … N deadline(s) recomputed").

### 2.4 "What does the AI think I should do next?"
**Expected result.** The champagne "AI next step" strip in the header shows
the next-step line; "Ask the AI about this deal" (in the More menu) opens
the deal-scoped chat. The chat advises only — it never edits the deal.

### 2.5 "What happens if the closing moves?"
**Expected result.** Section 3 below — the full diff before anything is
written.

---

## 3 · Move the closing and watch everything move (cascade)

### 3.1 Preview
**How to test.** Timeline tab → pencil icon on the Closing Date row → pick
a date a week later → "Preview changes".

**Expected result.**
- ✅ A panel titled "Change Closing Date" computes on the server and lists
  every row that will move: old date struck through → new date, with a
  "rolled off weekend" chip where the new date rolled forward.
- ✅ Rows that will NOT move are listed with the reason: "pinned" (a human
  set the date by hand), "already completed", "no rule attached", or "its
  anchor has no date". Nothing is silently skipped.
- ✅ Nothing has changed yet — close the panel and all dates are untouched.

### 3.2 Apply, re-sync, undo
**How to test.** Run the preview again and click Apply.

**Expected result.**
- ✅ One click applies everything: the closing date, rule-bound task dates,
  and requirement due dates all agree afterwards (check Tasks and
  Compliance).
- ✅ A hand-pinned task date did not move and was listed as pinned.
- ✅ If you have Google/Outlook calendar connected, a "Sync deadlines" chip
  appears right in the confirmation (externally pushed events are stale
  until you click it).
- ✅ "Undo" restores everything (it is a fresh apply of the inverse change —
  check Activity: two cascade entries, apply and undo).
- ✅ The same edit from the Tracking Dates strip (clicking the Closing Date
  chip) routes through the same preview — never a silent write.

### 3.3 Term rule edit cascades too
**How to test.** Timeline tab → pencil on "Home Inspection Deadline" →
change the day count with the stepper → "Preview changes".

**Expected result.**
- ✅ The same preview/apply flow; anything anchored on the inspection
  deadline (chained anchors) moves with it.

---

## 4 · Compliance tab

### 4.1 Waive a requirement and undo it
**How to test.** Click "Waive" on an open row.

**Expected result.**
- ✅ The row moves to the collapsible "Waived" group and an Undo chip
  appears; Undo (or "Un-waive" inside the group) restores it. Never a
  vanished row.

### 4.2 Full editing parity with the wizard
**How to test.** Pencil on an open row.

**Expected result.**
- ✅ The wizard's editor inline under the row: name, description, and
  EITHER a relative rule (days before/after an anchor, picked from the
  branded dropdowns) OR a specific date.
- ✅ Saving a rule shows a server-resolved due date (weekends roll forward);
  the strip due chip updates.

### 4.3 Upload a compliance document in one motion (Add document)
**How to test.** Click "Add document" in the card header; drag a PDF into
the modal.

**Expected result.**
- ✅ A MODAL opens (Escape closes it). The dropzone states the accepted
  formats (PDF, DOC/DOCX, JPEG, PNG, WEBP, GIF, TXT · up to 20 MB).
- ✅ Dropping the file auto-fills the Document name from the file name
  (Title Case, editable); pick a Document type from the branded dropdown;
  Due is None / Relative rule / Specific date.
- ✅ "Upload & add to checklist" creates the row directly in the UPLOADED
  group with "Matched: <file>", and the file appears on the Documents tab.
  Zero typing required (one name edit at most).
- ✅ Without a file, the button reads "Add to checklist" and the row lands
  in Open — that's the "track an obligation you don't hold yet" path.
- ✅ After the upload, the "✦ AI is checking this document…" chip appears
  on the row and settles into "✓ AI confirmed · <type>".

### 4.4 The AI catches a wrong document (verification)
**How to test.** On an open row (e.g. "Septic Inspection Report"), click
"Attach document" → "Upload a new file" → deliberately drop a purchase
agreement PDF → Attach.

**Expected result.**
- ✅ The row turns green immediately — the attach is never blocked.
- ✅ Within the parse time, the amber warning appears: "AI read this as
  Purchase Agreement - expected Inspection Report", with three one-click
  corrections: "Use AI type" (adopts the detected type on the row and the
  file), "Keep my type" (dismisses; it does not re-nag after reload), and
  "Detach & re-attach" (the row returns to Open and the Attach modal
  reopens).
- ✅ A file the AI cannot read (e.g. a photo of a blank page) settles into
  the muted "AI couldn't read this file" — honest, no action required.

### 4.5 Attach an existing file / request by email
**Expected result.**
- ✅ "Attach document" opens the modal on "Pick an uploaded file": ALL of
  this deal's unmatched documents as a radio list (filter box when there
  are many); Attach moves the row to Uploaded with the document named;
  "Detach" reverts it. With zero documents on the deal, the modal opens
  straight on the Upload pane — no dead-end.
- ✅ "Request by email" lists parties with an email; picking one files a
  DRAFT into AI Email Review — the toast says nothing sends without your
  approval.

### 4.6 Honest empty state (legacy deal)
**How to test.** Open the pre-checklist deal's Compliance tab.

**Expected result.**
- ✅ "No compliance checklist exists for this deal" with two buttons:
  "Generate the standard checklist" (adds the library items for this deal
  type, once — clicking again does not duplicate) and "Add a document"
  (the same upload modal, for a first custom item).

---

## 5 · Tasks, ask-the-bar, and auto-email

### 5.1 Ask the bar to add a deadline
**How to test.** Timeline tab → type into "Tell me what to change":
"add a septic inspection deadline 14 days after acceptance" → Enter.

**Expected result.**
- ✅ A preview chip describes exactly what will happen; nothing applies
  until you click Apply; afterwards an Undo chip removes it.
- ✅ A nonsense command ("fax the moon") gets an honest refusal listing what
  the bar CAN do — nothing mutates.
- ✅ "move the closing to <date>" opens the cascade preview from §3, never a
  direct write.

### 5.2 Add deadline by hand
**How to test.** Timeline tab → "Add deadline" → name it, pick a rule.

**Expected result.**
- ✅ The date is computed server-side (weekend rolls included) and the row
  appears with its basis; removing it shows the Undo chip (the task is
  skipped, not deleted — no admin rights needed).

### 5.3 Task rows expose their metadata (Tasks tab)
**Expected result.**
- ✅ Wizard tasks show their basis chip ("3 days before Closing Date") and,
  where linked, a "Related compliance item" link that jumps to the
  Compliance row.
- ✅ AI tasks show the chip with confidence/citation.
- ✅ The Auto-Email toggle appears ONLY on tasks whose target has a captured
  party email; toggling it on/off persists (re-open the tab to confirm) and
  the copy says drafts are reviewed before sending.
- ✅ The pencil opens the same rule-or-date editor as the wizard; the status
  menu and vendor-email button work as on the card.

---

## 6 · Verify an AI deadline against the contract (evidence)

**How to test.** On the wizard-created deal (created AFTER the evidence
migrations), click the AI chip on a timeline row, a compliance row, and a
task row.

**Expected result.**
- ✅ Each expands to the contract snippet, the page number, and the
  confidence percentage — the same evidence the wizard showed at intake.
- ✅ The Deal Brief band shows the watch-outs with "p.N" citation buttons.
- ✅ On a deal created BEFORE the migrations: no fake chips — AI rows
  show no evidence, and the brief shows the factual summary only. The
  summary always matches the live deal (change the price; the sentence
  follows).

---

## 7 · Header bar and the deal overview card

**Expected result.**
- ✅ The white header bar: breadcrumb, client names in serif with the stage
  pill and address inline, the champagne AI next-step strip, then one row
  with the section pills (Timeline … Activity, active pill orange) on the
  left and the quick actions on the right.
- ✅ Quick actions: Add Task, Upload Document, Sync deadlines, and a "More"
  menu holding Compose Email, Print closing checklist, and Ask the AI.
  ❌ No "Share" action.
- ✅ ONE overview card under the header with three hairline-separated rows:
  1. The stat row: Purchase price, Days to close (with the closing date
     under it), Open tasks (overdue count in red), Missing documents
     (overdue in red). Sparklines appear ONLY on the two stats with real
     history (completions / uploads) and only when there is at least one
     event — never decorative.
  2. The "Tracking dates" chip rail (T4); unset chips read "Not yet"; the
     five pure tracking fields open the small date popover and save
     directly; Closing/Possession route through the cascade (§3.2).
  3. The deal brief sentence with its watch-outs (§6).
- ✅ Changing Status (pill at the top right) asks for confirmation; choosing
  Closed opens the post-closing feedback prompt.
- ✅ Each tab below is a single card with a mono kicker and serif title — no
  floating bands, no empty side column.

---

## 8 · Documents, People, Activity

### 8.1 Drag a document anywhere
**How to test.** Drag a PDF from your desktop over any part of the
workspace (the Timeline tab, the header — anywhere).

**Expected result.**
- ✅ A "Drop to upload to this deal" overlay appears; releasing switches to
  the Documents tab and uploads the file; the toast says the AI is
  checking the document, and the new row carries the verification chip
  (checking → a verdict). The toast promise is real — every upload path
  runs the AI check.

### 8.2 Documents tab
**Expected result.**
- ✅ "Upload" (and the header's "Upload Document" quick action) opens the
  classified-upload dialog: file + name (auto-filled) + type; saving
  uploads and starts the AI check.
- ✅ The list shows every document with type, date, size, version, and a
  working download; rows carry the AI verification chip ("AI read this as
  …" offers "Use this type" when the file had no type; a mismatch against
  the picked type shows the amber warning with Use AI type / Keep my
  type).
- ✅ "Open documents manager" opens the full existing flow
  (rename/classify, versions, email, delete, parse-confirm, missing-docs —
  whose "Attach document" now opens the same shared modal).

### 8.3 People tab
**Expected result.**
- ✅ Parties grouped Buyer / Seller / Agents / Lender / Title (unknown roles
  under "Other contacts" — nothing disappears); each group's Add button
  opens the contact modal pre-filled for that group.
- ✅ Client Q&A, Assign team, and Manage client access open the existing
  modals (the latter two only for Agent/TeamLead/Admin).

### 8.4 Activity tab
**Expected result.**
- ✅ The audit feed with a filter box; cascade applies appear with their
  summary; the Communications button opens the existing panel.

---

## 9 · Portfolio page regression (must be unchanged)

- ✅ Card face, milestone bar, stage pills, AI banner, why-badges: pixel-
  identical to before.
- ✅ Drawer columns (Tasks / Key Dates / Contacts), all 16 modals, exports,
  print, sidebar filters, tabs, sort, search, `?expand=` and `?highlight=`
  links: all behave exactly as documented in
  TRANSACTIONS_PAGE_COMPLETION_PLAN.
- ✅ The Closing Calendar's deep links still open the card drawer (they
  retarget to the workspace only in Phase D / T6).

---

## 10 · Comfort and accessibility spot-checks (v2 scale)

- ✅ All readable content (row text, basis lines, chips, dates) is 12px or
  larger; the only smaller type is the benchmark's decorative mono kickers
  and stat labels (the same 10px voice the Calendar and dashboard pages
  ship).
- ✅ All click targets comfortably large (44–48px); rows ≥ 52px.
- ✅ Every async region shows a shimmer skeleton, then content or an error
  with a Retry button — never a blank.
- ✅ The page paints its header and timeline from one request (watch the
  network tab: one `/plan` call up front; tabs fetch lazily).

---

*Companion to WIZARD_TESTING_GUIDE.md. Covers Phases A–C of
TRANSACTION_PAGE_REDESIGN_SUPERIORITY_PLAN; Phase D (card/drawer slimming,
calendar retarget) and Phase E (global comfort scale) are Jake-gated and not
yet built.*
