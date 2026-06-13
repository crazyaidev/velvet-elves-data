# AI Agent Workspace — Frontend Testing Guide

For real-estate testers (no developer tools needed). Every step starts on a
visible page and ends with on-screen proof. Mouse-only; typing is only for
naming things or a short instruction.

This guide covers what shipped: Phases 0–2 of
`AI_AGENT_WORKSPACE_SUPERIORITY_PLAN.md` plus the mismatch-resolution slice
(the document-type-mismatch hero scenario, the agent conversation, the typed
action lifecycle, and the Email tab E1 subset).

---

## 0. Opening it

The agent-centric workspace **is** the transaction detail page now. Just open
any active transaction at `/transactions/<a deal>` — there is nothing to turn
on and no script to run.

- On a wide screen you see the **AI agent pane on the left** and the
  **workbench on the right**. The workbench is **one unified panel** with
  underline tabs across its top (Timeline, Compliance, Documents, Tasks,
  People, Activity, Email) and the active tab on the same surface below — no
  floating tab bar over a separate card. There is no KPI strip, tracking-date
  band, or deal-brief card.
- On a narrow screen there is no split — the deal opens straight into the
  **Agent** conversation (the first tab); the other tabs are one tap away.
- The header is slim: breadcrumb, a **"X% of tasks complete"** progress bar
  (centered, ListedKit-style), the deal name + status, and an **"Agent pane"**
  toggle (wide screens) that hides the conversation so the workbench fills
  the width. There are no Add Task / Upload / Compose / Print / Sync buttons
  up top — each lives inside its tab (Add Task in Tasks, Upload & Print in
  Documents, Compose in Email, Sync in Timeline).

The left pane opens on **AI suggestions**: one compact block listing what
needs you (the top few items, with a "Show all" link if there are more) and
a **Scan** button. Below it is the conversation, which **auto-scrolls** to
the newest message. The agent's replies are **formatted Markdown** (bold,
lists, headings render properly, not raw text). The composer sits at the
bottom: the **paperclip** attaches a file (uploaded, then analyzed in the
chat), the circular orange button sends, and typing **/** **@** **#** opens
commands, people, and references.

**Upload = analysis.** Whenever you add a document — by the composer
paperclip, or by uploading in the **Documents** or **Compliance** tab — the
agent uploads it, reads it, and posts an analysis in the conversation
(summary + any issues), the way ListedKit does. A document-type mismatch
surfaces here as a blocker you can resolve in one click.

(Escape hatch for reviewers only: setting local-storage key
`ve_agent_workspace_v1` to `off` reverts to the classic page while the
feature is still uncommitted. Normal testing never needs this.)

---

## 1. Ask a question (durable conversation)

1. In the composer (bottom of the agent pane), type **"When is the closing
   date?"** and press Enter.
2. Your message appears, then the agent answers with the exact closing-date
   format.
3. **Reload the page.** The conversation is still there — it is the deal's
   work log, not a throwaway chat.

Pass: the answer is correct and survives a reload.

---

## 2. The hero scenario — resolve a document mismatch

Setup (once): in Compliance, attach a file to the "Earnest Money Deposit
Receipt" requirement that is really a different document (e.g. a copy of the
purchase agreement). The row moves into **Uploaded** but wears a mismatch
chip — it *looks* satisfied, which is the danger.

1. In the agent pane's **AI suggestions** block, the summary line notes the
   blocker. An **issue card** titled "Document type mismatch …" states:
   *"This requirement currently reads as satisfied, but the attached file
   looks like a …"*.
2. Click the issue card's button **"Detach and draft a request for the
   correct document."**
3. A **proposed action card** appears in the conversation with a preview:
   *Step 1 detach … Step 2 create ONE pending-review request draft … Nothing
   sends until you approve it.* Click **Approve**.
4. The card flips to **Applied** with the result and an **Undo** chip.
5. Open the **Compliance** tab: the receipt requirement is back in **Missing**
   (the wrong file was detached — never silently accepted).
6. Open the **Email** tab: the request draft is listed as **Pending review**.
   The banner says *"Nothing sends without your approval."* No "Sent" row
   exists.
7. Back in the agent pane, click **Undo** on the applied card: the wrong file
   re-attaches (the draft remains, discardable from AI Email Review).

Pass: the requirement returned to Missing, a pending draft was created,
nothing was sent, and Undo worked — all visible on screen.

---

## 3. Reference any row without typing its name

1. On any workbench tab, hover a row (a task, a requirement, a document, a
   deadline, or a person). A small **✦ "Ask AI about this"** button appears.
2. Click it. The row becomes a **reference chip** in the composer and the
   pane focuses.
3. Type a question ("What is this?") and send. The agent answers with the
   referenced item in context.
4. Alternative: drag a row straight onto the composer — same chip, nothing is
   uploaded or changed.
5. The **+** button in the composer opens a searchable picker with tabs
   (Documents, Tasks, Deadlines, Requirements, People, Emails). Pick one to
   insert it.

Pass: every item is referenceable by mouse; the chip's name matches the row.

---

## 4. Commands

1. Click the **/** button (or type `/`). A menu opens: **/scan**,
   **/readiness**, **/summarize**, **/draft-email**, **/request-document**,
   **/add-deadline**, **/move-date**.
2. Click **/scan**: the agent runs a compliance scan and the issue list
   refreshes with a "Scan complete …" note.
3. Click **/readiness**: the agent reports whether the deal is ready to close,
   with the blockers to resolve.

Pass: commands are mouse-selectable and produce a visible result.

---

## 5. Move a date safely (cascade preview, then undo)

1. In the composer type **"Move the closing date to <a date a week later>"**
   and send.
2. The agent proposes an **apply-date-cascade** action whose preview lists
   exactly which deadlines and tasks move (and which do not, with reasons).
3. Click **Approve**. Open the **Timeline** tab: the dates moved.
4. Back in the pane, click **Undo**: the dates revert.

Pass: a date never changes without showing the cascade first; undo restores it.

---

## 6. Hide the conversation (focus the workbench)

1. Click the header **"Agent pane"** toggle to collapse it.
2. The workbench fills the width — the same tab bar and tabs, just wider.
3. Re-open the pane: your earlier conversation is still there.

Pass: the full-width workbench is one click away and nothing was lost.

---

## What is NOT in this build (later phases, by design)

- A document **viewer drawer** for citation jumps (Phase 3). Today a
  citation chip shows the page + snippet and opens the Documents tab.
- The full Email tab **Inbox with refile** and the **test-inbound** button
  (Phase 4); the E1 subset here shows this deal's pending drafts and sent
  outbound mail, and links to the full AI Email Review surface.
- The **Activity** tab does not yet show agent/compliance/document events
  (Phase 4 history expansion). Until then, the proof surface for every action
  is the owning tab (Compliance, Tasks, Timeline) and the Email tab — each
  applied action's result card names where to look.
- **Document merge**, **always-approve rules**, and **team-lead oversight**
  (Phases 5+).

Every action in this build requires your explicit approval. Email actions
only ever create pending-review drafts — the agent can never send.
