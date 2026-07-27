# AI Wizard - Round 2 Clear Items: Implementation Plan

> The obvious, unquestionable items from Audri's second round of answers, planned
> against the current source. Items that still depend on an open real-estate
> question (see AI_WIZARD_FOLLOWUP_QUESTIONS_ROUND_2.md) are excluded and listed
> in section 2.2.
>
> Status: IMPLEMENTED 2026-07-23 (Items A, B, C). Revised across three
> workflow-and-logic review passes plus one build pass (R1-R12, section 1.4);
> Item A's force-seeding was dropped during build (R12). Item D remains deferred
> (section 6). Where a document and the source disagreed, the source won.
> Verification: typecheck + lint clean; 70 wizard-flow integration tests, the
> contact-fill / document-name / PDF-viewer / ocr-highlight unit suites, and the
> touched backend suites all pass. The live 10-PDF Chrome pass is still pending
> (needs the backend running; run with the AI model set to OpenAI gpt-5.4).

---

## 1. Grounding

### 1.1 Documents reviewed (velvet-elves-data)

| Document | What this plan takes from it |
| --- | --- |
| AI_WIZARD_QUESTIONS_FOR_AUDRI.md + Audri's answers | The six answers this plan acts on |
| AI_WIZARD_FOLLOWUP_QUESTIONS_ROUND_2.md | The five still-open real-estate questions, which gate the items in 2.2 |
| requirements.txt (1.5 Agent/Team Profiles, 1.6 Onboarding) | Profile is the source of truth for the user's own details; "after the first transaction upload, prompt the user to complete their profile if required fields are missing" |
| STYLE_GUIDE.md | Branded inputs, champagne accents, lucide-only icons, segmented controls, no emoji on new work |
| FRONTEND_UI_WORKFLOW_LOGIC.md | The wizard step contract and "no dead-end, mouse-first" rules the acceptance scripts extend. Also `:445` "Full name (text, prefilled from `/me`)": prefilling identity from the profile is an ESTABLISHED convention, so Item A follows precedent rather than inventing a pattern |
| SYSTEM_DESIGN.md (2.2.6, 2.2.7) | `transactions.created_by` (the uploader) is distinct from the deal's agent; `transaction_assignments.role_in_transaction` includes `primary_agent`; `transaction_parties.party_role` includes `buyers_agent` / `listing_agent`. This validates the Item A owner gate: the uploader and the deal's agent are genuinely different people on an on-behalf upload |

### 1.2 Source reviewed (current code, load-bearing findings)

