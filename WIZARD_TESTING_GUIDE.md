# New Transaction Wizard — Testing Guide

> Walk through this checklist after each deploy to verify that every
> piece of client feedback from the testing rounds has been resolved.
> Every item lists **how to test** and the **expected result**. If a
> test fails, file a bug referencing the section heading (e.g. "WTG-3.4
> Email autocomplete").

**Test scope.** New Transaction wizard end-to-end (modal-hosted),
including drag-drop intake, AI parsing, address & parties, purchase
info, missing-info recovery, confirmation, dialogs, and the left-rail
stepper.

**Prerequisites.**
- Deployed to `dev.velvetelves.com` (or local equivalent).
- Logged in as an Agent user with the modal opened from the dashboard
  "New Transaction" button. Repeat the role-gated checks (§ 4.2) once
  as TC/TeamLead/Admin and once as Agent.
- A multi-page test PDF (10+ pages) and a single-page test PDF are
  needed for §§ 1.2 and 1.3.

**Conventions.**
- ✅ = expected to be present.
- ❌ = expected to be absent.
- "AI banner" refers to the "Fields that still need your attention are
  highlighted below…" hint shown above forms when AI has parsed.

---

## 1 · Step 1 — Documents

### 1.1 Mandatory representation radio
**How to test.** Open the wizard. Look at the top of Step 1 above the
file dropzone.

**Expected result.**
- ✅ A radio group titled "Who Are You Representing?" with options
  Buyer / Seller / Buyer & Seller, marked required (`*`).
- ✅ Subtitle: "Tell us who your client is so AI only pulls their
  contact info — not the other side's."
- ✅ Without a selection, the dropzone is dimmed and unclickable; the
  Continue button is disabled; clicking the dropzone shows a toast
  "Pick who you are representing first".
- ✅ "Skip upload — enter details manually" is also disabled until a
  selection is made.
- ✅ Once a choice is made, the dropzone activates and Continue
  enables (assuming a doc is uploaded or manual mode is chosen).

### 1.2 Drag-and-drop no longer dims the background
**How to test.** With the wizard open and a representation chosen,
drag a file from your desktop over the wizard's dropzone.

**Expected result.**
- ❌ The orange "Drop to upload" full-page overlay (the global intake
  overlay) does NOT appear behind the wizard.
- ✅ Only the wizard's local dropzone highlights (champagne border +
  scale-up).
- ✅ After releasing, the file appears in the wizard's uploaded list
  and the IntakeConfirmationModal does NOT pop on top of the wizard.
- ✅ A second drag works immediately — no stuck "drag" state.

### 1.3 Split button hidden for single-page PDFs
**How to test.** Upload a single-page PDF, then upload a multi-page
PDF.

**Expected result.**
- ❌ Single-page PDF: no "Split" button on its row.
- ✅ Multi-page PDF: "Split" button visible.
- ✅ Clicking Split opens the page-range dialog **above** the wizard
  modal (the "screen goes dim" bug is gone).
- ✅ Splitting succeeds and the new section documents replace the
  source PDF in the list; clicking Continue parses each section
  separately.

### 1.4 Multi-file upload + Remove
**How to test.** Drop multiple PDFs at once, then click the X to
remove one.

**Expected result.**
- ✅ All dropped files appear in the list with a count chip
  ("Uploaded · N").
- ✅ Removing a file decrements the count; Continue stays enabled if
  at least one doc remains.

### 1.5 Manual fallback
**How to test.** With representation picked but no file uploaded,
click "Skip upload — enter details manually".

**Expected result.**
- ✅ Wizard jumps directly to Step 3 (Address & Contacts) — Step 2 is
  skipped.
- ✅ AI banner is NOT shown on subsequent steps (manual mode).

---

## 2 · Step 2 — AI Parsing

### 2.1 Parsing runs and resolves
**How to test.** Upload a real purchase agreement and click Continue.

**Expected result.**
- ✅ Hero card shows "AI extraction in progress" with a pulsing
  Sparkles icon and a 4-phase ordered list.
- ✅ Per-document confidence bar appears once parsing completes.
- ✅ Once all documents are parsed/failed, the wizard auto-advances
  to Step 3.
- ✅ If parsing fails, an amber warning banner appears and a
  "Continue Manually" outline button is offered.

### 2.2 Step 1 → Step 2 → Step 1 → Step 2 round-trip
**How to test.** Upload a doc, click Continue (parsing starts), click
Back, click Continue again.

