# Features 14–32 testing notes (1 Sep 2026)

Staging: https://app.stage.velvetelves.com  
Account: crazyaidev20500519@gmail.com  
I did not press Send, Run AI tasks, Disconnect, or Change status.

New files (stamp 20260901): 500 Test Elm Dr, 600 Test Birch Way, 200 Test Maple Ave, 300 Test Pine Ct, 400 Test Cedar St, 410 Test No Contract Ln, 700 Test Dual Ave, 710 Order Title Ln, 720 Confirm Title Ln, 800 Test Utility Ln, 810 Order Warranty Ln.

Workspace How it runs default is Autopilot. I pinned Maple to Manual and the Autopilot seed files to Assisted so overnight would not mail.

Screenshots and dumps: `aime_automation_qa/artifacts_feature14_32/`.

The same notes are under each feature in `Aime_And_AI_Automation_Testing_A.md` (Features 27–32 added as Section 6).

**Rollup:** Pass 21 (cancel), 23, 26, 27, 31, 32. Skip 17 (no Run) and 20 (no Disconnect). Needs Work 14–16, 18, 19, 22, 24, 25, 28–30.

---

## 14 Cash Appraisal Ordered / Completed

**Status:** Needs Work

Buy-Cash To is the buyer plus-address. Sell-Cash To is the co-op plus-address. Sell-Cash Cc includes the assigned TC. I closed Complete this task without Send.

The plan body still reads like a note to me ("Email the buyer and ask if the appraisal has been ordered"). I will rewrite that as a question the buyer or co-op can answer.

I assigned the workspace TC (elf@cbstiles.com) so Cc would populate. I will not Send that plan. Later tests should use a plus-address TC, not a live office inbox.

Wizard: Appraisal On This Cash Deal? is on Contract Details after mortgage = No. Helper for Yes is "Appraisal follow-up tasks will be created."

**Countermeasure:** New copy for 265 / 267 / 271 / 275. Stop staffing live TCs on QA files.

## 15 Manual, named emails do not send

**Status:** Needs Work

Maple is Manual. Preview next run: This run would send 0 emails. I clicked Got it.

Buyer Welcome is not on the open task list. It sits under Handled by AI, so the Manual check is hard to do from Tasks.

**Countermeasure:** On Manual, keep named emails on the open list until a person sends or completes them.

## 16 Assisted, tap Send

**Status:** Needs Work

To is crazyaidev20500519+buyer@gmail.com. Give this back to the AI is not on the plan. I did not Send.

Same Handled by AI hiding as Feature 15.

**Countermeasure:** Same list placement. Send stays a person tap.

## 17 Autopilot, named emails may send once

**Status:** Skip Run

I did not confirm Run AI tasks. Preview said 0 emails. Pine is Assisted after seed so the hourly run would not fire welcomes.

**Countermeasure:** For a real Autopilot send check, pin one file whose Contacts are only plus-addresses I own, Preview, then Run only if the list is mine. Put the file back to Assisted after.

## 18 No buyer email, and no purchase agreement

**Status:** Needs Work

Cedar Buyer Welcome: "No Buyer contact with an email address is on this deal yet." To is empty. No guessed Gmail.

No-contract Order Title still offered Send & complete ("I'll email NoContract Title"). Body from the API says it will follow up with the contract. That is a send path with no purchase agreement on the file.

**Countermeasure:** Block Order Title / Loan Officer Welcome until the purchase agreement is on Documents. Needs You should show Upload document.

## 19 Inspection response reminder

**Status:** Needs Work (copy date only)

To is me. Body is a deadline nudge, no repair or negotiation language. The date printed as TBD.

Dual new file has both Inspection Response Reminder and both Inspection Negotiated rows (API). They are easy to miss on the open Tasks list.

**Countermeasure:** Print the inspection response date from the file. Keep the task findable on Tasks.

## 20 Mailbox down

**Status:** Skip

Disconnect is on Email & E-signature. I did not disconnect. Reconnect needs Google and I cannot finish that in this pass.

