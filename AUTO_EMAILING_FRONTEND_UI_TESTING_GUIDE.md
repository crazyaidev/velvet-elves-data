# Auto Emailing Frontend UI Testing Guide

**Last updated:** 2026-06-08  
**Scope:** Frontend UI verification for the currently updated auto emailing feature set in `velvet-elves-frontend`.  
**Audience:** Jan, QA testers, and product stakeholders validating the feature in local or dev environments.

---

## 1. What This Guide Covers

This guide verifies the updated AI email experience across the browser UI:

1. Deal-scoped **Compose with AI** from the transaction Communications panel.
2. Non-developer **Test inbound** harness from the transaction Communications panel.
3. **AI Email Review** improvements: attachments, source data, bulk approve/send, admin audit link.
4. **Email Templates** management at `/email-templates`.
5. **AI Governance** email automation settings.
6. User **Email signature** profile setting.
7. Inbound email match-basis badges in the Communications panel.

This is a frontend UI guide. It assumes backend migrations and API behavior are already available in the test environment.

---

## 2. Pre-Flight Checklist

Before UI testing, confirm:

1. Frontend is running:

   ```powershell
   cd c:\Projects\velvet-elves-frontend
   npm run dev
   ```

2. Backend is running and reachable from the frontend.
3. Test tenant has at least:
   - one Admin user,
   - one Agent or Transaction Coordinator user,
   - one transaction with a property address and closing date,
   - at least one transaction party with an email address,
   - at least one uploaded document if testing attachment behavior.
4. The user has a connected mailbox if testing real approve/send behavior.
5. Browser devtools console is open during testing. Any red console error is a test failure unless it is a known unrelated environment warning.

Recommended browser matrix:

| Browser | Required | Notes |
| --- | --- | --- |
| Chrome latest | Yes | Primary QA browser |
| Edge latest | Recommended | Good Windows parity check |
| Mobile viewport in Chrome devtools | Yes | Check layout at 390px width |

---

## 3. Role Matrix

| Surface | Admin | Team Lead | Agent | Transaction Coordinator | Portal roles |
| --- | --- | --- | --- | --- | --- |
| `/ai-emails` review queue | Yes | Yes | Yes | Yes | No |
| Compose with AI from deal communications | Yes | Yes | Yes | Yes | No |
| Test inbound from deal communications | Yes | Yes | Yes | Yes | No |
| `/email-templates` | Yes | Yes | Yes | Yes | No |
| Create shared tenant templates | Yes | Yes | No | No | No |
| AI Governance email settings | Yes | Expected Admin-only | No | No | No |
| Email audit log deep link | Yes | If route allows | No | No | No |
| Profile email signature | Yes | Yes | Yes | Yes | No portal-only users |

If the app allows a role outside this matrix, record it as a permissions bug unless product has explicitly approved it.

---

## 4. Shared Test Data

Use one transaction for most tests:

| Field | Suggested value |
| --- | --- |
| Address | `123 Maple St, Indianapolis, IN 46204` |
| Closing date | `2026-07-15` |
| Party 1 | `Buyer Jane`, `buyer.jane@example.com` |
| Party 2 | `Seller Sam`, `seller.sam@example.com` |
| Uploaded document | `Apex Inspection Report - 123 Maple St.pdf` |

Expected UI behavior should not depend on today's date except where the page explicitly displays "Updated" or current summary timestamps.

---

## 5. Transaction Communications Panel

### 5.1 Compose With AI Entry Point

Goal: confirm users can start a deal-scoped AI compose flow from the Communications panel.

Steps:

1. Sign in as Agent.
2. Open a transaction with at least one party email.
3. Open the transaction **Communications** panel.
4. Confirm there is a **Compose** button with a sparkle icon.
5. Click **Compose**.

Expected:

- A modal opens titled **Compose with AI**.
- The modal references the current deal when a deal label is available.
- Party recipients appear as selectable chips.
- The **All parties** control selects and clears all recipients.
- The **Generate** button is disabled until at least one recipient is selected and either a template or intent text is provided.
- Closing the modal returns to the Communications panel without navigation.

Failure examples:

- Compose button is missing for allowed internal roles.
- Modal opens with no recipients even though transaction parties have email addresses.
- Generate is enabled with no recipient.
- Any selected chip causes layout shift or text overflow.

### 5.2 Compose With Intent

Goal: generate a pending AI draft using freeform intent.

Steps:

1. Open **Compose with AI**.
2. Select `Buyer Jane`.
3. Leave template blank.
4. Enter intent: `Send a short update that closing is still on track.`
5. Click **Generate**.

Expected:

- Button shows a pending state while generating.
- Success toast says drafts are ready or some drafts are ready.
- Modal closes.
- User navigates to `/ai-emails`.
- A new outbound draft appears in the review queue.
- Draft does not send automatically.

### 5.3 Compose With Template

Goal: generate a pending AI draft from a reusable template.

Steps:

1. Open **Compose with AI**.
2. Select one or more recipients.
3. Choose a template from the template dropdown.
4. Confirm freeform intent is no longer required.
5. Click **Generate**.

Expected:

- One pending draft is created per selected recipient.
- Each draft appears in `/ai-emails`.
- The subject/body are grounded in the transaction context.
- No external email is sent until human approval.

### 5.4 No Party Emails Empty State

Goal: verify the modal handles a transaction with no party email addresses.

Steps:

1. Open a transaction that has parties but no email addresses.
2. Open **Compose with AI**.

Expected:

- Modal shows a clear empty state explaining that a contact email is needed.
- Generate stays disabled.
- No crash, blank modal, or `undefined` text appears.

### 5.5 Test Inbound Entry Point

Goal: allow non-developers to create a realistic inbound email and AI draft.

Steps:

1. Open a transaction Communications panel.
2. Click **Test**.
3. Confirm a modal titled **Send a test email** opens.
4. Choose each scenario in separate runs:
   - Closing question
   - Document request
   - Vendor schedule reply

Expected:

- A success toast appears.
- User navigates to `/ai-emails`.
- For scenarios that need a reply, a draft appears in the review queue.
- No external email is sent.
- The feature is visually marked as a test action, not a production send.

### 5.6 Inbound Match-Basis Badge

Goal: show why an inbound email was filed to a deal.

Steps:

1. Open the Communications panel for a transaction with inbound logs.
2. Find inbound rows created by different matching paths if available:
   - party email,
   - address,
   - subject tag,
   - learned sender,
   - user filed,
   - unmatched.

Expected:

- Inbound rows show a small badge such as **Matched by party**, **Matched by address**, **Matched by tag**, **Auto-filed**, or **Filed by you**.
- Badge text stays inside the row at desktop and mobile widths.
- Outbound rows do not show inbound match-basis badges.

---

## 6. AI Email Review Page

Route: `/ai-emails`

### 6.1 Base Page States

Goal: verify loading, empty, error, and populated states.

Expected:

- Loading state shows skeleton/placeholder UI, not a blank page.
- Empty state clearly explains there are no drafts.
- Error state has a retry/refresh affordance.
- Populated state shows draft list, detail pane, confidence/kind metadata, and action controls.

### 6.2 Attachment Chips

Goal: reviewers can see what file will be attached before approval.

Steps:

1. Create or use a document-request draft where the AI matched a document.
2. Open the draft in `/ai-emails`.

Expected:

- An **Attaches** row appears above the draft body.
- The chip shows the matched document name when available.
- If only IDs/counts are available, the chip shows a file count.
- The source-data panel does not expose internal IDs such as `matched_document_id`.
- The draft body must not promise an attachment unless an attachment chip is present.

### 6.3 Single Draft Approve And Send

Goal: verify the existing human approval workflow still works.

Steps:

1. Open a pending or ready draft.
2. Review subject, body, assumptions, source data, and attachment chips.
3. Click **Approve & Send**.
4. Confirm the dialog.

Expected:

- Confirmation copy clearly states the email will send now.
- Pending state prevents double-click sends.
- On success, the draft leaves the pending queue or updates status.
- Success toast appears.
- Communication log records the sent email.
- If mailbox integration is missing, a clear error is shown and the draft remains reviewable.

### 6.4 Bulk Approve On Ready Tab

Goal: verify bulk approval only exists where intended.

Steps:

1. Open `/ai-emails`.
2. Switch to the **Ready to Send** tab.
3. Select one draft using the row checkbox.
4. Use **Select all**.
5. Click **Approve & Send (N)**.
6. Confirm the dialog.

Expected:

- Checkboxes appear only on the Ready to Send tab.
- Selected count is correct.
- Select all toggles all visible ready drafts only.
- Confirmation states how many replies will send and how many recipients are involved.
- Bulk action sends each selected draft once.
- Success toast reports full or partial success.
- Failed drafts remain in the queue.
- Selection clears after the action.

Regression checks:

- Switching away from the Ready tab clears bulk selection.
- Sent/discarded drafts are pruned from selection.
- Row click still opens the draft without toggling the checkbox unless the checkbox itself is used.

### 6.5 Admin Audit Log Link

Goal: Admin can jump from AI Email Review to filtered audit logs.

Steps:

1. Sign in as Admin.
2. Open `/ai-emails`.
3. Confirm **Audit log** action appears in the header.
4. Click it.

Expected:

- User navigates to `/admin/audit-logs?entity=ai_email`.
- Audit log page opens with `ai_email` preselected as the entity filter.
- Non-admin users do not see the audit-log action.

### 6.6 Source Data Presentation

Goal: source data should be useful to humans, not internal plumbing.

Expected:

- Human-readable source fields render in the source panel.
- Empty values are hidden.
- Internal fields ending in `_id` are hidden.
- Assumptions remain visible and understandable.
- No raw encrypted value or database ID is shown in normal review UI.

---

## 7. Email Templates Page

Route: `/email-templates`

### 7.1 Route And Navigation Access

Goal: confirm allowed users can reach the templates page.

Steps:

1. Sign in as Agent, Transaction Coordinator, Team Lead, and Admin.
2. Visit `/email-templates`.

Expected:

- Allowed internal roles can open the page.
- Portal roles cannot access the route.
- Page header shows **Email Templates** and a count badge.
- New template CTA is visible to allowed roles.

### 7.2 Template List

Goal: verify system, shared, and personal template types display correctly.

Expected:

- Starter/system templates appear as read-only starter templates.
- Shared tenant templates use a **Shared** style/label.
- Personal templates use a **Personal** style/label.
- Cards show name, category when present, subject preview, and body preview.
- Long subject/body text wraps without overlapping actions.

### 7.3 Create Personal Template

Steps:

1. Sign in as Agent.
2. Open `/email-templates`.
3. Click **New template**.
4. Fill:
   - Name: `Quick closing update`
   - Category: `client_update`
   - Subject: `Update for {{property_address}}`
   - Body: `Hi {{buyer_name}}, closing is still on track for {{closing_date}}.`
5. Save.

Expected:

- Save is disabled until required fields are filled.
- Success toast appears.
- Dialog closes.
- New template appears as **Personal**.
- Template appears in the Compose modal dropdown.

### 7.4 Shared Template Permissions

Steps:

1. Sign in as Admin or Team Lead.
2. Create a new template with scope **Shared**.
3. Sign in as Agent.
4. Open `/email-templates` and the Compose modal.

Expected:

- Admin/Team Lead can create shared templates.
- Agent can see and use shared templates.
- Agent cannot create or edit shared templates.
- If the UI exposes a shared scope to Agent, save should fail gracefully and show an understandable error.

### 7.5 Copy Starter Template

Steps:

1. Open `/email-templates`.
2. Choose a starter/system template.
3. Click copy/save-a-copy action.
4. Save the copied template.

Expected:

- Copied template opens in the edit dialog.
- Name is prefixed with `Copy of`.
- Scope defaults to personal unless an Admin/Team Lead deliberately changes it.
- Saved copy is editable and deletable.
- Original starter template remains unchanged and read-only.

### 7.6 Edit And Delete Template

Expected:

- Editable templates can be changed and saved.
- Delete requires confirmation.
- Deleted templates disappear from the page and Compose dropdown.
- System/starter templates cannot be edited or deleted.
- Errors show a toast and leave the dialog state intact for retry.

### 7.7 Placeholder Usability

Expected:

- Supported placeholders are visible or discoverable on the page:
  - `{{property_address}}`
  - `{{closing_date}}`
  - `{{buyer_name}}`
  - `{{seller_name}}`
- Placeholder chips/text never overflow on mobile.
- Template body textareas support multiline content.

---

## 8. AI Governance Email Automation Settings

Route: `/admin/ai-governance`

### 8.1 Section Presence

Goal: confirm the new email automation controls are visible in AI Governance.

Steps:

1. Sign in as Admin.
2. Open `/admin/ai-governance`.

Expected:

- An **Email automation** section appears near other AI provider/governance controls.
- It includes tone, confidence threshold, escalation hours, disclaimer, preview, and Save.

### 8.2 Tone Control

Expected:

- Tone choices are **Professional**, **Friendly**, and **Concise**.
- Selecting a tone visibly changes the active state.
- Only one tone can be active at a time.

### 8.3 Threshold And Escalation Sliders

Expected:

- Confidence threshold slider ranges from 80% to 100%.
- Escalation slider ranges from 24h to 48h.
- Displayed numeric values update immediately while dragging.
- Layout remains stable while values change.
- Save button becomes enabled only when values differ from saved settings.

### 8.4 Disclaimer

Steps:

1. Edit the disclaimer.
2. Confirm preview updates.
3. Click **Use recommended**.
4. Save.

Expected:

- Disclaimer field enforces its character limit.
- Preview reflects the current disclaimer.
- Use recommended restores the default disclaimer text.
- Success toast appears after save.
- Refreshing the page shows saved settings.

---

## 9. Profile Email Signature

Surface: Account/Profile section.

### 9.1 Signature Field

Goal: internal users can define the signature appended to AI email replies.

Steps:

1. Sign in as Agent.
2. Open account/profile settings.
3. Find **Email signature**.
4. Enter:

   ```text
   Jane Smith
   Velvet Elves Realty
   (317) 555-1234
   ```

5. Save.
6. Refresh profile settings.

Expected:

- Field appears for internal users.
- Field does not appear for portal-only users.
- Save button becomes dirty when signature changes.
- Saved signature persists after refresh.
- Character limit prevents overly long input without breaking layout.

### 9.2 Signature In Drafts

Goal: generated drafts use the saved signature.

Steps:

1. Save an email signature.
2. Generate an AI email draft.
3. Open the draft in `/ai-emails`.

Expected:

- Draft body uses the saved signature block before the disclaimer.
- If no signature is saved, generated drafts should fall back to name/company/phone or platform default behavior.

---

## 10. Responsive And Accessibility Checks

Test these surfaces at desktop width and 390px mobile width:

- Communications panel with Compose and Test buttons.
- Compose modal.
- Test inbound modal.
- AI Email Review list and detail pane.
- Bulk approve toolbar.
- Attachment chips.
- Email Templates cards and edit dialog.
- AI Governance email automation section.
- Profile signature textarea.

Expected:

- No horizontal page scroll unless the app shell intentionally scrolls.
- Text does not overlap icons, chips, buttons, or adjacent rows.
- Buttons have accessible names.
- Icon-only or compact buttons have `aria-label` or useful `title`.
- Modal focus starts inside the modal and returns to the triggering control on close where supported by the dialog component.
- Keyboard users can tab through inputs and actions in a sensible order.
- Entering long text in template/body/signature fields does not collapse the layout.