**Expected result.**
- ✅ Continue is enabled on Step 1 even while a doc is mid-parse
  (status `parsing`).
- ✅ Re-entering Step 2 does NOT re-trigger parsing (no duplicate
  network calls in DevTools).
- ✅ Manual-mode fallback is NOT mistakenly triggered.

---

## 3 · Step 3 — Address & Contacts

### 3.1 Step label rename
**How to test.** Look at the wizard's left rail and the right-panel
step header.

**Expected result.**
- ✅ Both read "Address & Contacts" (not "Address").

### 3.2 Removed elements
**Expected result.**
- ❌ "I confirm this address is correct" checkbox.
- ❌ "Start typing — your browser will suggest matching addresses."
  hint under the Property Address heading.
- ❌ "Capture the full contact card for each." subhead.

### 3.3 Banner copy
**How to test.** Reach Step 3 after AI parsing.

**Expected result.**
- ✅ Banner reads: "Fields that still need your attention are
  highlighted below. Everything else was filled by AI — please verify
  before continuing."

### 3.4 Address autocomplete
**How to test.** Begin typing in the Street Address field.

**Expected result.**
- ✅ Browser-native autocomplete + a datalist of recent transaction
  addresses is offered.
- ✅ Selecting one auto-populates City / State / ZIP / County.

### 3.5 Parties section title and prompt
**Expected result.**
- ✅ Section header reads "Parties & Contacts".
- ✅ Subtitle reads exactly "Who's involved in this deal?" (no other
  copy).

### 3.6 "Add Party" — add and focus
**How to test.** Click the section-header "Add Party" button.

**Expected result.**
- ✅ A new empty party card appears at the end of the list.
- ✅ The page auto-scrolls so the new card is visible.
- ✅ The Name input of the new card is auto-focused.

### 3.7 Empty-state prompt
**How to test.** Open Step 3 with no parties yet (skip the manual
flow).

**Expected result.**
- ✅ A single-line dashed-border champagne prompt: "Add at least one
  party — typically the buyer or seller you're representing."
- ❌ A second / duplicate "Add Party" button inside the prompt.
- ✅ The section-header "Add Party" remains visible directly above.

### 3.8 Add Another Party (bottom repeater)
**How to test.** Add at least one party, then look below the last
card.

**Expected result.**
- ✅ A small ghost-style "Add Another Party" button (matching the
  visual scale of the section-header button) is centered under the
  list.
- ❌ A full-width dashed mega-card or oversized CTA.

### 3.9 Party card layout — AI vs manual identical
**How to test.** Add a manual party (via Add Party) AND let AI
extract a buyer/seller from a document. Inspect both cards on Step 3.

**Expected result.**
- ✅ Both cards have the same hairline border (`border-ve-border`),
  same white background, same header "Party N" (no " · AI Extracted"
  suffix).
- ❌ Champagne tint or any other visual differentiation between AI
  and manual cards.

### 3.10 Required fields per party
**How to test.** Add a party. Try filling the fields one at a time
and watch the Continue button.

**Expected result.**
- ✅ Email and Phone Number labels show a red `*`.
- ✅ Continue stays disabled until: name + email + phone are all
  filled for every party AND address is complete.

### 3.11 Email / Phone autocomplete from contacts
**How to test.** In a party card, type the start of a known
contact's name into Name; or an email address into Email; or a phone
into Phone.

**Expected result.**
- ✅ A datalist offers matching contacts.
- ✅ Selecting a contact via Name backfills the matching contact's
  email + phone.
- ✅ Selecting via Email backfills name + phone.
- ✅ Selecting via Phone backfills name + email.

### 3.12 "Needs attention" highlight (subtle, type-led)
**How to test.** Reach Step 3 with empty required fields.

**Expected result.**
- ✅ Each empty required field's label has a small champagne **dot**
  (~6 px) before it.
- ✅ The input itself shows a soft champagne border + faint wash
  (`border-ve-orange/70 bg-ve-orange-soft/15`).
- ❌ "NEEDS ATTENTION" pill, AlertTriangle icon, full champagne fill,
  thick left-edge stripe, ring-offset boxed look.
- ✅ Once a value is entered, the dot and wash disappear.

---

## 4 · Step 4 — Purchase Information

### 4.1 Banner
**Expected result.**
- ✅ Same updated copy as § 3.3 (when AI banner is shown).

### 4.2 "Who's Transaction Is It?" role gate
**How to test.** Log in as each role and open the wizard.