| Finding | Where |
| --- | --- |
| The user's own agent card self-fills EMPTY fields from their account, but only for an existing party that matches their name; nothing is written back to the profile | `NewTransactionWizard.tsx:3602-3622` (self-fill effect), `wizardContactFill.ts:25-82` |
| `partyLooksLikeCurrentUser` returns TRUE for an EMPTY-named card, and neither the self-fill effect nor `isCurrentUser` checks the transaction owner | `wizardContactFill.ts:46-60`, `NewTransactionWizard.tsx:6730-6739` |
| The wizard has an on-behalf-of owner control: Admin / TeamLead / TransactionCoordinator can assign the deal to another user via `owner_user_id`; Agents (and FSBO/Attorney) always own their own deal | `NewTransactionWizard.tsx:3212-3253` (`canAssignOwner`, assignable users), `:4160` (`owner_user_id` on commit), `:6931-6949` (selector) |
| The profile update endpoint exists and refreshes the auth context, and accepts `company_name`; but the convenience hook's body type does NOT | `useOnboarding.ts:87-113` (`useUpdateProfileBasics`, body = `{full_name, phone, bio}` only, `:81-85`); backend `PATCH /users/me` accepts `full_name`,`phone`,`company_name` (`schemas/user.py:52-77`) |
| The collect-info task is created due acceptance + 2 days (`requestBasis`) with a today + 2 fallback, sharing that timing with the signed-copy and missing-docs tasks | `NewTransactionWizard.tsx:4602-4647` |
| A relative `basis` WINS over an absolute `due_date` at task generation; setting the date is not enough, the basis must be removed | `services/task_generation_service.py:441-463` |
| AI finding cards render the proposal label/name plus the "Why you're seeing this" line and the page link, but no document name. The proposal citation carries `document_id` (already used for evidence) | `NewTransactionWizard.tsx` proposal cards (~7900, ~7990), `:4573`; `types/api.ts:1058-1101` |
| Each uploaded document carries `detectedType` and `fileName` in state, keyed by the same `document_id` a citation uses. There is NO document-type humanizer, and `detectedType` spans two vocabularies (base and extended-compliance) | `NewTransactionWizard.tsx:3892-3921`, `wizardTypes.ts:352`; vocab at `prompts.py:57` and `document_packet_parsing.py:501-507` |
| Pre-approval / financing expiration is suppressed twice (prompt omits it; the verifier drops any expiration-labelled proposal) | `prompts.py:276`, `intake_intelligence.py:163-198,322-327` |
| Watchouts are NOT rendered in the wizard at all: they are only persisted to the deal brief at commit. Checklist "compliance to review" cards carry document actions (Waive it / Add requirement / Add as task) | watchouts `NewTransactionWizard.tsx:4691-4697`; checklist buttons `:8254-8319` |
| The collect-info button already hides on the buyer, seller, and BOTH agent roles (only vendors defer), already matching "both agents are mandatory" | `wizardTypes.ts` `CONTACT_REQUIRED_ROLES`, `canDeferPartyContact` |
| A task with no `target` can never default to auto-draft, so an immediate collect-info task sends nothing on its own | `services/automation_posture_service.py:161-168` (`should_default_auto_draft`) |
| The owner selector renders only for Admin / TeamLead / TransactionCoordinator, so a plain Agent / FSBO / Attorney always owns their own deal | `NewTransactionWizard.tsx:3215-3218` (`canAssignOwner`) |

### 1.3 What Audri decided vs. what is still open

Decided: own details come from the profile and write back to it; collect-info tasks are due immediately; AI findings name the document they came from; pre-approval / financing expirations are kept for compliance while all other expirations stay suppressed.

Still open (NOT built here): the fee model, AI actively chasing vendor contacts, and whether a pre-approval expiry should also create a task. See AI_WIZARD_FOLLOWUP_QUESTIONS_ROUND_2.md.

### 1.4 Review corrections (workflow-and-logic passes, R1-R11)

The draft was reviewed against the source across three passes. Each defect below is corrected in place; this log records what was wrong.

