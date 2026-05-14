# Transaction Card — UI/UX Audit & Remediation Plan

> **Scope.** The `TransactionCard` component
> ([velvet-elves-frontend/src/components/shared/TransactionCard.tsx](../velvet-elves-frontend/src/components/shared/TransactionCard.tsx)),
> as rendered on the Active Transactions page and anywhere else it is reused
> (Attorney Workspace, dashboards, search results).
>
> **Trigger.** Jake reports that the majority of text on the card is too
> small to read comfortably. The most-cited offenders are the **Tasks**
> and **Contacts** "+ Add" buttons (which look decorative rather than
> interactive) and the dense micro-text inside the **Tasks** and
> **Key Dates** drawer columns.
>
> **Goal.** Bring the card into compliance with the
> [STYLE_GUIDE](./STYLE_GUIDE.md) typography contract, and along the way
> clean up several adjacent legibility and affordance issues.

---

## 1 · Diagnosis

### 1.1 The core problem — typography drift

The style guide ([STYLE_GUIDE.md §3.2](./STYLE_GUIDE.md)) defines an
explicit canonical scale:

| Role                                   | Spec                                                                                                                    |
| -------------------------------------- | ----------------------------------------------------------------------------------------------------------------------- |
| Body                                   | `text-[13px] leading-[1.55]`                                                                                            |
| Card body / secondary                  | `text-[12.5px] leading-relaxed`                                                                                         |
| Field label (form)                     | `text-[11.5px] font-medium tracking-wide`                                                                               |
| Mono kicker (uppercase label)          | `font-mono text-[9px] tracking-[1.8px] uppercase` — **9 px is the floor; mono is reserved for ≤ 4-word labels.**        |
| Buttons (size="sm")                    | `text-[11.5px]–[12.5px]` per §6.1                                                                                       |
| Help text                              | `text-[11.5px] text-ve-charcoal-soft/75` per §9.1                                                                       |

The card was authored with an internal scale that runs **8–12 px**,
roughly two steps below spec across almost every role:

- 51 occurrences of `text-[Npx]` where `N ≤ 12` in this single file.
- The lowest size (`text-[8px]`) is **below the mono-kicker floor**.
- The default body inside the card is **12 px** rather than the
  spec-mandated 12.5 px.
- Three interactive elements ("+ Add" inline, contact "+ Add", task
  status selector) sit at **9–10 px**, which is below the §6.1 button
  minimum of 11.5 px and below the WCAG 2.5.5 ~24 px hit-target target
  (the buttons are also short-height with no `min-h`).

### 1.2 Inventory of every undersized element

Locations are `TransactionCard.tsx:<line>`. "Issue" notes which spec
rule is violated; the right-hand column is the recommended fix.

#### Collapsed card face

| # | Element                                  | Line  | Current             | Issue                                             | Target                                                            |
|---|------------------------------------------|-------|---------------------|---------------------------------------------------|-------------------------------------------------------------------|
| 1 | Client name (serif)                      | 355   | 14 / 15 / 17 px     | Below §3.2 hero serif (22–26) / section (16–18)   | `text-[16px] xs:text-[17px] md:text-[19px]`                       |
| 2 | Status pill (`STATUS_PILL`)              | 360   | 10 px               | Pill text should be ≥ 11 px per §6.4              | `text-[11px]` + slight padding bump                               |
| 3 | "Why" badges                             | 370   | 10 px               | Same — actionable badges read as decorative       | `text-[11px]`                                                     |
| 4 | Address line                             | 381   | 11 / 12 px          | Below 12.5 px card body                           | `text-[12px] md:text-[12.5px]`                                    |
| 5 | Assignee chip "👤 …"                     | 383   | 10 px               | Below pill floor                                  | `text-[11px]`                                                     |
| 6 | Next-step banner title                   | 398   | 12 / 12.5 px        | Banner is the headline action — should pop more   | `text-[13px] md:text-[14px]`                                      |
| 7 | Next-step subtitle                       | 402   | 11 / 11.5 px        | Below card body                                   | `text-[12px] md:text-[12.5px]`                                    |
| 8 | Next-step CTA button                     | 410   | 12 / 12.5 px        | Acceptable                                        | Keep `text-[12.5px] md:text-[13px]`                               |
| 9 | Primary-contact name (inline strip)      | 434   | 11 px               | Below card body                                   | `text-[12.5px]`                                                   |
| 10| Primary-contact role                     | 438   | 10 px               | Too small                                         | `text-[11.5px]`                                                   |
| 11| Primary-contact phone (mono)             | 446   | 11 px               | Acceptable but inconsistent with row              | `text-[12px]`                                                     |
| 12| Primary-contact email link               | 458   | 10.5 px             | Too small for a link                              | `text-[12px]`                                                     |
| 13| Bullet separators `·`                    | 437/443/455 | 10–11 px      | Punctuation illegible at this size                | `text-[12px]`                                                     |
| 14| Info badges row (Docs / History / etc.)  | 487   | 10.5 / 11 px        | Below pill floor; some are clickable              | `text-[11.5px] md:text-[12px]`                                    |
| 15| Info-badge value (the number)            | 497   | 10.5 px             | Too small for tabular data                        | `text-[12px] tabular-nums`                                        |
| 16| "Days to Close" label                    | 512   | 9 px tracking 0.5px | Tracking below mono-kicker spec (1.5–1.8 px)      | Keep 9 px, add `tracking-[1.5px]`                                 |
| 17| Close-date string                        | 516   | 9 px mono           | Date is decorative metadata — acceptable          | Keep, but add `tracking-[0.5px]`                                  |
| 18| "Overdue Tasks" / "Price" labels         | 534/549| 9 / 9.5 px         | Acceptable as kicker IF tracking & color obey §3.2| `text-[9px] tracking-[1.5px] uppercase`                           |

