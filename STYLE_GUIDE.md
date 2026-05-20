# Velvet Elves — UI/UX Style Guide

> The single source of truth for how Velvet Elves looks and feels.
> Every component, page, modal, dialog, and email template MUST conform to
> this document. When in doubt, copy an existing pattern that already
> conforms — don't invent a new one.

This guide is normative. The Tailwind config (`tailwind.config.js`) and
the global CSS variables (`src/index.css`) are the canonical token
sources; this document explains **how to compose them**.

---

## 1 · Brand Voice

Velvet Elves is a **calm, premium, AI-assisted real-estate workspace**.
The interface should feel like a high-end concierge, not a SaaS dashboard.

| Quality        | Means                                                    | Means NOT                                                  |
| -------------- | -------------------------------------------------------- | ---------------------------------------------------------- |
| **Calm**       | Whitespace, hairlines, restrained color                  | Heavy borders, rainbow alerts, modal storms                |
| **Premium**    | Lora serif accents, mono small caps, soft shadows        | All-sans body, ALL-CAPS shouty headers, bevels             |
| **AI-aware**   | Champagne (`#EE7623`) accent on AI-touched fields        | Robot icons, "AI Assistant" mascots, neon glows            |
| **Confident**  | Decisive defaults, fewer choices, clear hierarchy        | Wizard-only-on-rails, 12-step modals, alert-driven UX      |

**Tone of voice in copy.** Plain, direct, a little warm. Address the user
in the second person ("Drop files here", "Pick who you're representing").
Avoid jargon. Avoid exclamation marks. Avoid "Oops!".

---

## 2 · Color Palette

All color tokens live under `theme.extend.colors.ve` in
`tailwind.config.js`. Use the token, never the literal hex.

### 2.1 Brand spine