---

## 11. Automated UI Test Recommendations

Add or update tests when touching this feature. Prefer React Testing Library, user-event, React Query test providers, MemoryRouter, and MSW handlers.

Recommended unit/integration coverage:

| Area | Test |
| --- | --- |
| `ComposeEmailModal` | Generate disabled until recipient plus template/intent are present |
| `ComposeEmailModal` | All parties toggles all recipients |
| `ComposeEmailModal` | Successful compose navigates to `/ai-emails` |
| `TestInboundButton` | Scenario click calls test-inbound mutation and navigates to `/ai-emails` |
| `AiEmailReviewPage` | Ready tab shows checkboxes and bulk action only there |
| `AiEmailReviewPage` | Bulk selection clears when leaving Ready tab |
| `AiEmailReviewPage` | Attachment chip renders for `attachment_ids` |
| `AiEmailReviewPage` | Source panel hides keys ending in `_id` |
| `EmailTemplatesPage` | System templates are copy-only/read-only |
| `EmailTemplatesPage` | Agent cannot save shared template scope |
| `EmailAutomationSection` | Dirty state and save payload update correctly |
| `ProfileSection` | Email signature is saved into `profile_settings.email_signature` |

Avoid snapshot tests for this feature. The UI is form-heavy and workflow-heavy; behavior tests catch more meaningful regressions.

---

## 12. Smoke Test Script

Run this short script before handing the feature to a stakeholder:

1. Admin opens `/admin/ai-governance`, changes email automation settings, saves, refreshes, confirms persistence.
2. Agent opens profile, saves an email signature, refreshes, confirms persistence.
3. Agent opens `/email-templates`, creates a personal template.
4. Admin creates a shared template; Agent confirms it appears.
5. Agent opens a transaction Communications panel, uses **Compose** with the personal template, generates a draft.
6. Agent opens `/ai-emails`, confirms draft content, source data, signature, and any attachment chip.
7. Agent uses **Test** inbound on the same transaction and confirms a new draft appears.
8. If connected mailbox is available, Agent approves one draft and confirms a sent communication log row.
9. Admin opens `/ai-emails`, clicks **Audit log**, confirms filtered audit logs open.
10. Tester repeats the key screens at 390px mobile width.

Pass criteria: no console errors, no broken navigation, no permission leaks, no automatic sends before approval, and no layout overlap.

---

## 13. Bug Report Template

Use this format for issues:

```text
Feature area:
Role:
Environment:
Browser:
Viewport:
Transaction id or address:
Steps to reproduce:
Expected:
Actual:
Screenshot/video:
Console error:
Network response, if relevant:
Severity:
```

Severity guidance:

| Severity | Meaning |
| --- | --- |
| P0 | Email sends without approval, wrong recipient, data leak, or permission bypass |
| P1 | Core workflow blocked: cannot compose, review, approve, or save settings/templates |
| P2 | Important degraded behavior: wrong badge, missing attachment chip, partial responsive break |
| P3 | Copy, spacing, minor visual polish, non-blocking annoyance |

---

## 14. Final Acceptance Criteria

The updated auto emailing frontend is ready when:

1. Allowed roles can compose AI drafts from a transaction and review them before send.
2. No UI path sends an AI email without explicit human approval.
3. Test inbound creates realistic review-queue drafts without external email.
4. Attachments are visible before approval when a draft promises a document.
5. Email templates can be created, copied, edited, deleted, and used according to role permissions.
6. AI email governance settings save and reload correctly.
7. User email signatures save and appear in generated drafts.
8. Admin can reach filtered AI email audit logs from the review page.
9. Inbound match-basis badges explain why emails were filed to a deal.
10. Desktop and mobile layouts remain readable, clickable, and free of overlap.