- **R1 (Item A, critical workflow).** The draft ignored the on-behalf-of owner control. A TC / TeamLead / Admin can assign a deal to another agent (`owner_user_id`), and Agents/FSBO/Attorneys always own their own. Prefilling or seeding the UPLOADER's profile into the primary agent card, and writing the card back to the UPLOADER's profile, is wrong when the deal belongs to someone else. This also exposes a latent bug: `partyLooksLikeCurrentUser` treats an empty-named agent card as the current user with no owner check (`wizardContactFill.ts:51`, `NewTransactionWizard.tsx:6730-6739`), so a TC's identity can already leak onto another agent's empty card. **Fix:** gate ALL prefill, seeding, and write-back on "the transaction owner resolves to the current user" (`!owner_user_id || owner_user_id === user.id`). This one gate also implements Audri's role split exactly (self-filers own their deals; on-behalf uploads do not) without hardcoding roles. §3 rewritten.
- **R2 (Item A, factual).** The write-back cannot "reuse `useUpdateProfileBasics`" as-is: its body type is `{full_name, phone, bio}` and omits `company_name`, the field most often missing. **Fix:** extend the hook (and `BasicProfileUpdate`) to include `company_name`, or `PATCH /users/me` directly; the endpoint already accepts it. §3.3 corrected.
- **R3 (Item B, logic).** A relative `basis` beats an absolute `due_date` at generation (`task_generation_service.py:451-463`), so setting `due_date = today` while leaving `basis` in place would keep the task at acceptance + 2. **Fix:** the contact-info task must DROP its `basis` and pass only `due_date = today`; this is now load-bearing, not incidental. Note `maybe_roll_forward` may nudge a weekend due date to the next business day, which is acceptable. §4.3 corrected.
- **R4 (Item C, completeness + presentation).** There is no existing document-type humanizer, and `detectedType` uses two vocabularies (`pre_approval` and `pre_approval_letter`, `lead_paint_disclosure`, etc.). Also, forcing "[label] in [document]" reads awkwardly for requirement labels like "Survey". **Fix:** add a label map covering both vocabularies (fall back to `fileName`, then to the label), and present the document name as a prominent source line beside the page link rather than jammed into the heading. §5.3 corrected.
- **R5 (Item D, design + scope, the big one).** Item D had no correct home. Watchouts are never rendered in the wizard (persisted to the brief only), so routing there is invisible; the checklist "compliance to review" cards carry Waive it / Add requirement actions that are meaningless for an expiration date. Surfacing it properly needs a NEW dated compliance-note surface, PLUS an LLM-prompt and extraction change to stop suppressing the pre-approval expiry, PLUS it still has an open sub-question (does it create a task). That is not "obvious and unquestionable" and not a drop-in. **Fix:** Item D is removed from the immediate set and reclassified as a small follow-on that needs one design decision first (§6). Until then the pre-approval expiry stays suppressed (status quo), which is safer than surfacing it in the wrong place.

The following were found on a SECOND review pass over the revised draft.

- **R6 (Item A, timing, workflow).** The `ownedBySelf` gate is necessary but not sufficient if evaluated only at fill time. The owner is chosen on the Contract Details step (Step 2), but the self-fill effect runs when parties are created during the parse, BEFORE Step 2, when `owner_user_id` is still empty (so `ownedBySelf` reads true) and fills once per role via `selfFilledRolesRef` (`NewTransactionWizard.tsx:3606-3622`). An Admin or TC therefore has their identity stamped onto the agent card during the parse, and then reassigning the deal to another agent on Step 2 does NOT clear it, because the effect neither depends on `owner_user_id` nor re-runs. **Fix:** the prefill must depend on `owner_user_id` and be reactive: track which agent-card fields came from the profile (vs. AI-extracted or user-typed), and when the deal is reassigned to another agent (`ownedBySelf` becomes false) withdraw those profile-sourced values (leaving AI/user values). The "It's you / From your profile" treatment, the `onUseMyAccount` button, and the incomplete-profile prompt are all gated on the same reactive `ownedBySelf`. §3.3 updated.
- **R7 (Item A, write-back scope).** "Write back when the profile was missing those values" is under-specified and risks silently rewriting a saved profile from a one-off correction on a single deal (for example a shortened name typed for one closing). **Fix:** the write-back is fill-empty-only. It populates only the profile fields that were EMPTY; it never overwrites a field the profile already had, even with a different non-blank value. §3.3 updated.
- **R8 (Item C, overclaim).** The draft said the document name applies to "the double-check prompts". Double-check fields carry no citation or document (`DoubleCheckField` = `{field,label,pass1,pass2,agree}`, `types/api.ts:1037-1043`); they compare two reads of one value and do not point at a document. **Fix:** scope Item C to the finding cards that carry a `citation` (timeline proposals and checklist/compliance proposals, including waive suggestions). §5.3/§5.4 updated.

The following were found on a THIRD review pass, checking implementation feasibility and side effects.