#### Expanded drawer — Tasks column

| #  | Element                       | Line | Current     | Issue                                                                              | Target                                          |
|----|-------------------------------|------|-------------|------------------------------------------------------------------------------------|-------------------------------------------------|
| 19 | "TASKS" kicker                | 572  | 9 px mono   | OK                                                                                 | Keep                                            |
| 20 | **Inline "+ Add" button**     | 575  | **9 px**    | **Below button floor (11.5 px §6.1) — Jake's #1 complaint. Looks like a label.**   | Convert to outline chip (see §2.3)              |
| 21 | Section titles inside tasks   | 584  | **8 px**    | **Below mono-kicker floor (9 px). Below any spec size.**                           | `text-[9px] tracking-[1.5px]`                   |
| 22 | Task label                    | 617  | 12 px       | One step below card body                                                           | `text-[12.5px] leading-[1.4]`                   |
| 23 | Task due line (mono)          | 624  | 10 px       | Too small — date is the entire point of this row                                   | `text-[11px] tracking-[0.3px]`                  |
| 24 | Status `<select>` "···"       | 634  | 10 px       | Below button floor; users don't notice it exists                                   | `text-[11px]` + `min-h-[24px]`                  |
| 25 | "+ Add Task" ghost button     | 659  | 11.5 px     | OK                                                                                 | Keep                                            |

#### Expanded drawer — Key Dates column

| #  | Element                             | Line | Current  | Issue                                       | Target                       |
|----|-------------------------------------|------|----------|---------------------------------------------|------------------------------|
| 26 | "KEY DATES" kicker                  | 668  | 9 px     | OK                                          | Keep                         |
| 27 | "(click to edit)" hint              | 670  | 9 px sans| Help text floor is 11.5 px (§9.1)           | `text-[11px]`                |
| 28 | Date label                          | 685  | 11.5 px  | Below 12.5 px card body                     | `text-[12.5px]`              |
| 29 | Date value (mono)                   | 688  | 11.5 px  | Below body; tabular data deserves emphasis  | `text-[12.5px] tabular-nums` |
| 30 | TBD suffix                          | 694  | 10 px    | Below 11.5 px help-text floor               | `text-[11px]`                |
| 31 | Edit ✏ glyph                        | 696  | 10 px    | Glyph — acceptable                          | Keep, but bump to 11 px      |

#### Expanded drawer — Contacts column

| #  | Element                             | Line | Current   | Issue                                                                       | Target                                |
|----|-------------------------------------|------|-----------|-----------------------------------------------------------------------------|---------------------------------------|
| 32 | "CONTACTS" kicker                   | 717  | 9 px      | OK                                                                          | Keep                                  |
| 33 | Group label ("BUYER", "LENDER")     | 724  | 9.5 px    | OK                                                                          | Keep                                  |
| 34 | **Group "+ Add" button**            | 732  | **10 px** | **Below button floor — Jake's #2 complaint. The 10 × 10 px icon is sub-WCAG.**| Convert to outline chip (see §2.3)    |
| 35 | Contact name                        | 768  | 12.5 px   | At spec                                                                     | Keep                                  |
| 36 | Contact secondary line (company)    | 772  | 10.5 px   | Below card body                                                             | `text-[12px]`                         |
| 37 | Phone/email mono in popped panel    | 810/818| 11 px   | Acceptable; bump for parity                                                 | `text-[12px]`                         |
| 38 | Chevron `▾`                         | 798  | 9 px      | Glyph — OK                                                                  | Keep                                  |
| 39 | Empty-state "Add Buyer / Seller"    | 836  | 12 px     | Below card body                                                             | `text-[12.5px]`                       |

