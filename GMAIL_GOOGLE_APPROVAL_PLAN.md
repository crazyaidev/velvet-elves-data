# Google's Approval for the Gmail Connection - Plan and Status

**The question this answers:** "What has to happen before real users can connect their Gmail, and what do you need from me?"
**In one sentence:** The Gmail features are built and working in testing, but before the public can use them Google has to review and approve us; that review is the one step on the launch path we cannot rush, so this document lays out the plan, what I handle, and the four things I need from you.
**Written by:** Jan
**Date:** July 6, 2026

---

## Why Google has to approve us at all

When one of our users clicks Connect Gmail, they are letting Velvet Elves read the mail arriving in their inbox and send replies from their own address. Google treats that as the most sensitive kind of access an app can ask for, and honestly they are right to. Any app that asks for it goes through a manual review: real people at Google check who we are, what exactly we do with the mail, whether our public privacy policy says the same thing, and whether we ask for more access than we actually use.

Until we pass that review, two things are true:

- Anyone connecting Gmail first sees a full-screen Google warning saying the app is unverified. It looks alarming, because it is designed to.
- Google caps us at 100 connected users in total.

Both are fine for testing. Neither is acceptable for launch, and that is the entire reason for this plan.

One piece of good news before anything else: your team's testing is not blocked by any of this. Test accounts keep working exactly as they do today while the review runs in the background.

---

## Where we stand today

### The feature itself: done and tested

So you know what Google will actually be looking at, this is the Gmail feature as it exists right now:

- A user connects their own Gmail in Settings, through Google's normal sign-in screen.
- Incoming mail about a deal shows up on that deal's page automatically; the system matches each message to the right transaction.
- The AI drafts replies, and the drafts wait in the review queue. Nothing is sent unless a person clicks Approve & Send or edits the draft first. There is no path where the AI emails anyone on its own, and that fact is one of our strongest cards in this review.
- Approved replies go out from the user's own Gmail address and are logged on the deal.
- Disconnecting is one click and genuinely stops all access.
- Everything sensitive we store, like sign-in tokens and the connected address, is encrypted.

### The Google side: plumbing done, paperwork not started

The Google Cloud project you created in March ("Velvet Elves") is in good shape. I went through it again today: the right Google services are switched on, and the pipeline that tells our production server "new mail just arrived" is set up and running against the live server address. You, Audri, and I all have full access to the project.

What has not happened yet is the approval process itself. Nothing has been submitted to Google, and a few things have to be in place before it can be. That gap is what the plan below closes.

---

## About the project living under your personal Google account

You created the project with your personal Google account and invited me in, which was exactly the right way to get moving. Two things are worth knowing about that setup.

First, it does not block the approval. Google reviews the app and the website, not the kind of account that owns the project. Apps get approved out of personally owned projects all the time, so we can proceed as we are.

Second, it is still a risk worth fixing, just not a Google one. Right now the keys to our entire email system sit inside one personal Gmail login. If that account were ever locked, lost, or compromised, the email integration goes down with it, and a personal account has no company-level way to recover. The clean fix is a Google Workspace subscription for velvetelves.com, which costs about eight dollars a month for a single seat and gives the company its own accounts that the project can live under. Moving the project is easier before we submit than after, so I would like your call on this in the next week or two. My recommendation is to do it; if you would rather not add a subscription right now, we submit as we are and revisit later, and I will say so in the plan without hard feelings either way.

---

## The plan, step by step

### Step 1 - I trim the permissions we ask for (this week)

The single most common reason Google rejects an app is asking for more access than it uses. We currently ask for three kinds of Gmail access, and I went through our code line by line this week: we only ever use two of them, reading incoming mail and sending approved replies. The third, the ability to move or modify messages inside the mailbox, is never used anywhere. I am removing it before we submit. This one change removes Google's most likely objection before they can make it.

### Step 2 - I finish the settings in the Google project

A few housekeeping items on my list: updating the return addresses used during Google sign-in (they still point at our old server address from before the domain move), tidying the app's public listing details, and making what we ask for in the project match the trimmed permissions from Step 1 exactly. The same review also covers our calendar connection, since it rides on the same Google setup, so I will fold that in rather than leave it showing warnings after Gmail is approved.

### Step 3 - Public pages: I write them, you confirm two facts

