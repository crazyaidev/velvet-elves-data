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
- The header is slim and reads left to right: breadcrumb + deal name, then on
  the right a **"X% complete"** progress bar, a colored **status** chip (a
  dot + the deal status, click to change), and a small icon-only **agent-pane
  toggle** (wide screens) that hides the conversation so the workbench fills
  the width. When the system is saving anything you clicked, a **"Saving…"**
  pill with a spinner appears in this same row and disappears when it is done.
  There are no Add Task / Upload / Compose / Print / Sync buttons up top — each
  lives inside its tab (Add Task in Tasks, Upload & Print in Documents, Compose
  in Email, Sync in Timeline).

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
2. **Your message appears instantly** as a dark right-aligned bubble the moment
   you send — you never wait for the answer to see what you typed. A small
   **thinking** indicator (three bouncing dots under the ✦ mark) shows while
   the agent works, then the reply lands as clean formatted text.
3. **Reload the page.** The conversation is still there — it is the deal's
   work log, not a throwaway chat.

Pass: your bubble shows immediately, the reply is correct, and it survives a
reload.

---

## 1a. The look of the pane (quick visual check)

No clicks needed — just confirm the pane reads as a modern assistant:

- The pane is one **white card** with a header (✦ gradient mark + "Velvet
  Elves AI" / "Your deal assistant") and a clean background — no muddy tint.
- **Your** messages are dark right-aligned pills; the **agent's** replies are
  bubble-less formatted text next to a small orange ✦ mark. The two are easy
  to tell apart at a glance.
- The composer sits in its own footer with the send button and the one-line
  honesty note under it.

Pass: it looks like a clean, current chat — not a dated bubble list.

---

## 1b. Clear chat history

1. After a few questions, click **Clear chat** in the top-right of the pane
   header (the eraser button — greyed out when there is nothing to clear).
2. A confirm box explains it permanently removes the conversation and any
   proposal cards, but **keeps** already-applied changes (tasks, drafts, dates)
   and the audit trail. Click **Clear history**.
3. The conversation empties to a fresh start. **Reload the page** — it stays
   empty (the wipe is durable, not just on-screen).
4. Open the **Tasks**/**Timeline**/**Email** tabs: anything the agent already
   applied is still there — clearing the chat does not undo real work.

Pass: the conversation is gone for good, but no real change was reversed.

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
6. Open the **Email** tab. It opens on the **Outbox** folder (the Email tab has
   an **Outbox / Inbox** segmented switch at the top, each with a count, so a
   busy deal never mixes the two). The request draft is listed as **Pending
   review** and the banner says *"Nothing sends without your approval."* No
   "Sent" row exists. Click **Inbox** to confirm it is a separate, clean list.
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

1. Click the header icon-only **agent-pane** toggle to collapse it.
2. The workbench fills the width — the same tab bar and tabs, just wider.
3. Re-open the pane: your earlier conversation is still there.

Pass: the full-width workbench is one click away and nothing was lost.

---

## 7. The tab controls (buttons, status, feedback)

1. Open the **Tasks** tab. Each task's status is a **colored pill** (grey =
   Pending, blue = In progress, green = Completed). Click it: the only choices
   are **Pending, In progress, Completed, Skipped** — the real statuses, with
   no leftover values that never applied.
2. Click a status. The pill **changes color immediately** (no waiting), and a
   **"Saving…"** pill appears in the page header while it records, then clears.
3. Look at each tab's top-right: the main action (**Add Task**, **Add
   deadline**, **Add document**, **Manage**) is a filled **orange** button, not
   a plain grey one. Secondary actions are clean outline buttons with icons.
   Per-row extras live behind a **three-dot** menu so the cards stay calm.
4. In **Documents**, click **Upload**: the button shows a spinner while the
   file uploads, so you always know it is working.

Pass: status choices match reality, every click gives instant or "Saving…"
feedback, and the buttons look modern and colored — never plain defaults.

---

## What is NOT in this build (later phases, by design)

- A document **viewer drawer** for citation jumps (Phase 3). Today a
  citation chip shows the page + snippet and opens the Documents tab.
- Email **refile** and the **test-inbound** button (Phase 4). The E1 subset
  here has an **Outbox** folder (this deal's pending drafts + sent outbound
  mail) and a read-only **Inbox** folder, switched by the segmented control,
  and links to the full AI Email Review surface; refiling a misfiled message
  and generating a test inbound are still later phases.
- The **Activity** tab does not yet show agent/compliance/document events
  (Phase 4 history expansion). Until then, the proof surface for every action
  is the owning tab (Compliance, Tasks, Timeline) and the Email tab — each
  applied action's result card names where to look.
- **Document merge**, **always-approve rules**, and **team-lead oversight**
  (Phases 5+).

Every action in this build requires your explicit approval. Email actions
only ever create pending-review drafts — the agent can never send.