- **R9 (Item A, render-loop risk).** Seeding a missing own-agent card mutates `state.parties`, which is a dependency of the very effect that would seed it, so a naive implementation re-seeds on every render. The existing effect avoids this for fills with `selfFilledRolesRef` (once per role, `:3606`). **Fix:** the seed must be idempotent under the same guard (seed at most once per agent role per document set), and must not re-seed a card the user deliberately deleted. §3.3 step 2 updated.
- **R10 (Item B, side-effect check, clears the item).** Moving the collect-info task to due-today could plausibly have tripped the auto-draft sweep. Verified it cannot: `should_default_auto_draft` returns False when `target` is None (`automation_posture_service.py:161-168`), and the collect-info task is created with no target by design (there is no email yet, which is the point). So the earlier due date introduces no automation side effect. Recorded so the item is not re-litigated. §4.3 updated.
- **R11 (Item A, scope bound).** The reactive owner-withdrawal (R6) sounds broad but is narrow in practice: the owner selector only renders for Admin / TeamLead / TransactionCoordinator (`canAssignOwner`, `:3215-3218`). A plain Agent, FSBO user, or Attorney never sees it, so `owner_user_id` stays empty and `ownedBySelf` is permanently true for them. **Fix:** state this bound so the common self-filing path stays simple and the reactive logic is understood as an assign-capable-role concern only. §3.3 updated.

The following was found during IMPLEMENTATION and changes the plan.

- **R12 (Item A, force-seeding dropped).** §3.3 step 2 called for seeding the own-agent card when the contract did not name it. In build this proved both over-reach and destabilising: it adds a mandatory party to every self-filed deal, which broke a spread of party/fee integration tests (an extra card shifts indices and, when the profile lacks a phone, blocks the step). Re-reading Audri, she asked for the account holder's details to be PULLED from the profile ("their information doesn't even need to be present ... it should come from the settings/profile page"), not for a new mandatory agent card. **Fix:** the implementation prefills an EXISTING own-agent card (owner-gated), writes back to the profile, and shows the from-profile caption / incomplete-profile prompt — but does NOT create a card the contract omitted. If capturing the own-agent contact when the contract omits it turns out to matter, it can be a separate, lighter surface (for example pulling it at the workspace from the owner's profile) rather than a forced wizard party. This keeps Audri's core ask and the latent-bug fix while removing the churn.

---

## 2. Scope

### 2.1 In scope (this plan)

- **Item A.** The account holder's own details come from their profile, are shown prefilled on the wizard, are collected inline when the profile is incomplete, and are written back to the profile, ALL gated on the account holder actually owning the deal. (Audri Q1)
- **Item B.** The collect-info task is due immediately (the upload day), not acceptance + 2 days. (Audri Q5)
- **Item C.** Every AI finding that points at a document names that document beside its page link, in Audri's format. (Audri Q6)

### 2.2 Out of scope (held for the open questions), and why

- **Fee model changes.** Gated on Round-2 questions 2, 3, 4.
- **AI actively chasing vendor contacts.** Gated on Round-2 question 5 and the send-vs-approve posture. The existing collect-info task is unchanged except its due date (Item B).
- **A hard "co-agent party is mandatory" gate.** The no-defer-button rule already treats both agents as required; a gate forcing a co-agent party to exist depends on who is uploading and breaks on FSBO and dual deals (open B-group).
- **Team Lead / Brokerage Owner connect-and-assign.** A feature in its own right; route to Jake.
- **Item D (pre-approval / financing expiration call-out).** Deferred per R5; needs a surface design decision plus a prompt/extraction change. Kept as a documented follow-on in §6.

---

## 3. Item A - The account holder's own details come from their profile

### 3.1 What Audri asked

The account holder's information should come from their settings/profile rather than being typed. If the profile is incomplete, the wizard should notice and collect it, then write it back so future deals prefill. Both agents are mandatory, sourced differently: the co-agent is typed and required; the account holder's own comes from the profile. Agents, FSBO users, and attorneys enter deals for themselves; TCs, Team Leads, and Brokerage Owners can enter deals for other people.

### 3.2 Current behaviour and the gaps