**Expected result.**
- ✅ Agent: section is NOT shown.
- ✅ TC (Elf): section visible, dropdown shows TC themself + users
  associated with their account.
- ✅ TeamLead: section visible, dropdown shows TL + their team
  members.
- ✅ Admin: section visible, dropdown shows all users in the system.

### 4.3 "Who are you representing?" removal from Step 4
**Expected result.**
- ❌ Step 4 does NOT have a "Who Are You Representing?" select. (It
  lives on Step 1 as a radio.)

### 4.4 "Is The Buyer Getting A Mortgage?"
**Expected result.**
- ✅ Replaces the old "Closing mode" field, marked required.
- ✅ Options: Yes / No.
- ✅ Selecting Yes reveals a "Mortgage Type? (Helps AI Process Your
  Transaction)" dropdown with options FHA / Insured Conventional /
  Conventional / VA / USDA / Portfolio / Hard Money / Other.
- ✅ Selecting No hides Mortgage Type and clears its value.

### 4.5 Field renames
**Expected result.**
- ✅ "Final purchase price" → "Purchase Price"
- ✅ "Earnest money" → "Earnest Money Amount"
- ✅ "Insurance commitment days" → "Days For Homeowners Commitment"
- ✅ "Inspection days" → "Is The Buyer Getting A Home Inspection?"
  (Yes/No → "Days For Home Inspection")
- ✅ "Home warranty" → "Is The Buyer Getting A Home Warranty?"
  (Yes/No → "Home Warranty Ordered By: Buyer/Seller")