#### Drawer footer + AI suggestions

| #  | Element                             | Line     | Current   | Issue                              | Target                                  |
|----|-------------------------------------|----------|-----------|------------------------------------|-----------------------------------------|
| 40 | "AI Suggestions for This Deal"      | 854      | 11 px mono| OK                                 | Keep                                    |
| 41 | AI suggestion buttons               | 861      | 11.5 px   | At button floor                    | Keep                                    |
| 42 | Footer buttons (Docs/Print/History) | 883/889/895/901 | 11 / 12 px | Below button floor on mobile  | `text-[12px] md:text-[12.5px]`          |
| 43 | Footer Delete button                | 910      | 11 / 12 px| Same                               | `text-[12px] md:text-[12.5px]`          |
| 44 | Footer price                        | 917      | 13 px     | OK                                 | Keep                                    |

### 1.3 Adjacent issues surfaced by the audit

Not strictly font-size, but discovered while measuring every line:

- **A. "+ Add" affordance.** The two complained-about buttons (lines
  575 & 732) are styled as inline orange text with no border, no
  background, no hover affordance other than `hover:underline`. Even
  at the correct font size they would read more as section labels than
  controls. The fix is **structural**, not just typographic.
- **B. Hit targets.** Several controls are below the WCAG 2.5.5
  recommendation (24 × 24 px minimum): the inline "+ Add" buttons,
  the status `<select>` (`py-[1px]`), the date row edit glyph, and the
  primary-contact email/phone links. Adding a `min-h-[28px]` and a
  little horizontal padding fixes them.
