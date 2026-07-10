# AI Wizard: Non-Functional UI & Incomplete-Feature Audit

**Date:** 2026-07-09
**Author:** Jan
**Scope:** The New Transaction "AI Wizard" (`velvet-elves-frontend/src/components/wizard/*`, the `useWizardApi` hooks, and the backend AI endpoints they call).
**Goal:** Find every element that is hard-coded, half-implemented, or a UI placeholder with no working behavior behind it, and give a concrete fix for each so nothing in the wizard misleads a user.

---

## Executive summary

I walked the wizard end to end, step by step (Upload -> Parsing -> Address & Contacts -> Purchase Info -> Missing Info -> Confirm -> Documents/Checklist -> Create), then traced every button and AI affordance down to the backend endpoint that serves it.

**The headline is good:** the wizard is, with two exceptions, fully implemented. Document upload, the two-pass AI extraction, the double-check panel, the Intake-Intelligence proposals (timeline/checklist/tasks/watchouts), the natural-language command bar, the evidence viewer with OCR-anchored highlighting, the compliance checklist, task generation at commit, the FSBO invite, e-signature gating, Stripe payment, and cross-device drafts are all real and wired to working endpoints.

**Two user-facing problems are real and should be fixed:**

| # | Issue | Severity | Type |
|---|-------|----------|------|
| **F1** | The **"AI Search"** button on the Missing Info step calls a backend method that is a deliberate stub and **always returns zero results**. | **High** | UI placeholder with no working backend |
| **F2** | **Address autocomplete** is hard-disabled by a `const` flag, and no API key is provisioned. The Street Address field still presents itself as a live autocomplete (combobox, "Start typing..." placeholder) but does nothing for a new user. | **Medium** | Feature built then flagged off; misleading affordance |

**Two lower-priority cleanups** (no user impact today, but they are dead/duplicated code that will confuse the next person in the file):

| # | Issue | Severity | Type |
|---|-------|----------|------|
| **F3** | `renderTimeline` / `renderReview` and their large child components (`WizardTimelineStep`, `ReviewTasksStep`) are **unreachable dead code** after the flow was folded down to 3 phases. | **Low** | Dead code / incomplete migration |
| **F4** | The Parsing screen shows a **static 4-item "phases" list** as a fallback when the backend has not yet streamed progress. Cosmetic only. | **Info** | Hard-coded fallback content |

The rest of this document details each finding with exact locations, evidence, user impact, and the fix I recommend.

---

## F1 — "AI Search" (public-source lookup) never returns anything

### Severity: High. This is the clearest "placeholder that looks functional."

### Where the user sees it
- **Step:** Missing Info (`renderMissing`, `NewTransactionWizard.tsx:6968`).
- The step tells the user, verbatim: *"You can type a value or let AI search public sources."* (`NewTransactionWizard.tsx:7012-7016`).
- Every missing field that is **not** a fixed-choice decision renders through `MissingFieldRow` (`NewTransactionWizard.tsx:9706`), which shows a prominent amber **"AI Search"** button (`NewTransactionWizard.tsx:9772-9786`).
- Which fields get the button: from `detectMissingFields` (`wizardTypes.ts:1165`), everything except `title_ordered_by` and `has_appraisal` (the only two routed to one-click choice rows). So a blank ZIP, purchase price, acceptance/closing date, inspection/HOA days, and even a missing buyer/seller name all render an "AI Search" button.

### What actually happens
`runSearch` (`NewTransactionWizard.tsx:9721-9752`) calls the `useAiPublicSearch` hook (`useWizardApi.ts:247-260`) -> `POST /api/v1/ai/search-public-source`.

The endpoint (`backend/app/api/v1/ai.py:1585-1640`) calls `AIService.search_public_source` (`backend/app/services/ai_service.py:87-118`), whose own docstring states the truth:

> *"Until a real search provider is wired in, this returns an empty list so the wizard UI can fall back to manual entry."*

It delegates to `getattr(self._provider, "search_public_source", None)` **only if the provider implements it**. I grepped every provider (`backend/app/services/providers/*.py`): **none of them implement `search_public_source`.** So the method always falls through to `return []`.

The endpoint then dutifully returns `results: []`, and the UI shows the honest-but-pointless message: *"AI Search finished, but no public-source match was found."* (`NewTransactionWizard.tsx:9738-9741`).

### Impact
Every time a user clicks the most AI-flavored button in the wizard, on the step whose entire purpose is "let AI help fill gaps," it spins and returns nothing. On a first impression this reads as "the AI is broken," which is the opposite of the message the wizard is trying to send. It is the single most misleading affordance in the feature.

### Fix options

**Option A (recommended, short-term): remove the affordance so the UI is honest.**
- Delete the "AI Search" button and the search-results / search-message block from `MissingFieldRow`.
- Change the Missing Info intro copy (`NewTransactionWizard.tsx:7012-7016`) from *"type a value or let AI search public sources"* to *"Enter the remaining details below."*
- Keep manual entry (which works perfectly) and the one-click choice rows.
- Small, safe, and removes the false promise today. The endpoint/hook can stay in place for when a real provider lands.