- ✅ "HOA" → "Is The Home Governed By An HOA?" (Yes/No → "Days For
  HOA Doc Delivery")

### 4.6 Money fields
**Expected result.**
- ✅ Purchase Price and Earnest Money show a leading `$` and live
  comma-formatted thousands separators while typing.
- ✅ The submitted payload sends a plain numeric value (no `$`,
  no commas).

### 4.7 Date constraints
**How to test.** Try entering a future date in Contract Acceptance
Date or a past date in Closing Date.

**Expected result.**
- ✅ Contract Acceptance Date input has `max=today`; the calendar
  greys out future days.
- ✅ Closing Date input has `min=today`; the calendar greys out past
  days.
- ✅ Possession Date is unconstrained (can be before or after
  closing).

### 4.8 "Who Orders Title" dropdown
**Expected result.**
- ✅ Options: Buyer, Seller. (Only those two.)
- ❌ "Other".

### 4.9 Custom contingencies
**How to test.** Click "Add Contingency" in the Additional
Contingencies block.

**Expected result.**
- ✅ A row with Name + Days inputs + remove icon appears.
- ✅ A bottom centered ghost "Add Another Contingency" button (same
  scale as Add Party bottom repeater) is shown once at least one row
  exists.
- ❌ Full-width dashed mega-card.

### 4.10 Notes + Pin
**Expected result.**
- ✅ Pin checkbox is positioned to the right of the "Notes" label,
  above the textarea.
- ✅ Pin label reads exactly "Pin This Note To The Top Of The
  Transaction Log".
- ✅ Pin is disabled when Notes is empty.

### 4.11 Dynamic field ordering (priority-first)
**How to test.** With AI parsing complete, scan the Deal Type &
Pricing section.

**Expected result.**
- ✅ Fields that AI did NOT fill (i.e. still need attention) are
  ordered ABOVE fields that AI did fill, within the section grid.
- ✅ Once a user enters a value into a previously unfilled field,
  the field's "needs attention" indicator disappears and the field
  drops to the bottom of the priority order.

---

## 5 · Step 5 — Missing Information

### 5.1 Friendly field names
**How to test.** Force at least one missing required field (e.g.
clear Closing Date in Step 4 then continue) so Step 5 surfaces it.

**Expected result.**
- ✅ Each missing-field row shows the human-readable label
  ("Closing Date", "Purchase Price", "Days For Home Inspection") —
  NOT the data key (`purchase.closing_date`).

### 5.2 Date and money input types
**Expected result.**
- ✅ Date fields render a native `type="date"` calendar picker.
- ✅ Money fields render with a leading `$` and comma formatting on
  the displayed value.
- ✅ Plain text fields render a regular input.

### 5.3 AI Search
**How to test.** Click "AI Search" on a missing field row.

**Expected result.**
- ✅ Spinner appears while running.
- ✅ If results return, each shows value + source + confidence and a
  "Use" button to apply.
- ✅ If no results, an amber feedback message appears.
- ✅ Errors render in a red feedback panel.

---

## 6 · Step 6 — Confirm

### 6.1 Hero card
**Expected result.**
- ✅ Champagne accent stripe across the top.
- ✅ Mono kicker "✦ Ready to Create" in champagne.
- ✅ Property street address in serif Lora at ~24 px.
- ✅ City / State / ZIP as a muted subtitle.
- ✅ Three metric tiles in a row: **Purchase Price**, **Closing**,
  **Accepted** — with mono uppercase labels and serif values.
- ✅ Dates render formatted as "Jun 15, 2026" (not raw ISO).
- ✅ A chip strip showing "Representing [Buyer/Seller/Both]" +
  "Cash" or "Financed · [Mortgage Type]" + (when known)
  "Owner-Occupied" or "Investment".
- ✅ A pencil icon in the top-right corner of the hero edits the
  address.

### 6.2 Parties card
**Expected result.**
- ✅ Header reads "PARTIES · N" (count badge).
- ✅ Each party row shows: champagne avatar circle with two-letter
  initials, name in bold + small role pill, and a muted line with
  email · phone.
- ✅ Edit pencil button at top-right of the card.

### 6.3 Purchase Information card
**Expected result.**
- ✅ Header reads "PURCHASE INFORMATION".
- ✅ Top half: 2-column SummaryPair grid for Earnest Money,
  Possession Date, Title Ordered By, Days for Homeowners Commitment.
- ✅ Bottom half: a Contingencies sub-section with a green check icon
  for active contingencies and a muted dash for inactive ones.
- ✅ Custom contingencies appear as additional checked rows with name
  + days.
- ✅ Edit pencil button at top-right of the card.

### 6.4 Notes / Pinned Note card (conditional)
**How to test.** Add a long note (multi-line, with explicit
newlines) on Step 4, mark it pinned, advance to Step 6.

**Expected result.**
- ✅ Card title reads "PINNED NOTE" with a small champagne pin icon
  to the left of the label (or "NOTES" if not pinned).
- ✅ Note body wraps cleanly using `whitespace-pre-wrap break-words`
  — long single words don't overflow, line breaks are preserved.
- ❌ The note overflowing into other layout columns (the original
  bug).

### 6.5 Documents card
**Expected result.**
- ✅ Header reads "DOCUMENTS · N".
- ✅ Each row: champagne file-icon tile, filename in bold, "AI
  confidence · X%" muted subline, and a coloured confidence pill on
  the right (green ≥ 80, amber ≥ 50, red otherwise).
- ✅ Empty state when no documents: "No documents uploaded."

### 6.6 Edit jump-back
**How to test.** From Step 6, click any Edit pencil. Make a change
on the destination step. Click Continue.

**Expected result.**
- ✅ The wizard returns DIRECTLY to Step 6 (does not walk forward
  step-by-step through Missing Info etc.).

### 6.7 Submit
**How to test.** Click "Create Transaction" / "Accept & Create
Transaction".

**Expected result.**
- ✅ Submit button shows a spinner + "Creating…" while pending.
- ✅ On success, a toast appears with the generated tasks count.
- ✅ The wizard closes and the user lands on the transactions list
  with the new transaction highlighted.
- ✅ If a pinned note was set, it appears at the top of the new
  transaction's History panel under a "Pinned Notes" group.
- ✅ Documents uploaded in the wizard are linked to the new
  transaction.

---

## 7 · Stepper (Left Rail)

### 7.1 Hover region consistency
**How to test.** Hover each step in the left rail.

**Expected result.**
- ✅ Every step's hover swatch is the same width — regardless of
  label length ("Documents" vs "Address & Contacts" vs "Confirm").
- ✅ The dot stays vertically aligned with the connecting line on
  every row.

### 7.2 Hover layout balance
**Expected result.**
- ✅ Inside the hover swatch, dot + label are vertically centered.
- ✅ A few pixels of padding cushion the content; the highlight
  doesn't feel like a stretched bar.
- ✅ The connecting line passes cleanly through every dot.

### 7.3 Click-to-jump (visited steps)
**How to test.** Walk through Steps 1–4. Then click each previous
step in the rail.

**Expected result.**
- ✅ Steps 1, 2, 3, 4 are clickable (visited). Cursor changes to
  pointer; click navigates.
- ✅ After clicking back to Step 1, you can click forward to Step 4
  directly without walking through 2 and 3.
- ✅ Step 5 / 6 (unvisited) are NOT clickable — cursor stays default,
  no hover background.

### 7.4 Step labels capitalized
**Expected result.**
- ✅ All step labels are in Title Case ("Address & Contacts",
  "Purchase Info", "AI Parsing"). No "address & contacts".

---

## 8 · Discard Confirmation Dialog

### 8.1 No native browser dialog
**How to test.** Upload a document or fill a field (so wizard becomes
dirty), then click the X close button or hit Escape.

**Expected result.**
- ❌ Chrome / Safari / Firefox native confirm dialog.
- ✅ Branded AlertDialog appears in front of the wizard.

### 8.2 Dialog visual style
**Expected result.**
- ✅ White rounded card on a 45 % black + 3 px blur backdrop.
- ✅ Mono champagne kicker "✦ CONFIRM" at the top.
- ✅ Serif title "Discard this transaction?" at ~20 px.
- ✅ Body in muted secondary copy.
- ❌ A square champagne icon tile / AlertTriangle icon (the previous
  "dated" treatment).
- ✅ Two right-aligned buttons: ghost "Keep editing" + solid
  charcoal "Discard" (using `bg-ve-text-primary`, NOT bright red).

### 8.3 Dialog behavior
**How to test.** Run through each interaction.

**Expected result.**
- ✅ "Keep editing" closes only the dialog; the wizard remains open
  with state preserved.
- ✅ "Discard" closes both the dialog and the wizard; URL `?new=1`
  is removed.
- ✅ Clicking the dialog backdrop or pressing Escape inside the
  dialog cancels (= "Keep editing").
- ✅ Reopening the wizard after a discard starts fresh
  (`isDirty=false`).

---

## 9 · Cross-Cutting / Visual

### 9.1 Money formatting on every field
**Expected result.**
- ✅ Every monetary value (Purchase Price, Earnest Money, confirm
  hero metric tile, confirm Earnest Money pair) shows a leading `$`
  and comma thousands separators.

### 9.2 Title-cased section labels
**Expected result.**
- ✅ All form section headings and field labels are in Title Case
  (e.g. "Days For Home Inspection", not "days for home inspection").

### 9.3 Dropdowns populated
**Expected result.**
- ✅ Every dropdown has its full set of options (representation
  radio, mortgage Yes/No, mortgage type, title-ordered-by, party
  role, transaction owner, etc.). No empty or half-wired dropdowns.

### 9.4 No raw browser dialogs
**Expected result.**
- ❌ `window.confirm()`, `window.alert()`, `window.prompt()` anywhere
  in the wizard or its surrounding components.

### 9.5 Z-index correctness
**How to test.** Inside the wizard modal, trigger:
- The PDF Split dialog (Step 1)
- The Discard Confirmation dialog (close while dirty)
- Toasts (e.g. upload failure)

**Expected result.**
- ✅ All three render visually ABOVE the wizard modal — the wizard's
  body is dimmed/blurred behind, and the secondary dialogs are fully
  interactive without being clipped.

---

## 10 · Step 7 — Review Your Timeline

> New step between Confirm and the Compliance checklist
> (AI_WIZARD_SUPERIORITY_COMPLETION_PLAN §4). Everything here is
> mouse-only: steppers, dropdowns, and date pickers.

### 10.1 Anchor gate
**How to test.** Walk a document flow through Confirm Details. You land
on "Review Your Timeline".

**Expected result.**
- ✅ A champagne card asks "Does this Date of Acceptance look right?"
  with the extracted date in large numerals.
- ✅ If the date came from the document, a "View in document" link jumps
  the right-hand PDF viewer to the cited page.
- ✅ The deadline list below is dimmed with the hint "Confirm the anchor
  first; every deadline below is calculated from it".
- ✅ The "Confirm Timeline" button is disabled until you click
  "Looks good".
- ✅ "Edit date" opens an inline date picker; no navigation.
- ✅ With a document that has no acceptance date (or manual mode), the
  card honestly says "I couldn't find a Date of Acceptance in the
  documents" and offers only a date picker — no made-up date.

### 10.2 Deadline list and basis chips
**How to test.** Click "Looks good" and read the list.

**Expected result.**
- ✅ Every row shows a name, a date, and HOW it was calculated (e.g.
  "5 days after Date of Acceptance", "From the contract").
- ✅ Only dated rows appear. Operational tracking dates (EM Delivered,
  CD Delivered, Cleared to Close) are NOT here — they live in the
  Active Transactions drawer.
- ✅ Core dates (Closing, Possession) have no Remove button.

### 10.3 Editing and the cascade
**How to test.** Click "Edit date" on the anchor card and pick the next
day.

**Expected result.**
- ✅ An amber summary appears: "N deadlines and M task dates moved".
- ✅ "Review changes" expands an old → new diff (old date struck
  through).
- ✅ Editing a derived row (e.g. Home Inspection Deadline) offers a Days
  stepper ("[7] days after Date of Acceptance") or a specific date —
  picking a date converts it to the day count; weekends/holidays roll
  forward automatically (the shown date may shift to the next business
  day — that is correct, not a bug).

### 10.4 Custom deadlines
**How to test.** Click "+ Add deadline", type a name (e.g. "Septic
inspection"), keep the relative rule (3 days after Date of Acceptance),
click "Save deadline".

**Expected result.**
- ✅ The new row appears with the server-computed date and the rule text.
- ✅ Remove shows a "Removed … Undo" chip; Undo restores it.
- ✅ After Approve & Create, the deadline exists as a task (milestone
  "Deadline") in My Task Queue and on the Closing Calendar, dated by
  the rule.

---

## 11 · Step 8 — Confirm Your Compliance Checklist

> New step between Timeline and Review Tasks (plan §5). The list is
> deterministic: same use case + same contract terms = same rows, every
> time. No spinner theater.

### 11.1 Generated rows
**How to test.** Confirm the timeline and read the checklist.

**Expected result.**
- ✅ Document rows match the transaction type (e.g. Closing Disclosure
  only on financed deals; Proof of Funds only on cash deals).
- ✅ Rows gated by contract terms (HOA Documents Package, Home Warranty
  Order Confirmation) appear ONLY when those terms are true, with a
  "From contract terms" chip.
- ✅ Each row shows a due date and its basis ("3 days after acceptance").
- ✅ With exactly ONE uploaded document, the Purchase Agreement row is
  checked green "Uploaded · <your file name>". With several uploads,
  nothing auto-matches; each row offers "Attach document", which opens a
  modal: pick one of the uploaded files by radio, or switch to "Upload a
  new file" and drop the document right there.
- ✅ The search box filters rows as you type (optional typing).

### 11.2 Add, edit, remove
**How to test.** Use "+ Add document", the pencil, and the trash on a row.

**Expected result.**
- ✅ "+ Add document" opens a MODAL (not a card expansion): drag the file
  in or click to browse (the file is optional), the name auto-fills from
  the file name, and the due date is None / a relative rule via stepper +
  branded dropdowns / a specific date.
- ✅ Adding WITH a file shows the row already green ("Uploaded · <name>")
  — the file is real, uploads immediately, and lands on the transaction
  at Approve & Create. Saving a draft also keeps it.
- ✅ After an upload, a champagne "AI is checking this document…" chip
  appears on the row, then settles into a verdict ("AI read this as …").
  Attaching a deliberately WRONG file to a library row (e.g. a purchase
  agreement onto Earnest Money Deposit Receipt) shows the amber warning
  "AI read this as … - expected …" with "Keep my type" and "Remove file"
  — it warns, it never blocks.
- ✅ Edit (pencil) stays inline under the row, same editor fields.
- ✅ Remove shows the Undo chip (hover the trash: "Removed library items
  are recorded as waived"). Removed rows are NOT deleted at create: they
  are saved as "waived" and can be un-waived later from the
  Documents view.

### 11.3 Use your own checklist
**How to test.** Click "Use your own checklist" → Paste text tab → paste
two lines ("Septic Certificate", "Well Test") → "Read checklist".

**Expected result.**
- ✅ A review list appears with both rows CHECKED but NOT yet added.
- ✅ Unchecking one and clicking "Add 1 document" adds only the checked
  row to the checklist. Nothing was added without that click.
- ✅ The Upload tab accepts PDF/TXT/CSV; a scanned image-only PDF says
  honestly that no items were found and suggests the paste tab.
- ✅ "Add as tasks instead" adds the rows as Manual tasks on the Review
  Tasks step (the older paste behavior).

### 11.4 Life after the wizard
**How to test.** Create the transaction, open its Documents view (the
Transaction Documents modal from the Active Transactions card).

**Expected result.**
- ✅ A "Missing documents" group lists the same open rows you confirmed,
  each with a due chip (red when overdue).
- ✅ "Attach document" opens the shared modal: pick one of the
  transaction's documents by radio (filter box when there are many), or
  upload a new file right there; Attach flips the row to uploaded.
- ✅ "Waive" hides the row into a collapsible "Waived" group with
  Un-waive.
- ✅ The mail icon ("Request … by email") lets you pick a party; it files
  a DRAFT into AI Email Review. Verify nothing was sent: the draft sits
  in /ai-emails awaiting approval.
- ✅ Uploading a document whose detected type matches an open row shows a
  confirm chip ("Is <file> the <document>?"); nothing links without
  your Yes.
- ✅ A quick-create (modal) transaction ALSO has a default checklist on
  its Documents view — wizard and quick-create files behave the same.

---

## 12 · Step 9 — Review Tasks upgrades

### 12.1 Relative due rules
**How to test.** On Review Tasks, click "Rule…" beside a task's date.
Set "3 days before Closing Date", Save rule.

**Expected result.**
- ✅ The date updates to the server-computed value (weekend rolls
  forward) and the basis line shows "3 days before Closing Date" with a
  "rule" chip.
- ✅ Typing a date directly instead clears the rule (they are mutually
  exclusive; the "edited" chip shows).
- ✅ After create, the task on the Tasks view carries the rule-derived
  date.

### 12.2 Related compliance item
**How to test.** Open the "Related document" dropdown on a task.

**Expected result.**
- ✅ It lists exactly the checklist rows from the previous step plus
  "None". Selecting one links the task to that document at create.

### 12.3 Auto-Email toggle
**How to test.** Find a task targeted at a person whose email you
captured (e.g. a Buyer task when the buyer has an email), and one
targeted at "Agent".

**Expected result.**
- ✅ The "Auto-Email off" chip appears ONLY on tasks whose target
  resolves to a real captured email. The Agent task shows no toggle at
  all (no disabled mystery controls).
- ✅ Turning it on shows: "When this task comes due, I draft the email
  to <name> (<email>) for your review. Nothing sends without approval."
- ✅ After create, when the task is due and the admin reminders run
  fires (POST /ai-emails/reminders/run or the daily cron), exactly ONE
  draft appears in /ai-emails per task per due date — re-running the
  sweep adds nothing. Nothing is ever sent automatically.

### 12.4 Search and descriptions
**Expected result.**
- ✅ A "Search tasks…" box filters the list as you type.
- ✅ Tasks show their one-line description under the name.

---

## 13 · Top stepper (public phases)

**Expected result.**
- ✅ The top bar shows "Step X of 5 · <phase>" over five dots: Upload,
  Review details, Timeline, Compliance, Tasks & create.
- ✅ Back still walks every internal screen one at a time.
- ✅ Resuming an older saved draft restores it at its saved screen; the
  new Timeline and Compliance steps simply start fresh when reached.

---

## 14 · Regression Smoke

After any change touching the wizard, also re-verify:

- ✅ A full happy-path flow: upload one PDF → AI parses → land on
  Step 3 → fill any flagged field → Step 4 fill price + dates → Step
  5 (skip if all captured) → Confirm → "Looks good" + Confirm Timeline
  → Confirm Checklist → review tasks → Create.
- ✅ The created transaction appears at the top of the active
  transactions list with the highlight ring.
- ✅ Tasks were generated (see toast and the History panel).
- ✅ The Documents view shows the Missing documents group matching the
  confirmed checklist.
- ✅ No console errors or warnings.

---

## 15 · The AI plan: suggestions, Autopilot, and the command bar

> Part II of the plan (§16–§22): after parsing, the AI now READS the deal
> and proposes deal-specific deadlines, documents, tasks, and watch-outs.
> Everything it proposes carries a citation back into the document and a
> confidence score; nothing applies without your click (or one Autopilot
> approval). All mouse-only.

### 15.1 AI suggestions on the Timeline step
**How to test.** Upload a packet that contains a deal-specific
contingency the standard timeline does not cover (e.g. a septic
evaluation addendum). Walk to "Review Your Timeline".

**Expected result.**
- ✅ Below the deadline list, an "AI suggestions" group shows a card per
  proposal: name, the RULE it proposes (e.g. "14 days after Date of
  Acceptance"), a confidence chip ("AI · 93%"), and a citation line
  (page + the contract's own words).
- ✅ Clicking the citation jumps the right-hand viewer to that page with
  the snippet highlighted. Every suggestion has a working citation — if
  the AI can't show where it read something, the suggestion never
  appears.
- ✅ "Add" turns the card into a normal deadline row (champagne "AI"
  chip on the row); "Skip" dismisses it. Nothing was added before the
  click.
- ✅ High-confidence suggestions (at or above the admin threshold,
  Settings → Confidence) arrive PRE-ACCEPTED with a subtle check — one
  click reverses them.
- ✅ The dates obey the same cascade as every other row: change the
  anchor date and the AI rows move too.
- ✅ A mini timeline strip at the top shows the whole deal as dots
  (navy core dates, orange AI additions, a dashed "today" marker).

### 15.2 AI suggestions on the Checklist step
**How to test.** Continue to "Confirm Your Compliance Checklist".

**Expected result.**
- ✅ Deal-specific document suggestions appear the same way (card,
  confidence, citation, Add/Skip).
- ✅ A WAIVE suggestion (e.g. "Buyer waived inspection — waive the
  Inspection Report row?") is NEVER pre-accepted, no matter the
  confidence. It always waits for your click.
- ✅ If the AI found nothing beyond the standard list, there is no empty
  "suggestions" box — a quiet line says the standard checklist covers
  this deal.

### 15.3 The deal brief
**How to test.** Look above the timeline (and again on the final
confirm screen).

**Expected result.**
- ✅ A short brief in plain sentences: price, financing, the two or
  three dates that matter, and "watch out" lines.
- ✅ Every watch-out has a citation link into the document. The factual
  sentences (price, dates) exactly match the confirmed fields — the
  brief never contradicts the form.

### 15.4 Autopilot — the 3-click intake
**How to test.** Upload a clean, complete packet (all core fields
present, every party with name + email + phone, both AI passes
agreeing). Click "Start Intake".

**Expected result.**
- ✅ After parsing, a single Autopilot banner says everything checked
  out: N fields verified, M deadlines, K documents, all suggestions
  verified. One "Looks good" click, then one "Approve & Create" click.
  Three clicks total, start to finished transaction.
- ✅ The banner lists what will be created BEFORE you approve — nothing
  is hidden behind the shortcut.
- ✅ "Review step by step" is always offered next to the shortcut and
  walks the normal steps.

### 15.5 Autopilot interrupts honestly
**How to test.** Upload a packet where a party has no phone number (or
remove one on the parties screen).

**Expected result.**
- ✅ Autopilot does NOT offer the shortcut. It says exactly what is
  missing ("The buyer has no phone number") and drops you on that step
  with the field focused.
- ✅ Fixing the field brings the shortcut back.

### 15.6 The command bar
**How to test.** On the Timeline, Checklist, Confirm, or Review Tasks
step, click the "Tell me what to change" bar and type:
`add a septic inspection deadline 14 days after acceptance`.

**Expected result.**
- ✅ The bar answers with a PREVIEW of what it understood ("Add deadline
  'Septic inspection' · 14 days after Date of Acceptance — computed
  date <date>") and Apply / Cancel buttons. Nothing changed yet.
- ✅ Apply adds the row exactly like the manual editor would (same
  server-computed date, same cascade behavior) and shows an Undo chip;
  Undo restores the previous state completely.
- ✅ Try `waive the home warranty row` and `turn on auto-email for the
  earnest money task` — same preview-then-apply pattern.
- ✅ Type nonsense (`make it rain`). The bar says it can't map that to
  an action and lists the kinds of things it CAN do. It never guesses.

### 15.7 Comfort check (the v2 scale)
**How to test.** Walk any wizard flow at 100% browser zoom.

**Expected result.**
- ✅ No squinting: body text reads at 15px, labels at 12.5px, and no
  text anywhere in the wizard is smaller than 12px.
- ✅ Section titles are serif 20px; the anchor date is large serif.
- ✅ Status chips and confidence chips are legible at arm's length.
- ✅ Compare against any non-wizard page (e.g. the dashboard): the
  wizard should feel noticeably easier on the eyes. (The app-wide
  rollout is a separate decision — D13.)

---

## Bug Reporting Template

When a check fails, file with:

```
Section: WTG-X.Y (e.g. WTG-3.10 Required fields per party)
Environment: dev.velvetelves.com / browser+version / role
Steps to reproduce: 1. … 2. … 3. …
Expected: <copy from this guide>
Actual: <what you saw>
Screenshot: <attach>
```

---

*Last revised: 2026-06-11 (Part II: AI suggestions, Autopilot, command bar, deal brief, v2 comfort scale).*