**Countermeasure:** Do this on a throwaway mailbox, then Connect and Test connection before leaving.

## 21 Prepared drafts and Send all ready

**Status:** Pass (cancel path)

Intelligence page is Email. Send all ready was idle. Deal Email on Maple showed Send all ready (1). I did not confirm it.

**Countermeasure:** None for cancel. If a Ready non-named draft appears, check To before any Send.

## 22 Blocked tasks

**Status:** Needs Work

Needs You did not show Add contact, Upload document, or Switch this deal off Manual on the first screen. Cedar's missing email is on the task plan ("add the contact on the Contacts tab").

Try now (this deal only) is Admin. I did not click it.

**Countermeasure:** Put the same recovery verbs on Needs You that the task plan already uses.

## 23 Inbound mail and money

**Status:** Pass

I filed four test messages on Maple (not a second live Gmail). All four sit on Email Inbox. Wire and banking did not become Ready.

**Countermeasure:** Keep money off Ready. A later pass can repeat from a second inbox I own.

## 24 Dates never move themselves

**Status:** Needs Work

Ask AI from the header did not open the pane in this pass. The closing date stayed October 15, 2026. I did not click Approve.

**Countermeasure:** Open the agent pane, propose the date change, Dismiss, confirm Timeline is unchanged.

## 25 Digest, Fine-tune, and Paused files

**Status:** Needs Work (Paused not pinned)

Overnight still holds Preview / Draft / Run / Digest. Fine-tune is a separate card. I did not pin Paused.

**Countermeasure:** Pin one test file Paused, Preview, confirm it is out of would-send, then set it Active again.

## 26 Words that should not appear

**Status:** Pass

I did not see library letters, written by AI, or Autopilot used as the Fast intake banner on the surfaces I opened.

**Countermeasure:** None.

## 27 Live IDs stay; Closing Gift is one row

**Status:** Pass

One Closing Gift on the buyer file and on the listing. Listing still has Schedule Pick Up of Sign and Lockbox and Change MLS Listing Status to Sold.

**Countermeasure:** None.

## 28 Dual agency (Both)

**Status:** Needs Work

API and Tasks: Buyer Welcome and Seller Welcome exist. Co-op Agent Welcome does not. One Order Title. Both inspection reminder and negotiated rows exist.

Deliver Title is two rows (Buyer and Seller). Deliver Utility Info is still on Dual. Request Testimonials is two rows.

**Countermeasure:** On Both, no co-op utility or co-op welcome. Keep one Deliver Title unless buyer and seller letters are required by the playbook; if they are, say that in the test step so it is not a Fail.

## 29 Order Title vs Confirm Title Order

**Status:** Needs Work (courtesy name)

710 (title ordered by Buyer) has Order Title, not Confirm. 720 (title ordered by Seller) has Confirm Title Order, not Order Title.

Confirm body has courtesy-order language. It greets the title rep as "courtesy to TitleOther" (the title person’s name). I will name the co-op there.

**Countermeasure:** Courtesy line uses the co-op agent. Still withhold personal-property and monetary addenda.

## 30 Deliver Utility Info on a listing

**Status:** Needs Work

To is the co-op plus-address, not the seller. The dialog still has a delivery leg that "needs a buyer on the file," so Send is blocked.

**Countermeasure:** Listing Deliver Utility Info is one letter to the co-op. Do not require a buyer client email.

## 31 Order Home Warranty is an internal reminder

**Status:** Pass

To is me. Cc can include the assigned TC. API body is an internal reminder to place the order and send the invoice to title and the co-op. I did not Send.

Listing task name is Confirm Home Warranty Order when the other side orders.

**Countermeasure:** Keep that name, or match the guideline label Confirm Home Warranty.

## 32 No seller Inspection Completed on new listings

**Status:** Pass

800 Test Utility Ln has no Inspection Completed. Dual has Inspection Completed on the Buyer only.

**Countermeasure:** None.
