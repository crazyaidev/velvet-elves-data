# AI Wizard - Testing Notes Status Report

**Prepared by:** Jan (sole developer)
**Date:** July 23, 2026
**Scope:** Audri's July 22 testing round on the AI Wizard

---

## Summary

I have addressed every item in Audri's testing notes. All changes are implemented, and I verified them in a real Chrome browser: I logged in with the admin account, uploaded all ten test documents for 5915 E 350 N at once, and walked the wizard from Step 1 through Verification. Where a behavior is easier to prove deterministically, I also added automated tests. Two of my earlier follow-up questions are already confirmed by Audri; five remain open and are listed at the end. I shipped a sensible default for each open item, so nothing is blocked on my side.

## Status of each note

| Step | Audri's note | Status | How I verified it |
| --- | --- | --- | --- |
| 1 | Make "Who are you representing?" stand out, and center it with the choices below | Done | Real Chrome: the question is centered and enlarged, with the Buyer / Seller / Buyer & Seller choices stacked below it |
| 1 | While parsing, show a simple "thinking" screen instead of the per-document detail | Done | Real Chrome: four fixed phases with a spinner, and none of the per-file narration |
| 2 | The "Find in Document" magnifiers did not work | Done | Real Chrome: the magnifier now locates and highlights the value inside the document. Root cause was that dates and prices were searched in a format no contract uses |
| 3 | Let the mouse scroll through the document pages when it is over the viewer | Done | Real Chrome: smooth, continuous scrolling through every page. I rebuilt the viewer to render all pages in one scroll area |
| 3 | Add "Create a task to collect this information" on the contact cards | Done | Real Chrome: the button appears on vendor cards; deferring makes email and phone optional and creates the task, which is listed on Verification. Also covered by an automated test |
| 3 | Remove "separate from the app's own per-deal billing fee" from the Transaction fee box | Done | Real Chrome: the sentence is gone |
| 3 | Remove the orange contract-clause box | Done | Real Chrome: the box is gone |
| 3 | New request: for Seller / dual, capture the listing and buyer-agent fees and any seller contribution | Done | Automated test plus earlier real Chrome: a two-card layout with the "is the seller paying any of the buyer agent's fee, and how much" question |
| 3 | Make the "needs your eyes" requests clearer, and never surface expiration dates | Done | Real Chrome: each card carries a plain-English "Why you're seeing this" line, and no expiration box appears even with four counter offers uploaded |
| 4 | Add the professional fee(s) so a user can verify them, and say "Paid by Buyer / Paid by Seller" | Done | Automated test: the fees always show on Verification, worded "Paid by Buyer" / "Paid by Seller" |
| 4 | Move the "Upload Transaction" button to the bottom of the page | Done | Real Chrome: the button is the last thing on the page, with the disclaimers around it and everything else above |
| Sales note | Vendor directory value | Noted | The new collect-info task pairs naturally with saving good vendors, which reinforces this point |

## Verification detail

I ran the full walkthrough with the exact fixture set Audri specified: ten documents for 5915 E 350 N (a purchase agreement, four counter offers, an amendment, earnest money, the signed seller's disclosure, a post-closing possession agreement, and a pre-approval letter), all uploaded together. The parse of ten documents takes several minutes, which is expected for a packet that size, and it completed and drove the review steps correctly. Screenshots of each step are saved with my working notes.

## Open questions (defaults shipped, awaiting Audri)

I captured these in a separate document, "AI Wizard - Questions & Answers for Audri". In short:

- **Collect-info button:** I hide it on both principals and both agents (vendors only). I want to confirm whether your own side's agent should also be allowed to defer.
- **Expiration dates:** I suppress them entirely rather than renaming the box, and I included the pre-approval letter expiry in that. I want to confirm both choices.
- **Seller / dual fees:** I assume the seller pays part of the buyer-agent fee and the buyer pays the rest. I want to confirm that split and whether the question applies on a dual deal.
- **"Paid by" wording:** confirm the phrasing for a fee split across both sides.
- **Collect-info task:** confirm the task name and its default due date.

## Bottom line

Every item Audri raised is resolved and confirmed working in a real browser with the ten-document upload. The most important fixes, the expiration suppression against real counter offers and the continuous document scrolling, are both verified. I will update and re-verify anything that changes once Audri answers the five open questions.