**Option B (long-term, the real feature): wire a web-search-capable provider tool.**
- Anthropic's Messages API supports a server-side `web_search` tool, and OpenAI has an equivalent. Implement `search_public_source(field, context)` on `AnthropicProvider` / `OpenAIProvider` in `backend/app/services/providers/`, prompt it to return `[{value, source_label, source_url, confidence}]` grounded in a real citation, and keep the existing "AI-sourced, requires confirmation" UI (which is already built and correct).
- This is a genuine build (provider method + prompt + parsing + guardrails + cost metering), not a config flip. Worth scoping as its own task if the public-source lookup is a feature we actually want to ship.

**My recommendation:** ship Option A now so nothing lies to the user, and track Option B as a separate feature if/when we want the capability.

---

## F2 — Address autocomplete is disabled, but the field still advertises it

### Severity: Medium.

### Where the user sees it
- **Step:** Address & Contacts (`renderAddress`, `NewTransactionWizard.tsx:5659`).
- The Street Address input (`NewTransactionWizard.tsx:5692-5740`) is marked up as a live autocomplete: `role="combobox"`, `aria-autocomplete="list"`, `aria-expanded`, and the placeholder *"Start typing the property street address..."*, with a dropdown list wired for keyboard navigation.

### What actually happens
The whole Google Places integration is gated behind a hard-coded constant:

```ts
// NewTransactionWizard.tsx:557
const ADDRESS_AUTOCOMPLETE_ENABLED: boolean = false
```

The comment above it (`:548-556`) explains why: the live key was being rejected by Google (Places API not enabled / referrer restrictions), and the error was surfacing inside the field. So the effect at `:3064-3072` early-returns before ever calling Google.

Compounding it: `VITE_GOOGLE_MAPS_API_KEY` is **empty** in both `.env` and `.env.example`, so even flipping the flag would not work without provisioning a valid key.

With Google off, the dropdown is fed only by "recent addresses" pulled from the user's own prior transactions (`NewTransactionWizard.tsx:3040-3062`). For a **brand-new user or tenant with no transactions yet, the recents list is empty**, so the combobox opens to nothing and appears completely dead, despite presenting itself as a search box.

The full Places implementation (`loadGooglePlacesApi`, `getPlacePredictions`, `hydrateGoogleAddress`, `parseGooglePlaceAddress`) is present and correct. It is only switched off.

### Impact
Lower than F1 because the field still works as a plain text input and the four address sub-fields (city/state/zip/county) are all manually editable. But the "Start typing..." combobox sets an expectation of live address search that is not met, especially for the first-run experience where recents are empty.

### Fix options

**Option A (recommended if we want the feature): provision the key and turn it on.**
1. Create/repair a Google Maps key with the **Places API enabled** and HTTP-referrer restrictions that include the app's real domains (dev, staging, prod).
2. Put it in `VITE_GOOGLE_MAPS_API_KEY` across the frontend env files.
3. Flip `ADDRESS_AUTOCOMPLETE_ENABLED` to `true` and verify predictions resolve in each environment.
The existing error-handling (`humanizePlacesStatus`, the inline dropdown error rows) already covers the failure modes cleanly.

**Option B (if we are not provisioning a key soon): stop advertising autocomplete.**
- When `ADDRESS_AUTOCOMPLETE_ENABLED` is false, drop `role="combobox"` / `aria-autocomplete` and change the placeholder to a plain *"Property street address"*, so the field does not imply a search it cannot perform.
- Keep the recent-address dropdown, but only render the combobox affordances when there is actually at least one recent suggestion to show.

**My recommendation:** Option A if address autocomplete is a feature we care about (it is a nice quality-of-life win and the code is already written). Otherwise Option B so the field is honest. Either way, the current in-between state (built, flagged off, still dressed as a live search) should not stay.

---

## F3 — Orphaned step renderers and their child components (dead code)

### Severity: Low. No user impact today; it is a cleanup / incomplete-migration item.

### Detail
The flow was folded from its original step list down to three phases. `WIZARD_STEPS` now excludes `parsing`, `timeline`, and `review` (`wizardTypes.ts:56-63`); Timeline folded into Confirm, and the Tasks-review step folded into Documents.

But the renderers and their large children still exist and are still referenced in `stepRender` (`NewTransactionWizard.tsx:8158-8168`):
- `renderTimeline` (`:8003`) -> `WizardTimelineStep` (755 lines)
- `renderReview` (`:7601`) -> `ReviewTasksStep` (885 lines), which itself hosts the "Ask AI for supplemental tasks" feature (`usePreviewAiSuggestions`).