- **C. Visual density of the collapsed face.** The "primary contact"
  inline strip ([TransactionCard.tsx:430-465](../velvet-elves-frontend/src/components/shared/TransactionCard.tsx#L430-L465))
  packs name + role + bullet + phone + bullet + email-link into a
  single line, each piece at a different size and color. Even at
  corrected sizes this reads as a wall of small text. Recommendation:
  drop the redundant "Email" link (the icon-only Contacts-column
  email button already covers it) and let the phone be the only
  inline action, in mono.
- **D. Inconsistent mono tracking.** Per §3.3, all mono labels must
  use `tracking-[1.5px]–[1.8px]`. Lines 512 (`tracking-[0.5px]`) and
  672 (no tracking) drift off-spec.
- **E. "(click to edit)" instructional copy is a hint, not a kicker**
  ([TransactionCard.tsx:670-672](../velvet-elves-frontend/src/components/shared/TransactionCard.tsx#L670-L672)).
  It uses `font-sans normal-case` already — it should follow the help-text
  contract (`text-[11.5px] text-ve-charcoal-soft/75`).
- **F. Section headers inside the tasks scrollbox are 8 px** (line 584).
  This is the only size in the entire app that falls below the
  9 px mono-kicker floor. It came in as a "make this look like a
  tiny separator" choice, but it actively hurts scan-ability of what
  is otherwise the most-used drawer.
- **G. The status `<select>` shows "•••" by default** — discoverability
  is poor; users won't realise that's the door to Blocked / Skipped /
  In Progress. After resizing it, consider replacing the `<select>`
  trigger with a small "Status" pill that opens a popover menu, for
  consistency with the inline date edit.

### 1.4 Why the audit doesn't just say "bump every size by 1 px"

A blanket increase would break the collapsed-row grid (the right-hand
stats column has fixed `min-w-[52px]` slots and a hard `gap-[10px]`).
Three rows (name, badges, address) already wrap on mobile at 14 px.
Section §2 below ties the typography fix to a small set of layout
adjustments so the card still fits on a 360 px viewport.

---

## 2 · Plan

### 2.1 Typography pass (mechanical)

Single-PR atomic change. Apply the **Target** column from §1.2 verbatim.
Wrap the change in a quick visual diff:

1. Update every `text-[Npx]` per the audit table.
2. Add the missing `tracking-[1.5px]` to every `font-mono uppercase`
   that lacks it (items D, 16, 27).
3. Update the body-text default for the card so future additions
   inherit 12.5 px. The cleanest place is a top-level wrapper
   `text-[12.5px] leading-relaxed` on the root `<div>` at line 338.
   Children that already specify a size will keep theirs; only
   un-sized children inherit the new default.
4. No structural HTML changes in this pass. Goal is a "raise the floor"
   PR that's mergeable in isolation.

**Effort:** ~½ day. **Risk:** low — visual-only, no logic.

### 2.2 Layout adjustments to absorb the new sizes

Done **inside the same PR** as §2.1 so the regressions don't ship:

- Collapsed face grid: change
  `gap-[10px] md:gap-[14px]` → `gap-[12px] md:gap-[16px]`
  to give the now-12.5 px address line breathing room.
- Right-hand stats column: bump
  `min-w-[52px]` → `min-w-[60px]` for the overdue and price columns,
  and `min-w-[70px]` → `min-w-[78px]` for the "Days to Close" tile,
  so the new label sizes don't push the numbers off-center.
- Primary-contact inline strip (item C): remove the inline "✉ Email"
  link (kept under Contacts), reducing the row from five pieces to
  three (name · role · phone). Keeps the line scannable at the new
  larger sizes.

### 2.3 "+ Add" affordance fix (the headline complaint)

Replace the two text-link "+ Add" controls (Tasks header, Contacts
group header) with a single shared **outline chip** following the
"section-header outline + bottom ghost-repeater" pattern from
[STYLE_GUIDE.md §6.1 / §9.4](./STYLE_GUIDE.md):

```jsx
<button
  type="button"
  className="inline-flex items-center gap-[5px] rounded-full border-[1.5px]
             border-ve-orange-border bg-white px-2.5 py-[3px]
             text-[11.5px] font-semibold text-ve-orange
             hover:bg-ve-orange-light hover:text-ve-orange-xdark
             transition-colors min-h-[26px]"
>
  <Plus className="h-3 w-3" /> Add
</button>
```

Why a chip and not a full button:
- The drawer column is narrow; a full-height button would dwarf the
  9 px kicker beside it.
- The pattern matches the existing **info-badges** strip on the
  collapsed face, so the visual language stays consistent.
- A `border + hover` state turns it from "decorative text" into
  "obviously interactive" without raising the volume.

The wider "+ Add Task" ghost button at the bottom of the Tasks column
(line 658) **stays as-is** — it's the bottom ghost-repeater half of
the §9.4 pattern and is already at spec.

Empty-state contact card (lines 829-838) also stays — it's already a
dashed call-to-action card and reads correctly as interactive.

### 2.4 Hit-target sweep

While in the file, add `min-h-[28px]` (or `min-h-[24px]` for genuinely
inline controls) and a little horizontal padding to:

- The new "+ Add" chip (above).
- The status `<select>` on each task row.
- The date row click area (currently relies on `py-[6px]` of the
  flex container — fine, but make sure the `cursor-pointer` extends
  to the full row width).
- The primary-contact phone/email anchor pair on the collapsed face,
  which today are zero-padding inline anchors.

### 2.5 Drop the 8 px section title

Item F. Inside the Tasks scrollbox, change the `text-[8px]` section
divider to `text-[9px] tracking-[1.5px]` (still small, still mono,
but at-floor). If the section gets crowded after the size bump, the
right move is to **remove** these dividers and rely on whitespace +
the section count to separate buckets; the dividers were only
load-bearing because everything else was the same size.

### 2.6 Out-of-scope, but log

These are not part of this PR. Capture as follow-ups:

- The status `<select>` "•••" UX (issue G). Replace with a popover
  menu in a later UX pass; it's a real discoverability problem but
  not what Jake flagged.
- Mobile breakpoint review: the card has many `md:` overrides but no
  `xs:`/`sm:` ladder. After §2.2, re-test 360 px width and check
  whether the badges row still wraps gracefully.
- The MilestoneTimeline component sits inside the card but is not
  audited here; if Jake's "everything is small" complaint extends to
  it, audit separately — it has its own scale.

### 2.7 Acceptance criteria

A reviewer should be able to verify the fix without measuring pixels:

- [ ] No `text-[Npx]` with `N < 9` remains in `TransactionCard.tsx`.
- [ ] No `text-[Npx]` with `N < 11` remains on **any element with
      `onClick` / `onChange` / `href`** in this file (i.e., every
      interactive control clears the §6.1 button floor).
- [ ] The two "+ Add" controls render as outlined chips with visible
      borders at rest, not as bare orange text.
- [ ] The card still fits on a 360 px viewport without horizontal
      scroll, and the collapsed-face right-hand stats column does not
      wrap onto two rows on a 768 px viewport.
- [ ] Visual diff captured for the Active Transactions page (one
      collapsed card + one expanded card, light mode) and attached
      to the PR for Jake to sign off before merge.

### 2.8 Suggested rollout

One PR. The change is visual-only and bounded to a single file plus
its single direct consumer (the Active Transactions page already
uses the same component everywhere). No backend, no API, no migration.

Sequence within the PR:

1. Commit 1 — typography sweep (§2.1) + layout absorbers (§2.2).
   Reviewer can verify against the audit table.
2. Commit 2 — "+ Add" chip refactor (§2.3) + hit-target sweep (§2.4)
   + 8 px section title fix (§2.5). Reviewer can verify against the
   acceptance criteria.

Show Jake the rendered before/after on `dev.velvetelves.com` before
merge so he can confirm the fix lands where it hurt.