- Self-fill (`NewTransactionWizard.tsx:3602-3622`) fills only the empty fields of an existing party that matches the user's name. If the contract did not name the user's own agent, there is no card to fill.
- Nothing writes the completed details back to the profile.
- Critically (R1), none of this checks `owner_user_id`, and an empty-named agent card is assumed to be the current user (`wizardContactFill.ts:51`). So when a TC or Team Lead files for another agent, the uploader's identity can be stamped onto that agent's card.

### 3.3 What to build

The gate for every part of this item is **`ownedBySelf = !state.purchase.owner_user_id || state.purchase.owner_user_id === user.id`** (in practice the assignable-users list excludes the current user, so `ownedBySelf` is simply "no other owner was assigned"). When false (filing for another agent), the wizard does none of the prefill/write-back below; the agent cards are typed, exactly as a TC would expect, and filling them from the assigned agent's profile is the separate connect-and-assign feature (open).

**Scope of the gate (R11).** The owner selector renders only for Admin / TeamLead / TransactionCoordinator (`canAssignOwner`, `:3215-3218`). A plain Agent, FSBO user, or Attorney never sees it, so their `owner_user_id` stays empty and `ownedBySelf` is permanently true: for them this item is simply "your card is prefilled from your profile". The reactive behaviour below matters only for the assign-capable roles.

The gate must be **reactive to `owner_user_id`, not evaluated once (R6).** The owner is chosen on Step 2 (Contract Details), but parties and the self-fill effect are created during the parse, before Step 2. So the prefill must (a) include `owner_user_id` in its trigger and (b) track which agent-card fields it sourced from the profile, so that if the deal is later reassigned to another agent it withdraws exactly those profile-sourced values (leaving any AI-extracted or user-typed value intact). The "It's you / From your profile" treatment, the `onUseMyAccount` button (`:6740-6746`), and the incomplete-profile prompt are all gated on this same reactive `ownedBySelf`.

1. **Gate the existing self-fill and `isCurrentUser` on the reactive `ownedBySelf`.** This fixes the latent leak (R1) and the timing leak (R6): a TC who parses a deal and then assigns it to another agent no longer keeps their own account stamped onto the agent card.

2. **Prefill the account holder's own agent card from their profile, when `ownedBySelf` (as built).** When the parse produced the user's own agent card (a `userAgentRolesForRepresentation` role matched by `partyLooksLikeCurrentUser`), fill its EMPTY fields from the profile via `fillAgentPartyFromUser`, guarded once per role by `selfFilledRolesRef` (it mutates `state.parties`, a dependency of the effect, so an unguarded version would loop — this is the surviving half of R9).

   **No card is created that the contract omitted (R12).** The draft called for seeding a missing card; that was dropped in build. Force-adding a mandatory agent party to every self-filed deal is over-reach against Audri's actual ask ("their information doesn't even need to be present ... it should come from the profile") and destabilising (an extra card shifts party indices and, when the profile lacks a phone, blocks the step). If capturing the own-agent contact when the contract omits it proves necessary, it belongs on a lighter surface (for example pulling it at the workspace from the owner's profile), not a forced wizard party.

   The existing precedence is preserved: the self-fill only populates EMPTY fields, so a contract-extracted agent email is never overwritten by the profile. The profile fills gaps; it does not overrule the document.

3. **Mark the card as sourced from the profile.** Extend the existing "It's you / Filled from your account settings" treatment (`NewTransactionWizard.tsx:11285-11331`) so the own-agent card reads as prefilled-from-profile with a small "From your profile" caption and an Edit affordance, not four blank required inputs. The co-agent card is untouched (typed, required, no button).

4. **Detect an incomplete profile and collect it inline.** "Complete" = full_name + email + phone + company; in practice full_name and email always exist from registration, so the real check is phone + company, matching the existing `accountIncomplete` (`:6737-6739`). When incomplete, the own-agent card shows the missing fields editable with one line: "Add your phone and brokerage so we can save them to your profile for next time." No separate screen.