Navigation can never reach `timeline` or `review`: `next_step`/`prev_step` walk `WIZARD_STEPS`, the stepper's `allowedStepsForJump` filters to `WIZARD_STEPS`, and a restored draft is coerced back onto a navigable step by `coerceNavigableStep` (`NewTransactionWizard.tsx:1437-1440`, called from the `restore_state` reducer at `:1843-1849`). So these two renderers plus roughly 1,600 lines of component code are unreachable.

### Why it matters
It is not a bug a user hits, but it is a real trap for whoever edits this file next: two full step implementations that look active (they are in the `stepRender` map) but are dead. The `ReviewTasksStep` in particular represents a per-task preview/exclude/edit surface, and an AI supplemental-task suggester, that are **no longer exposed anywhere in the wizard**. If we intended to drop per-task editing from the wizard, the code should go; if we intended to keep it, it needs a route back in.

### Fix
Decide intent, then either:
- **Remove:** delete `renderTimeline`, `renderReview`, their entries in `stepRender`, and the now-unused `WizardTimelineStep` / `ReviewTasksStep` (and prune any imports/props that only fed them), OR
- **Re-expose:** if the task-preview surface is wanted, add it back as a real navigable step.

I lean toward removal, since Audri's feedback explicitly folded these away ("create happens straight from Documents; the full plan still generates at commit"). Removal also shrinks a 10.5k-line file.

---

## F4 — Parsing screen's static "phases" fallback

### Severity: Info. Cosmetic; documenting for completeness.

`renderParsing` (`NewTransactionWizard.tsx:5528-5534`) defines a hard-coded four-item list ("Reading documents", "Extracting property data", "Identifying parties", "Checking dates") that is shown **only** when the backend has not yet streamed any real progress events. Once `parseProgress` starts filling (via the `onProgress` callback threaded through `useParseDocumentPacket`, `useWizardApi.ts:157-200`, fed by the backend's `_report` stage events), the real stage-by-stage feed replaces it.

This is a reasonable graceful fallback, not a fake. The only risk is that if the backend ever stops emitting progress events, the user would sit on a static list of four "in progress" rows with no motion until the parse resolves. No change required; noted so it is not mistaken for a live feed in future reviews.

---

## Areas I verified as fully functional (so the review is on record as thorough)

- **Upload step** (`renderUpload`, `:5218`): representation gate, drag/drop, file input, per-file status, split affordance, manual-entry escape hatch. All real.
- **Parsing pipeline** (`runParsing`, `:3653`): two-pass extraction, double-check, citation building, signature-status capture, multi-doc resolver, Autopilot eligibility. Backend `document_packet_parsing.py` and `intake_intelligence.py` are real implementations.
- **Purchase step** (`renderPurchase`, `:6120`): every field, the days<->date sync for contingencies, cash-appraisal election, FSBO block, custom contingencies, pinned note. All wired to state.
- **Missing Info choice rows** (`MissingChoiceRow`): the one-click title/appraisal decisions work (only the free-text "AI Search" path is the F1 stub).
- **Confirm step** (`renderConfirm`, `:7066`): review tables with per-value source jumps, packet-level confidence (the old "85% on every doc" bug is fixed), AI-found-deadline proposals with accept/dismiss, Autopilot hub, `AdSlot` (collapses cleanly when no ad).
- **Command bar** (`WizardCommandBar`): real LLM intent classification (`POST /ai/wizard-command` -> `parse_wizard_command`, `ai_service.py:688`), deterministic preview-apply-undo.
- **Checklist/Documents step** (`WizardChecklistStep`): preview == commit planner, supporting-doc upload, requirement matching, waive/restore.
- **Submit** (`submit`, `:3921`): transaction create, party persistence, FSBO invite (`POST /invitations/`), doc linking, bulk requirement commit, conditional e-sign send, task generation. Thorough and defensively coded.
- **Supporting panels:** `WizardDoubleCheckPanel`, `WizardSignaturePanel` (e-sign-provider gated), `WizardMissingDocsPanel`, `WizardDealBrief`, `WizardEvidenceViewer` (OCR-geometry highlight + document search). All real.
- **Infra:** credit/paywall badge, Stripe return handling, server + local drafts, confidence settings (`/confidence/`). All real.

---

## Recommended order of work

1. **F1 (High):** apply Option A (remove the non-working "AI Search" affordance and fix the intro copy). ~30 minutes, removes the worst false promise.
2. **F2 (Medium):** decide provision-vs-honest. If provisioning the Google key is quick, do Option A; otherwise apply Option B so the field stops advertising autocomplete.
3. **F3 (Low):** remove the orphaned `timeline`/`review` renderers and their dead child components once we confirm the fold-down is permanent.
4. **F4 (Info):** no action; keep for reference.

Items 1 and 3 are safe, self-contained frontend changes. Item 2 has an ops dependency (the Google key) for its recommended path. None of them touch the extraction/commit core, so the risk surface is small.

I can implement F1 and F3 immediately on your go-ahead, and either provision path for F2.