Google's reviewers open our public website and check that it plainly tells users what we do with their Gmail data. Our current privacy page only covers the marketing site's email signup form, because that is all the website itself does. I will write the missing pieces: a privacy policy that covers the app and its Gmail use in plain language, a page explaining how users can disconnect and have their data deleted, and a support contact page.

This is where I need you. For the policy to be real I need the company's legal name and state, and I need a support email address, something like support@velvetelves.com, that a person actually reads. Those two answers are the only outside dependency in the first half of this plan.

### Step 4 - I record the demo video

Google requires a short video showing exactly how the app uses each permission: connecting Gmail, a message arriving and landing on the right deal, the AI drafting a reply, a human approving it, the send, and the disconnect. I will record this with test accounts and staged deals, no real client data anywhere in frame. It usually runs under ten minutes and the reviewers follow it closely, so I will script it around the human-approval point.

### Step 5 - I submit, and we enter the waiting phase

Once steps 1 through 4 are done I submit everything through Google's verification process and the clock starts. Reviews of email access typically take a few weeks. During this period Google emails questions, and the single biggest thing we control is answering them fast; I will respond within one business day, every time.

One practical point for you: because the project is owned by your account, some of Google's emails may land in your personal inbox rather than mine. If anything from Google shows up, forward it to me the same day. A reviewer question sitting unread for a week is the most common self-inflicted delay there is.

### Step 6 - The possible extra round: a security audit

For apps that read Gmail, Google sometimes requires an independent security assessment on top of the regular review. We may or may not be asked; it depends on their classification of us. If they do ask, it adds a few weeks and an outside cost, typically somewhere from a few hundred to a few thousand dollars depending on which assessment path they assign. I am preparing the written security documentation in advance so that if the request comes, we respond immediately instead of scrambling. If it comes with a price tag, I will bring you exact numbers before committing to anything.

### Step 7 - Approval

When Google approves us, the warning screen disappears, the 100-user cap lifts, and the Gmail connection is simply available to every customer. I will run a final end-to-end check on the live system and then this whole topic is behind us, apart from a light annual re-check Google requires, which I will handle when it comes up.

---

## What I need from you

Everything above is mine to do except these four items:

1. **The company's legal name and state**, for the privacy policy. Needed within the next two weeks so Step 3 does not stall.
2. **A support email address that someone reads**, ideally support@velvetelves.com. Also needed for Step 3, and Google expects it to stay monitored.
3. **A yes or no on Google Workspace** for velvetelves.com (about $8 a month, my recommendation is yes). Needed in the next week or two, because moving the project is much easier before submission than after.
4. **During the review: forward me any email from Google the day it arrives**, and please do not change anything inside the Google Cloud project while the review is running. Even small settings changes can send a review back to the start of the line.

---

## How this affects the launch date

The honest picture: building things is not the long pole here, waiting is. From the day I submit, expect roughly three to six weeks to approval, and up to about eight if the security audit is required. That window cannot be bought down or talked down; it moves at Google's pace.

What we can control is everything around it:

- **Submit early and run it in parallel.** The review does not block any other work. Payments, the remaining product work, and your team's testing all continue while Google deliberates. Gmail for the public is the only thing waiting on them.
- **Remove the known objections before submitting.** The three classic causes of rejection are asking for unused permissions, a privacy policy that never mentions Gmail, and slow replies to reviewer questions. Steps 1, 3, and 5 exist precisely to take each one off the table.
- **Keep testing on test accounts.** Nothing about the review limits what we already do today, so the test window you and the team are running continues untouched.

Put together: if I get the two answers in Step 3 from you inside the next two weeks, I expect to submit before the end of July, which puts approval between mid August and mid September depending on whether the audit round happens. If Gmail approval turns out to be the last thing holding up launch, we also have the option of launching everything else first and switching Gmail on for customers the day approval lands. I will flag it early if it starts to look that way.

---

## Timeline at a glance

| When | What happens | Who |
|---|---|---|
| This week | Unused permission removed, project settings finished | Me |
| Next 2 weeks | Privacy and support pages written and published | Me, after your two answers |
| Next 2 weeks | Workspace decision, if we are moving the project | You, then me |
| Mid to late July | Demo video recorded, everything submitted to Google | Me |
| Weeks 3 to 6 after submitting | Review runs; we answer questions same-day | Me, with you forwarding any Google emails |
| If audit is required | A few extra weeks; I bring you costs before we commit | Me |
| On approval | Warning gone, user cap lifted, final live check, Gmail ready for launch | Me |