5. **Write back to the profile at commit, fill-empty-only (R7), when `ownedBySelf`.** Send only the profile fields that were EMPTY (typically phone and company) to `PATCH /api/v1/users/me`. Never overwrite a profile field the user already had, even with a different non-blank value, so a one-off correction on a single deal cannot silently rewrite their saved profile. Because the convenience hook omits `company_name` (R2), either extend `useUpdateProfileBasics` + `BasicProfileUpdate` to include it or call `apiFetch('/api/v1/users/me', { method: 'PATCH', ... })` directly, then refresh the auth user so the next wizard is prefilled. Best-effort and non-fatal: a failure never blocks the transaction.

### 3.4 Acceptance (mouse-only)

- **Agent, complete profile:** start a deal. The own-agent card is prefilled, marked "From your profile", zero typing.
- **Agent, incomplete profile:** start a deal, fill the missing phone/brokerage once, upload. Open Settings: the values are now saved. Start a second deal: the card is already complete.
- **TC filing for another agent:** in "Who's Transaction Is It?", pick another agent. The primary agent card is NOT prefilled with my (the TC's) details, and nothing is written to my profile. Both agent cards are typed and required, with no "collect later" button.
- **Reassignment mid-flow (R6):** parse a deal as an Admin/TC (own-agent card prefills), then on Contract Details reassign it to another agent. Return to Contacts: my prefilled details have been withdrawn from the agent card, so the other agent's deal does not carry my identity.
- **Fill-empty-only (R7):** with a profile that already has a name, complete a deal where I typed a slightly different name on my agent card; after upload my saved profile name is unchanged (only the empty phone/brokerage were saved).
- The co-agent card always requires name, email, and phone, with no button.

---

## 4. Item B - Collect-info task is due immediately

### 4.1 What Audri asked

"Please make it due immediately. Time is of the essence getting docs to the appropriate parties."

### 4.2 Current behaviour

The collect-info task is created with `basis` = acceptance + 2 days and `due_date` = today + 2 (`NewTransactionWizard.tsx:4640-4641`), sharing `requestBasis` / `requestDueFallback` with the signed-copy and missing-docs tasks.

### 4.3 What to build

Scope the change to the `contact_info` task only. Give it `due_date` = today (local `YYYY-MM-DD`) and **omit `basis` entirely**. Omitting the basis is load-bearing (R3): the backend resolves a relative basis over an absolute date (`task_generation_service.py:451-463`), so leaving the acceptance + 2 basis in place would keep the task two days out. Note the three intake tasks currently share one `requestBasis` / `requestDueFallback` pair, so this needs its own date rather than an edit to the shared values. Leave the signed-copy and missing-documents tasks on their existing timing (Audri did not ask to change those). `maybe_roll_forward` may move a same-day due over a weekend to the next business day, which is acceptable for "immediately".

**No automation side effect (R10).** Pulling the due date earlier cannot trigger an auto-send: `should_default_auto_draft` returns False when a task has no `target` (`automation_posture_service.py:161-168`), and the collect-info task is created with no target by design, since there is no email yet. AI actively chasing the vendor is the separate, still-open item in §2.2.

### 4.4 Acceptance (mouse-only)

- Defer a vendor's contact and upload. Open the deal's task list: the "Collect contact details for [vendor]" task is due today (or the next business day), not two days out.
- The signed-copy and missing-documents intake tasks are unchanged.

---

## 5. Item C - AI findings name the document they came from

### 5.1 What Audri asked

Keep the page number and the in-document search (she praised both). Add the name of the document the finding refers to, so the card reads like "Date Missing in Lead Based Paint Disclosure" and the user can see at a glance which document it came from. This also closes her Q2 "unclear findings" note (screenshot 146/147): that card was the blank-title waive suggestion, whose title was already fixed last round to show the requirement name and a plain-English line; naming the document is the remaining piece.

### 5.2 Current behaviour and available data

- Timeline and checklist proposal cards render the proposal's label/name plus the "Why you're seeing this" line and "View in document (page N)". None names the document.
- The data is present client-side: the proposal `citation.document_id` (already read at `:4573`) maps to a `WizardDocument` carrying `detectedType` and `fileName`. No backend change needed.

### 5.3 What to build

1. **A document-name resolver (frontend).** Given a `document_id`, return a human name: humanize `detectedType` through a small label map that covers BOTH vocabularies (R4) - base (`pre_approval` -> "Pre-Approval Letter", `sellers_disclosure` -> "Seller's Disclosure", ...) and extended-compliance (`pre_approval_letter`, `lead_paint_disclosure` -> "Lead Based Paint Disclosure", ...). Fall back to the uploaded `fileName` when the type is missing, then to nothing. Keep the map beside the document-type enums so it stays in sync. One helper keyed off `state.documents`, reused by every finding card.

2. **Present the document name prominently, without awkward grammar (R4).** Keep the existing obligation/requirement label as the card heading. Directly beneath it, show the source as "in [Document Name]" merged with the existing page link, e.g. "Lead Based Paint Disclosure - page 5" as a single clickable source line. This delivers Audri's ask (the document is named right at the top of the card) and matches her example, while reading correctly for every label, including requirement names like "Survey" where "Survey in Lead Based Paint Disclosure" would not.

3. **Keep page and search.** The "View in document (page N)" behaviour and the viewer search are unchanged; the document name is additive.

4. **Apply to the finding cards that carry a citation (R8).** Timeline proposals and checklist/compliance proposals (including waive suggestions) both carry a `citation` and get the shared source-line component. The double-check prompts are explicitly OUT: `DoubleCheckField` has no citation or document (it compares two reads of one value, `types/api.ts:1037-1043`), so there is no document to name there. When a proposal has no citation document_id (for example a demoted dead-citation row), show the label without a source line rather than inventing one.

### 5.4 Acceptance (mouse-only)

- Upload the ten-document fixture. On Verification, each "found in the contract" card (timeline and compliance/waive) names the document it came from (for example "Lead Based Paint Disclosure - page 5"), and the page link and document search still work.
- A finding whose citation could not be located shows its label with no source line (never a blank title or a raw internal id). The double-check panel is unchanged (it names no document by design).

---

## 6. Item D (deferred) - Pre-approval / financing expiration as a compliance call-out

Audri asked to keep pre-approval and financing-letter expirations "for compliance" while suppressing every other expiration. This is a real ask, but the review (R5) found it is not a drop-in, so it is intentionally NOT in the immediate build:

- **No fitting surface exists today.** Watchouts are never shown in the wizard (persisted to the brief at commit only), and the checklist "compliance to review" cards carry Waive it / Add requirement / Add as task actions that make no sense for an expiration date.
- **It needs backend changes with re-testing risk.** The pre-approval expiry is suppressed twice (prompt + verifier); surfacing it means loosening the prompt to extract that one date and carving it out of `_is_expiration_proposal`, then re-verifying that no other expiration leaks back in.
- **It has an open sub-question.** Whether an expired or expiring pre-approval should also create a "request an updated letter" task (Round-2 question 1).

**Recommended shape when it is built:** a new dated, informational compliance-note card (no Waive/Add-requirement actions), carrying the date, the citation, and Item C's document-name source line, shown flagged as expired when the date has passed. Until the surface is decided, the pre-approval expiry stays suppressed, which is safer than putting it in the wrong place. One small design decision unblocks it: where the call-out lives.

---

## 7. UI, UX, and design standards (applies to every in-scope item)

The testers are real-estate professionals, so every item must be provable by clicking through the wizard, with no developer tools.

- **Mouse-first, minimal typing.** Item A removes typing when the profile is complete and reduces it to a one-time entry otherwise; it never adds a required free-text field for a self-filing agent. Items B and C add no input.
- **One surface, no dead ends.** Item A collects the profile inline on the contacts step (it offers a Settings link but completes in place). Item C stays on Verification where the user already is.
- **Design system.** Reuse the branded input, the champagne "from your profile" caption already used for the self-fill banner, lucide icons only, and the existing proposal-card layout. No new visual language, no emoji, no gradient panels.
- **Professional-tool feel.** The finding source line ("Lead Based Paint Disclosure - page 5") reads like a coordinator's reference, not a debug log. The profile prefill reads as the app already knowing the user.
- **Honesty.** Item A never overwrites a populated profile field with a blank and never stamps the uploader onto another agent's deal. Item C falls back to the file name, then to the label, and never fabricates a document name.

---

## 8. Invariants this plan obeys

1. No in-scope item is built on an open question; everything gated on Round-2 questions is in section 2.2 or §6.
2. All profile prefill and write-back are gated on the account holder owning the deal, and the gate is REACTIVE to `owner_user_id`: reassigning the deal to another agent withdraws any profile-sourced value already placed on the agent card. On-behalf uploads are untouched. (No agent card is force-created; see R12.)
3. Profile write-back reuses `PATCH /users/me`, is fill-empty-only (never overwrites a field the profile already had, blank or not), and is non-fatal.
4. The server remains the single place deadline arithmetic happens; Item B changes only which absolute date is sent (and removes the competing basis), adding no client-side arithmetic beyond "today".
5. Item C adds no backend fields (the document name is resolved from data already in state).
6. Existing behaviour that already matches Audri's intent is left alone (the collect-info button already excludes both agents; the signed-copy/missing-docs timing is unchanged).

---

## 9. Phasing and rough effort

| Phase | Contents | Depends on | Effort |
| --- | --- | --- | --- |
| 1 | Item B (collect-info due immediately) and Item C (document-name source line). Small, isolated, frontend-only, high-visibility. | none | 0.5 to 1 day |
| 2 | Item A (own details from profile + write-back), gated on `owner_user_id`. Owner-reactive prefill of an existing own-agent card, prefilled/captioned state, incomplete-profile inline collect, commit-time fill-empty-only write-back, and the self-fill owner-guard fix. (No card seeding; R12.) | existing `PATCH /users/me` (extended for company_name) | 1 to 1.5 days |
| 3 (follow-on, needs a decision) | Item D, only after the surface question is answered. | §6 decision | 1 to 1.5 days |
| Verify | Mouse-only walkthrough of the acceptance scripts, including the TC-files-for-another-agent case and the incomplete-profile write-back loop. | Phases 1, 2 | 0.5 day |

Phases 1 and 2 are independent and can proceed in parallel.

---

## 10. Verification (mouse-only, tester-facing)

Run with the real admin account and the ten `testing_docs` PDFs uploaded together, plus one deliberately incomplete profile and one on-behalf assignment.

1. **Profile prefill, self (Item A).** On a deal whose contract names the account holder's own agent: complete profile -> that card is prefilled and marked from-profile, zero typing; incomplete profile -> fill the missing phone/brokerage once, upload, confirm Settings now shows them saved, start a second deal and confirm it is prefilled. (No own-agent card is created when the contract omits one; R12.)
2. **On-behalf guard (Item A, R1).** As a TC/TeamLead, assign the deal to another agent: the primary agent card is NOT prefilled with the uploader's details, and the uploader's profile is not written.
3. **Collect-info timing (Item B).** Defer a vendor, upload, confirm the collect task is due today.
4. **Finding document names (Item C).** On Verification, every finding names its document and keeps the page link and search.
5. **Regression.** The four Step-1-through-4 behaviours from the last round (centered representation question, four-phase parsing, Find in Document, continuous scroll, fee sections, Upload button at the bottom) still pass.

Each script is a click path a real-estate tester can run unaided.