| Role                     | Token                  | Hex        | Use                                                   |
| ------------------------ | ---------------------- | ---------- | ----------------------------------------------------- |
| Primary brand (champagne)| `ve-orange`            | `#E26812`  | Primary CTA, active step, AI accent, "✦" kicker       |
| Brand dark (hover)       | `ve-orange-dark`       | `#C05A0A`  | Primary CTA hover                                     |
| Brand deepest (text)     | `ve-orange-xdark`      | `#8B3F00`  | Champagne text on light tinted backgrounds            |
| Champagne tint           | `ve-orange-light`      | `#FEF3E6`  | Subtle hover wash for ghost buttons                   |
| Champagne mid            | `ve-orange-mid`        | `#FDD9AD`  | (rare)                                                |
| Champagne border         | `ve-orange-border`     | `#F4BA87`  | Borders on champagne-tinted cards                     |
| Champagne soft (whisper) | `ve-orange-soft`       | `#FFF9F4`  | Background washes, AI-filled hint                     |
| Sidebar dark navy        | `ve-sidebar` (#1E3356) | `#1E3356`  | Wizard left rail, app sidebar                         |

### 2.2 Surfaces and ink

| Role                    | Token                | Hex        | Use                                                     |
| ----------------------- | -------------------- | ---------- | ------------------------------------------------------- |
| Page background         | `ve-bg`              | `#F4F4F4`  | Default page canvas                                     |
| Card surface            | `ve-surface`         | `#FFFFFF`  | All cards, modals, panels                               |
| Card secondary          | `ve-surface-2`       | `#F8F8F6`  | Nested / muted card surface                             |
| Hairline border         | `ve-border`          | `#E2E2E0`  | Default 1 px hairline                                   |
| Strong border           | `ve-border-strong`   | `#CACAC8`  | Hover / focus border                                    |
| Primary text (titles)   | `ve-text-primary`    | `#1A1A1A`  | Headlines, important values                             |
| Secondary text          | `ve-text-secondary`  | `#4A4A4A`  | Body                                                    |
| Muted text (labels)     | `ve-text-muted`/`-soft` | `#7A7A7A` | Secondary labels, helper copy                          |
| Ghost text              | `ve-text-ghost`      | `#B0B0B0`  | Placeholders, em-dashes for empty values                |

> `ve-charcoal` and `ve-charcoal-soft` exist for inherited reasons
> (legacy components). **Prefer `ve-text-primary` / `ve-text-muted` for
> new work.** Both reference the same neutral ink.

### 2.3 Status palette (always paired bg + border + text)

Status colors come as triads — **never use a status color in isolation**.
Always pair `*-bg` with `*-border` and `*-text` so the chip reads as a
deliberate token, not a stray hue.

| Status     | DEFAULT      | bg           | border       | text         | When                                                |
| ---------- | ------------ | ------------ | ------------ | ------------ | --------------------------------------------------- |
| Red        | `ve-red`     | `ve-red-bg`  | `ve-red-border` | `ve-red-text` | Destructive, overdue, errors                  |
| Amber      | `ve-amber`   | `ve-amber-bg`| `ve-amber-border`| `ve-amber-text`| Warnings, pending, low confidence            |
| Green      | `ve-green`   | `ve-green-bg`| `ve-green-border`| `ve-green-text`| Success, complete, signed                    |
| Blue       | `ve-blue`    | `ve-blue-bg` | `ve-blue-border` | `ve-blue-text`| Informational                                  |
| Purple     | `ve-purple`  | `ve-purple-bg`| `ve-purple-border`| `ve-purple-text`| Co-agent, vendor                            |
| Neutral    | `ve-neutral` | `ve-neutral-bg`| `ve-neutral-border`| `ve-neutral-text`| Other / inactive                          |
| AI accent  | —            | `ve-ai-bg`   | `ve-ai-border`| —            | "AI suggested" surfaces                             |

### 2.4 Forbidden

- **Raw hex literals in JSX.** Always use the `ve-*` token.
  Exception: `#C8322F` is allowed for the destructive button only because
  it was hard-coded in the deletion confirmation before tokens existed; in
  new code use `ve-red`.
- **Tailwind's default palette** (`text-blue-500`, `bg-emerald-50`).
  All UI must come from the `ve-*` namespace. The only acceptable Tailwind
  defaults are `bg-emerald-50/100/500/700` and `bg-amber-50/700` for
  confidence pills and the amber edge cases that pre-date the `ve-amber`
  triad — and only when matching an established pattern.
- **Dark mode.** The app is light-mode only. Don't add `dark:` variants
  unless explicitly directed.

---

## 3 · Typography

### 3.1 Type stack

| Family   | Tailwind     | Use                                                         |
| -------- | ------------ | ----------------------------------------------------------- |
| Sans     | `font-sans`  | Body, UI, buttons. **IBM Plex Sans.**                       |
| Serif    | `font-serif` | Hero headlines, premium titles, deal preview. **Lora.**     |
| Mono     | `font-mono`  | Tiny uppercase labels ("kickers"), tabular numerics. **IBM Plex Mono.** |

Body default is **13.5 px** (set on `<body>` in `index.css`); the size
scale is in `tailwind.config.js` under `theme.extend.fontSize`.

### 3.2 Hierarchy

Velvet Elves uses a **three-voice hierarchy**: serif for the protagonist,
sans for the body, mono for tiny labels. Never mix them on a single line
unless it's `<kicker><title>` (mono → serif).

```
✦ READY TO CREATE                         ← font-mono text-[9px] tracking-[1.8px] uppercase text-ve-orange
100 Main St                               ← font-serif text-[24px] tracking-[-0.005em] text-ve-text-primary
Denver, CO 80202                          ← text-[12.5px] text-ve-charcoal-soft
```

**Canonical sizes** (use exactly these — don't invent):

| Role                                   | Class                                                            |
| -------------------------------------- | ---------------------------------------------------------------- |
| Hero serif title                       | `font-serif text-[22px]–[26px] leading-[1.15] tracking-[-0.005em]` |
| Section serif title                    | `font-serif text-[16px]–[18px] font-semibold`                    |
| Body                                   | `text-[13px] leading-[1.55]`                                     |
| Card body / secondary                  | `text-[12.5px] leading-relaxed`                                  |
| Field label (form)                     | `text-[11.5px] font-medium tracking-wide text-ve-charcoal-soft`  |
| Mono kicker                            | `font-mono text-[9px] tracking-[1.8px] uppercase text-ve-charcoal-soft` |
| Tabular number (price, %)              | Add `tabular-nums`                                               |

### 3.3 Rules

- **One serif title per card.** Never two. The serif voice should feel
  rare and earned.
- **Mono is for ≤ 11 px text only.** Don't render full sentences in
  mono. Two- to four-word labels max.
- **Tracking.** Mono labels always use `tracking-[1.5px]` to
  `tracking-[1.8px]`. Serif titles tighten with `tracking-[-0.005em]`
  at 20 px+.
- **Never use `font-bold` on body copy.** Use `font-semibold`. `bold`
  reads as shouty in this typography.
- **Sentence case.** Buttons and titles are sentence case. ALL CAPS is
  reserved for mono kickers.

---

## 4 · Spacing & Layout

### 4.1 The 4 px grid

All margins, paddings, gaps must be a Tailwind step: `0.5` (2 px),
`1` (4), `1.5` (6), `2` (8), `2.5` (10), `3` (12), `4` (16), `5` (20),
`6` (24), `8` (32), `10` (40). **Never use arbitrary px values for
spacing.**

### 4.2 Card padding

| Card type                   | Padding                                |
| --------------------------- | -------------------------------------- |
| Tight inline card (party row, contingency row) | `p-3` (12 px)             |
| Default card body           | `p-5` (20 px)                          |
| Hero / featured card        | `p-6` (24 px)                          |
| Modal body                  | `px-6 pt-6 pb-5` (24/24/20)            |

### 4.3 Section rhythm

Vertical rhythm between sections inside a card body or page:
`space-y-4` (16 px) for content, `space-y-5` or `space-y-6` (20–24 px)
for major section breaks. Never use `mb-N` on individual elements to
fake spacing — let the parent's `space-y-N` carry it.

### 4.4 Container widths

| Container                 | Max width            |
| ------------------------- | -------------------- |
| Wizard right panel        | `max-w-2xl` (672 px) |
| Standard page content     | `max-w-3xl`–`max-w-5xl` |
| Modal dialog (alert)      | `max-w-[380px]`      |
| Modal dialog (form)       | `max-w-lg` (512 px)  |
| Wizard host modal         | `1040px`             |

---

## 5 · Borders, Radii, Shadows

### 5.1 Borders

| Use                                    | Width / class                            |
| -------------------------------------- | ---------------------------------------- |
| Default hairline                       | `border border-ve-border` (1 px)         |
| Form input default                     | `border-[1.5px] border-ve-border` (1.5 px) |
| Emphasized / branded card              | `border-[1.5px] border-ve-orange-border` |
| Dashed prompt / placeholder card       | `border-2 border-dashed border-ve-border` (or `-orange-border`) |

Don't use `border-2` for solid borders. The brand uses 1 px hairlines
or 1.5 px on form controls — stepping to 2 px solid reads as "loud".

### 5.2 Radii

| Element                       | Radius                                   |
| ----------------------------- | ---------------------------------------- |
| Inputs, selects, buttons      | `rounded-md` / `rounded-lg` (6–9 px)     |
| Inline pills                  | `rounded-full`                           |
| Cards                         | `rounded-xl` (12 px)                     |
| Hero cards / modals           | `rounded-2xl` (16 px) or `rounded-[14px]–[16px]` |
| Wizard host modal             | `rounded-[16px]–[18px]`                  |

Avoid `rounded-3xl`+ — too soft for a premium feel.

### 5.3 Shadows

Three approved shadow voices. Don't compose new ones.

```css
shadow-soft       /* 0 2px 8px rgba(20,20,20,.06) — quiet card lift   */
shadow-card       /* same as soft, semantic alias                     */
shadow-card-hover /* 0 4px 20px rgba(45,45,45,0.08) — hover state     */
shadow-premium    /* 0 12px 28px rgba(20,20,20,.12) — modals, premium */
```

For confirm-screen hero cards and dialogs, layered ambient shadows are
acceptable when written explicitly:

```css
shadow-[0_24px_60px_-16px_rgba(15,20,30,0.28),0_4px_18px_-4px_rgba(15,20,30,0.10)]
```

Never use `shadow-2xl` or stock Tailwind shadows — they don't match the brand.

---

## 6 · Components

### 6.1 Buttons

The shared `<Button>` lives at `src/components/ui/button.tsx`. Use its
variants — don't restyle from scratch.

| Variant       | When                                                                          |
| ------------- | ----------------------------------------------------------------------------- |
| `default`     | Primary action. Use the brand orange via `bg-ve-orange hover:bg-ve-orange-dark`. |
| `outline`     | Secondary action ("Add Party", "Edit"). Hairline `border-[1.5px] border-ve-border`. |
| `ghost`       | Tertiary inline (icon-only, "Continue manually", "Skip").                     |
| `destructive` | Destructive primary. The discard-dialog button uses `bg-ve-text-primary` (refined charcoal) instead of red — both are acceptable for destructive depending on context. |
| `link`        | Inline text-link only.                                                        |

**Sizing.** Size scale is `sm` (h-9), `default` (h-10), `lg` (h-11).
For our typography density, prefer `size="sm"` with `text-[11.5px]–[12.5px]`
explicit text-size overrides.

**Repeater buttons** (Add Party, Add Contingency) follow the
"section-header + bottom ghost-repeater" pattern. The bottom button is
`variant="ghost" size="sm"` with `text-[11.5px] font-semibold
text-ve-orange hover:bg-ve-orange-light hover:text-ve-orange-xdark`,
centered. No dashed mega-cards.

### 6.2 Inputs

```jsx
<Input className="border-[1.5px] border-ve-border rounded-lg px-3 py-2 text-[13px] text-ve-charcoal bg-white focus:border-ve-orange focus-visible:ring-ve-orange/30" />
```

This is the canonical "branded input class" used by the wizard.

**"Needs attention" treatment** for required-but-empty fields:

```jsx
// Subtle champagne wash on the input itself
className="... border-ve-orange/70 bg-ve-orange-soft/15"
```

Plus a 6 px champagne **dot** rendered before the label
(`<span className="inline-block h-1.5 w-1.5 rounded-full bg-ve-orange shadow-[0_0_0_2px_rgba(232,119,34,0.18)]" />`).
**Never** use a "Needs Attention" pill, an alert-triangle icon, or a
chunky left-edge box — those are explicitly rejected.

### 6.3 Cards

Two flavors:

```jsx
// Default content card
<div className="rounded-xl border border-ve-border bg-white shadow-[0_1px_4px_rgba(30,30,30,0.03)]">
  <div className="px-5 py-3 border-b border-ve-border flex items-center justify-between">
    <p className="font-mono text-[9px] tracking-[1.8px] uppercase text-ve-charcoal-soft">SECTION TITLE</p>
    <button>Edit</button>
  </div>
  <div className="p-5">{/* body */}</div>
</div>

// Featured / hero card
<div className="overflow-hidden rounded-2xl border border-ve-border bg-gradient-to-br from-white to-ve-orange-soft/15 shadow-[0_2px_14px_rgba(30,30,30,0.05)]">
  <div className="h-[3px] bg-gradient-to-r from-ve-orange via-ve-orange to-ve-orange/30" />
  <div className="p-6">{/* hero content */}</div>
</div>
```

### 6.4 Pills / chips

```jsx
// Status pill (paired bg + text)
<span className="rounded-full bg-ve-green-bg px-2.5 py-0.5 text-[11px] font-semibold text-ve-green-text">Complete</span>

// Soft chip (informational)
<span className="rounded-full border border-ve-border bg-white px-2.5 py-0.5 text-[11.5px] font-medium text-ve-charcoal">Cash</span>

// Brand chip
<span className="rounded-full bg-ve-orange-soft/55 px-2.5 py-0.5 text-[11.5px] font-semibold text-ve-orange-xdark">Representing Buyer</span>
```

### 6.5 Dialogs

Two dialog primitives in this app:

- **`<Dialog>`** (`@/components/ui/dialog.tsx`) — for forms.
- **`<AlertDialog>`** (`@/components/ui/alert-dialog.tsx`) — for
  confirm/destructive prompts. *Yes/No* style.

Both default to `z-50`. **When a dialog must appear over another modal**
(e.g. discard-confirm over the wizard at `z-[600]`), use the radix
primitive directly with explicit `z-[650]` overlay and `z-[660]` content
— see `NewTransactionModal.tsx` and `DocumentSplitDialog.tsx` for the
canonical pattern.

**Never use `window.confirm()`, `window.alert()`, or `window.prompt()`.**
They render Chrome's native dialog and break the brand.

**Discard / destructive dialog template** (canonical):

- Width: `max-w-[380px]`
- Border: 1 px hairline, `rounded-[14px]`
- Backdrop: `bg-[rgba(15,20,30,0.45)] backdrop-blur-[3px]`
- Layout: mono kicker → serif title (20 px) → body (13 px) → right-aligned button row
- Buttons: ghost cancel (`hover:bg-ve-bg`) + solid charcoal primary
  (`bg-ve-text-primary hover:bg-black`)
- No icon tile, no alert pill — type-led only

### 6.6 Stepper / progress indicators

Wizard left-rail stepper canonical sizes:

- Dot: `h-[26px] w-[26px] rounded-full`
- Active: `bg-ve-orange ring-4 ring-ve-orange/25`
- Completed: `bg-ve-orange/90`
- Not yet visited: `bg-white/8 text-white/55 border border-white/15`
- Connecting line: `absolute left-[13px] w-px` (line passes through dot center)
- Row: `flex w-full items-center gap-3 rounded-md px-2 py-1.5 -mx-2`
  with `hover:bg-white/[0.06]` — **always `w-full`** so hover regions are
  uniform regardless of label length.

---

## 7 · Iconography

- **Library:** `lucide-react`. No other icon set.
- **Sizes:** `h-3.5 w-3.5` for inline button icons. `h-4 w-4` for
  list-row icons. `h-5 w-5` for hero/sidebar icons. Never `h-6+` inside
  body content.
- **Color:** match the surrounding text color (`text-ve-orange`,
  `text-ve-charcoal-soft`, etc). Don't re-color icons mid-text.
- **Brand glyph:** the **✦ (asterism)** is the Velvet Elves brand
  icon; reserve it for kicker labels and brand surfaces. Don't sprinkle
  ✦ in body copy.

---

## 8 · Animation

Use only the keyframes defined in `tailwind.config.js`:
`animate-fade-in`, `animate-fade-in-up`, `animate-slide-in-right`,
`animate-scale-in`, `animate-shimmer`, `animate-float`,
`animate-search-focus`.

For dialog/modal opens, use Radix's data-state animations:
`data-[state=open]:animate-in data-[state=closed]:animate-out`
combined with `fade-in-0` and `zoom-in-[0.97]`.

**Never use bouncy / spring / overshoot easing.** The brand is calm.
Default to `ease-out` over 200–300 ms.

---

## 9 · Forms

### 9.1 Field anatomy

Always use the `<FieldGroup>` wrapper from `NewTransactionWizard.tsx`
or replicate its structure:

```
[label + asterisk + (optional needsAttention dot)]
[input]
[optional inline help text]
```

- Required indicator: `<span className="ml-0.5 text-ve-orange">*</span>`
- Help text: `text-[11.5px] text-ve-charcoal-soft/75`

### 9.2 Validation feedback

- Live-validate on **blur** (or on submit), never on every keystroke.
- Surface required-but-empty fields with the **champagne dot + soft input wash**
  pattern (§ 6.2). Don't pop a red error message until the user has
  attempted submit.
- Inline errors: `text-[11.5px] text-ve-red-text mt-1`.

### 9.3 Selects, datepickers, money inputs

- Selects: use `<Select>` from `@/components/ui/select` (Radix-based).
  Canonical trigger styling is the same `brandedInputClass` as `<Input>`.
  **Never use a native `<select>`.** Native selects look archaic, don't
  match brand input styling, and break visual consistency with every
  other dropdown in the project. For filter-chip style triggers (e.g.
  the Audit Log filters), override the trigger with `h-9 rounded-full`
  and a `min-w-[160px]` so it reads as a chip, not a boxy form input.
- Date inputs: native `type="date"`. Use the `min`/`max` HTML
  attributes for constraints (e.g., contract acceptance has
  `max={todayIso}`).
- Money inputs: use the `<MoneyInput>` helper in
  `NewTransactionWizard.tsx` — `$` prefix + comma formatting + numeric
  internal value.

### 9.4 Repeater patterns (lists you can grow)

When a section can have N items (parties, contingencies, contacts):

1. Section-header **outline** "Add X" button (entry point on first sight).
2. Inline **ghost** "Add Another X" button below the list (so users
   don't scroll back up). Centered, `text-[11.5px] font-semibold
   text-ve-orange`.
3. After adding: scroll the new card into view and focus its first
   input.

---

## 10 · AI-Adjacent UI

The "AI handled this" indication uses one accent color: champagne
(`ve-orange*`).

- AI-filled banner copy (canonical):
  > "Fields that still need your attention are highlighted below.
  > Everything else was filled by AI — please verify before continuing."
- AI extraction in progress: `<Sparkles className="text-ve-orange animate-pulse" />`
- AI confidence badges (file rows): green ≥ 80, amber ≥ 50, rose otherwise.
  These are the only places where Tailwind's `emerald-50/700` / `amber-50/700`
  / `red-50/700` defaults are accepted (they pair more cleanly with file-row
  density than the `ve-green-bg`/`ve-green-text` triad).
- The "✦" mark in `✦ AI Assistant` / `✦ New Transaction` etc. is a
  brand cue, not a pure AI signal.

---

## 11 · Empty States

Empty states are **explanatory, not apologetic**. One sentence, no
"oops". Optional small inline action.

```jsx
<div className="rounded-xl border-[1.5px] border-dashed border-ve-orange-border bg-ve-orange-soft/15 px-4 py-3">
  <p className="text-[12px] text-ve-charcoal-soft">
    Add at least one party — typically the buyer or seller you're representing.
  </p>
</div>
```

Don't dramatize empty states with illustrations or emoji.

**Charts always have an empty state.** A chart whose data is empty must
render an explicit dashed empty-state card with explanatory copy ("No
closed transactions yet — the chart will fill in as deals close"), *not*
a blank or broken-looking SVG. A reader must be able to tell that the
chart is intentionally empty, not broken. See § 16.6.

---

## 12 · Accessibility

- **Color contrast:** every `*-text` token on its paired `*-bg` token
  meets WCAG AA. Don't pair `ve-text-muted` with `ve-orange-soft` —
  ratio drops below 4.5:1.
- **Focus rings:** keep the default Tailwind `focus-visible:ring-2
  focus-visible:ring-ring focus-visible:ring-offset-2` (which resolves
  to a champagne ring via `--ring`). Don't suppress with `outline-none`
  alone.
- **Hit targets:** interactive controls inside lists ≥ 32 × 32 px;
  primary buttons ≥ 36 × 36 px. Touch targets on standalone elements
  use the `.touch-target-lg` utility (44 × 44 minimum).
- **Aria:** every icon-only button needs `aria-label`. Dialogs need
  a `Title` and `Description`.
- **Keyboard:** Escape closes modals. Enter submits primary forms.
  Tab order follows visual order.

---

## 13 · Anti-Patterns (Hard Don'ts)

These have been explicitly rejected by the client. Don't reintroduce:

1. **Heavy field highlights** — no `ring-2 ring-offset` boxes,
   no chunky champagne backgrounds, no "NEEDS ATTENTION" pills with
   alert-triangle icons. Use the dot + soft input wash.
2. **Oversized empty-state cards** — no full-width dashed mega-cards
   with hero CTAs for in-list "Add another". Use the small ghost button
   pattern.
3. **`window.confirm()` / `window.alert()` / `window.prompt()`** —
   replace with `<AlertDialog>`.
4. **Square icon tiles in dialogs** — type-led only.
5. **Bright destructive red as a dialog primary** — prefer the refined
   charcoal (`bg-ve-text-primary`) for the discard pattern; reserve
   `ve-red` for the delete-transaction case.
6. **Inconsistent hover regions in lists/sidebars** — every clickable
   row in a list uses `w-full`, so longer labels don't produce wider
   hover swatches.
7. **AI-extracted vs manual badge differentiation** — once data is in
   a card, it doesn't matter where it came from. Don't visually
   differentiate by source.
8. **Mixed type voices in one heading** — kicker (mono) + title (serif)
   is allowed; serif + sans on the same line is not.
9. **Tailwind default colors** for new UI (`bg-blue-500`,
   `text-emerald-500`). Use the `ve-*` namespace.
10. **`shadow-2xl`, `shadow-3xl`** — use the named `shadow-soft / -card
    / -card-hover / -premium` tokens.
11. **Dropdown options that aren't there.** If a select promises Buyer /
    Seller / Both, all three must be in the menu. Half-wired dropdowns
    are a recurring bug class.
12. **Forgetting "Capitalize Each Word" rules** on user-facing labels.
    Field titles use Title Case ("Contract Acceptance Date"), not
    sentence case.
13. **`max-w-[N]` containers on internal pages.** Internal pages fill
    the gutter (`px-3 md:px-6`, no inner `max-w`). The exceptions are
    listed in § 15.3 (wizard right panel; narrow form columns). A
    dashboard centered inside `max-w-[1400px]` is a wasted-margin
    failure — the user sees empty space on both sides on wide displays.
14. **Top bars on dashboards.** Dashboards open with data, not chrome
    (§ 16.1). The breadcrumb / page-title bar is for list / settings /
    admin sub-pages — not for `/dashboard/*` routes. No greeting, no
    "Customize" button, no primary CTA that duplicates the sidebar.
15. **Native `<select>` elements.** Always use `<Select>` from
    `@/components/ui/select` (Radix-based). A native `<select>` looks
    archaic and breaks visual consistency with every other dropdown in
    the project. (See § 9.3.)
16. **Multiple card shapes on one dashboard.** Every block — section
    card, rail card, chart sub-card, KPI card — must share one card
    vocabulary (§ 16.2). Variation in importance is expressed through
    `tone`/`density` props, *never* through ad-hoc rounding, shadows,
    gradient strips, or border weights. Bespoke "hero" cards next to
    plain section cards next to differently-shaped rail cards read as a
    hodgepodge.
17. **Monotone dashboards.** A dashboard whose every card is the same
    neutral grey provides no hierarchy and fails its at-a-glance job.
    Mix at least one brand-toned hero, a tone-tinted KPI or two, and
    severity-colored action-queue items (§ 16.3). The inverse failure
    is drowning the page in champagne — reserve `ve-orange` for moments
    that matter.

---

## 14 · Naming Conventions

- Component file: `PascalCase.tsx` (`NewTransactionWizard.tsx`).
- Helper file: `camelCase.ts` (`wizardTypes.ts`).
- Test file: mirror with `.test.tsx`.
- Tailwind class strings: alphabetize within `cn()` calls only when
  it improves readability — order by *role*, not alphabet
  (layout → spacing → color → state).
- CSS custom properties: `--ve-*` (matching `ve-*` Tailwind tokens).

---

## 15 · Page Shells

The product's pages must feel like surfaces of one app — same gutter,
same header anatomy, same scroll behavior. These rules apply to *every*
internal page; dashboards have an additional set in § 16.

### 15.1 The canonical shell

Every internal page uses the same shell. Don't invent variations.

```jsx
<div className="flex h-full min-h-0 flex-col overflow-hidden bg-ve-bg">
  {/* Optional sticky header per § 15.2. Dashboards omit it — see § 16.1. */}
  <header className="flex-shrink-0 border-b-[1.5px] border-ve-border bg-white px-3 md:px-6 pt-3 pb-0">
    …
  </header>
  {/* Scroll body */}
  <div className="flex-1 min-h-0 overflow-y-auto bg-ve-bg px-3 md:px-6 pt-4 pb-12">
    …
  </div>
</div>
```

Side gutter is **`px-3 md:px-6` project-wide**. Communication Audit,
Audit Log, AI Governance, the Admin Dashboard, the transaction lists,
and the FSBO portal all use it. Never widen it without an explicit
revision to this guide.

### 15.2 Header / breadcrumb pattern

Internal pages that have a header (list, settings, audit, governance,
admin sub-pages) share one anatomy:

| Slot | Style |
| --- | --- |
| Breadcrumb row (above the title) | `text-[11.5px]`: parent crumb + icon, `›` separator (`text-ve-charcoal-ghost`), current page in `text-ve-text-muted font-medium`. |
| Title | `font-serif text-[16px] md:text-[20px] text-ve-text-primary`. |
| Inline badge | A pill chip *next to the title* — counts, status, etc. (e.g. `342 entries`). |
| Optional tab strip | Below the title row, with `border-t-[1.5px] border-ve-border -mx-3 md:-mx-6 px-3 md:px-6` so the rule bleeds to the page gutter (per `CommunicationAuditPage`). |

Admin sub-pages use the shared `AdminPageHeader` component
(`src/components/admin/AdminPageHeader.tsx`); other pages compose the
same anatomy inline. **Every page in a group must share the same header
style** so the group reads as one product surface — e.g. Communication
Audit, Audit Log, and AI Governance all share the breadcrumb-and-serif
header pattern, with the "Admin" crumb linking back to the admin
dashboard.

### 15.3 Container width — no `max-w` on internal pages

Internal pages do **not** wrap content in `max-w-*` containers. Content
fills the gutter; grids expand naturally. Exceptions:

- Wizard right panel: `max-w-2xl` (per § 4.4).
- Standard form / settings pages may use `max-w-3xl`–`max-w-5xl` *only*
  when narrowing the reading column genuinely improves form
  readability. Even then, the outer gutter is still `px-3 md:px-6`.

When a settings page has *multiple* control rows (e.g. two sliders
side-by-side), drop the `max-w` and lay the controls out in a
`grid-cols-1 md:grid-cols-2` grid so the horizontal space is used
intentionally — not absorbed by margins.

The anti-pattern: a dashboard centered inside `max-w-[1400px]` on a
wide display. The reader sees a strip of content with hundreds of
pixels of dead space on each side. (See § 13, item 13.)

---

## 16 · Dashboard Design

Dashboards are the surfaces where information density and visual
hierarchy matter most. Their primary job is **at-a-glance
comprehension**: the reader sees the most important numbers, the most
important action, and the most important risks without scrolling or
parsing labels. The brand voice is still calm (§ 1) and the palette is
still restrained (§ 2), but a dashboard's *contrast* must be decisive.

These rules govern the admin dashboard explicitly; role dashboards
(Solo Agent, Team Leader, Attorney, FSBO) follow the same principles
through the shared kit (`@/components/dashboard/shared`).

### 16.1 What a dashboard is — and isn't

A dashboard is **data**, not chrome. The page identity comes from the
sidebar route + the data on the page, not from a sticky header.

Dashboards **must not** have:

- A sticky **top bar** with greeting, breadcrumb, or page descriptor
  chrome. (Other internal pages do — dashboards do not.)
- A **"Customize" / "Edit layout"** button on the page itself. Drawer-
  style layout reordering belongs in user settings, not the dashboard.
- A primary CTA that **duplicates the sidebar primary CTA**
  ("Invite user", "+ New Transaction"). The shell already exposes one
  primary action; the dashboard must not echo it.
- A separate **page-title row** above the first row of content.

Dashboards **do** have:

- A KPI strip as the first row of content (§ 16.4).
- A main column of section cards + a right rail of compact cards via
  `MainRailGrid` from `@/components/dashboard/shared`.
- A `FloatingAskAi` widget — floating bottom-right is not chrome.
- The shell from § 15.1 (`px-3 md:px-6`, no `max-w`).

### 16.2 One card vocabulary per dashboard

A dashboard must use **one** card shell across every block — main-
column sections, rail cards, chart sub-cards, KPI cards. Different
card shapes for "this is a section card" vs. "this is a rail card"
vs. "this is a chart card" is a hodgepodge and a documented anti-
pattern (§ 13, item 16).

For the admin dashboard, that vocabulary is:

- **`AdminCard`** (`src/components/dashboard/admin/AdminCard.tsx`) —
  every section block and every rail card. Standardises:
  - Outer chrome: `rounded-xl border border-ve-border bg-white shadow-card`.
  - Header anatomy: **icon tile → mono kicker → serif title → optional
    description** on the left; `action` / `trailing` slots on the right.
  - Two density modes: `default` (main column) and `compact` (rail /
    chart sub-card).
  - Tone via prop: `tone='brand'` colors the icon tile and eyebrow
    champagne; `tone='neutral'` keeps them muted.
  - Body tint via prop: `bodyTint='soft'` applies a `ve-surface-2/40`
    overlay so list / grid contents lift off the card.
- **`AdminStat`** (`src/components/dashboard/admin/AdminStat.tsx`) —
  every "small number in a tinted container": same border, padding,
  mono kicker, 22 px serif value. Tone varies; shape never does.
- **`AdminKpiCard`** — KPI strip. Shares `AdminCard`'s outer chrome
  *exactly*; differs only in the body (icon tile + serif headline
  value).

Role dashboards use the shared kit's `SectionCard` + `RailCard` for the
same reason — pick one card type per dashboard and stick with it.

**Variation is expressed through props (tone, density), not through
ad-hoc styling.** When a hero block needs more visual presence, use
`tone='brand'` + `bodyTint='soft'` + a trailing-slot badge strip — not
a one-off `rounded-2xl` card with a custom gradient strip.

### 16.3 Emphasis & color contrast

A dashboard where every card is the same neutral grey has failed its
primary job. A dashboard where every card screams champagne has also
failed it. Aim for:

- **~1 brand-toned section per page** (the priority / hero block) —
  gets `tone='brand'`.
- **1–2 tone-tinted KPI cards** (e.g. green for pipeline-volume money,
  amber when something needs attention). Four neutral KPIs = monotone
  failure.
- **Tone variation on action-queue severities** — red rail for critical,
  amber for high, blue for review, neutral for FYI (§ 16.5).
- **Neutral for everything else** — most cards are `tone='neutral'`,
  and that's correct.

Within the `ve-*` palette:

| Color | Where to use it on a dashboard |
| --- | --- |
| Champagne (`ve-orange*`) | AI surfaces, brand / priority emphasis, primary CTAs. Don't waste it on decoration. |
| Status triads (red / amber / green / blue) | Paired bg + border + text only (§ 2.3). Severity rails, status pills, tone-tinted stats. Never in isolation. |
| Neutral (`ve-surface-2`, `ve-text-ghost`) | The dashboard body. Most cards are neutral. |

### 16.4 The KPI strip

Most dashboards open with a 4-card KPI strip as the first row of
content (above everything else — there is no header on a dashboard, per
§ 16.1).

- `grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 md:gap-4`.
- Each card: **tinted circular icon tile** (~40 px) on the left, then
  mono kicker label + serif headline value (28–32 px) + optional muted
  hint underneath.
- Cards are **clickable** and deep-link to filtered views — KPIs are
  the dashboard's primary navigation, not decoration.
- **At least two different tones** across the four cards. Four neutral
  KPIs = monotone failure (§ 16.3).
- Outer chrome must match every other card on the page (§ 16.2) — the
  KPI strip is part of the family, not a separate widget.

### 16.5 Action queue / priority list

The "Needs your attention" pattern carries the strongest hierarchy on
a dashboard. Anatomy:

- Parent card uses `bodyTint='soft'` so items pop off the card.
- Each item is a card-shaped row with:
  - **4 px severity rail** down the left edge — `ve-red` (critical),
    `ve-amber` (high), `ve-blue` (review), `ve-neutral` (FYI).
  - **Tinted icon tile** (~44 px rounded square, `ring-1 ring-inset`,
    color matched to severity). The icon is chosen by category
    (AI → `Sparkles`, Access → `Users`, Pipeline → `Briefcase`,
    Security → `ShieldAlert`).
  - **Severity pill + category badge** inline above the title, both
    paired bg / border / text triads per § 2.3.
  - **15–17 px serif title** + muted "why" line below.
  - **Filled brand-orange primary button** for the action — never an
    outline button for the primary action on an action item.
  - Lift-on-hover (`-translate-y-[1px]` + `shadow-card-hover`).
- **One explicit action button per item.** Never make the whole card
  the click target — this is the alert-card clickability rule
  (`feedback_alert_card_clickability`). If a card needs parallel
  actions, render multiple explicit buttons. Clicking different
  regions to produce different behaviors is forbidden.

### 16.6 Trend / chart grid

A "trends" section is a grid of N equal-height chart cards inside a
parent `AdminCard`:

- Parent: `AdminCard` with `bodyTint='soft'` so the inner white
  sub-cards lift off the tint.
- Sub-cards: **the same** `AdminCard compact` shell as rail cards
  (icon tile + kicker + title + description, `trailing` slot for the
  headline stat) — not a bespoke chart panel.
- **Fixed-height chart frame** (e.g. 180 px) inside every sub-card so
  the row stays aligned at every breakpoint.
- **Explicit empty state** when data is empty — a dashed empty-state
  card with explanatory copy. A chart must never render a blank or
  broken-looking SVG (per § 11).

### 16.7 Right rail composition

The rail is a vertical stack of `AdminCard compact` cards. Each gets:

- The same **icon-tile-in-header** pattern as main-column cards.
- Compact density (`px-4 py-3` header, `p-4` body).
- Smaller serif title (~14 px) so the rail reads as secondary.

Rail cards must not look like a different visual species from main
column cards — the only difference is density.

### 16.8 Dashboard-adjacent admin pages

Pages that the dashboard deep-links to (AI Governance, Audit Log,
Communication Audit) are **not** dashboards — they get the standard
page shell from § 15 with the breadcrumb header, and they share the
same header anatomy across the whole admin group. AI configuration
that admins reach from the dashboard's "Tune thresholds →" link lives
on the AI Governance page, not in tenant Settings — keep AI admin
decisions on one surface so the cognitive model stays intact.

---

## 17 · When in Doubt

1. **Find the closest existing pattern** — the wizard, the
   `TransactionListPage`, the `HistoryPanel`. Copy it.
2. **Ask the user** before inventing a new color, a new shadow, a
   new dialog shape, or a new repeater layout.
3. **Reread §13 (Anti-Patterns).** The most common mistake is
   reintroducing one of those.
4. **Test in the wizard modal context.** Many bugs come from
   z-index, drag handlers, or hover regions only manifesting inside the
   wizard's nested layout.

---

*Last revised: 2026-05-20 (rev 2 — added § 15 Page Shells and § 16
Dashboard Design; extended § 13 Anti-Patterns with items 13–17;
strengthened § 9.3 and § 11 with explicit rules on selects and chart
empty states). Treat this document as the spec; if you disagree with
a rule, propose a revision before you ship around it.*
