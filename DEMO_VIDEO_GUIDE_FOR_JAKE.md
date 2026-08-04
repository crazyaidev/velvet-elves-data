# Recording the Google Demo Video

**Who this is for:** Jake
**Written by:** Jan
**Date:** August 3, 2026
**Record on:** https://app.velvetelves.com (the live site, not stage)

---

## What this is

Google needs to watch someone actually use the app before they'll approve our Gmail connection. It's the last thing standing between us and submitting. Everything else on the Google side is finished.

You've done these before so I won't tell you how to record. What I have written out is exactly where to click and what to say, because Google is checking specific things and it's easy to miss one and have to redo it.

I'd rather you record it than me. A reviewer watching the broker explain his own product is more convincing than watching a developer click through screens.

Aim for 6 to 10 minutes.

## What Google is actually checking

Three things, and that's genuinely it:

1. That the Google permission screen is shown clearly enough to read.
2. That we actually use each permission for something real, rather than just claiming we do.
3. That a person is in control, specifically that the AI isn't emailing clients on its own.

Number three is the one that sinks submissions. We'll be explicit about it twice.

## Two things to get right before you start

**Record on the live site, `app.velvetelves.com`.** Not stage. Stage runs on a separate Google project with a different set of credentials, so a video recorded there shows a permission screen that doesn't match what we're submitting. That's a straight rejection and it's the one mistake that would cost us a full re-record.

**Use a throwaway Gmail for the mailbox you connect**, not your own. You'll be showing the inbox and sent folder on camera.

Everything else is the usual: incognito or signed out of your other Google accounts so the account picker doesn't appear mid-take, tabs closed, notifications off.

---

## The recording, step by step

Rough words are below each step. Don't read them out, they'll sound stiff. Just hit the point.

### 1. The website (about 45 seconds)

Go to **velvetelves.com**, then **velvetelves.com/privacy**. Scroll to the section about Google data and hold there a few seconds so it's readable.

*Roughly:* "This is Velvet Elves, a transaction coordination platform for real estate brokerages. Here's our privacy policy, and this section covers exactly what we do with data from a user's Google account."

### 2. Sign in (about 20 seconds)

Go to **app.velvetelves.com** and sign in. You'll land on **/dashboard**.

*Roughly:* "Signing in as an agent. This is where I'd see my active transactions."

Keep it short.

### 3. Connect Gmail (about 90 seconds), the critical one

**Where:** left sidebar, bottom → **Settings** → the **Email & E-signature** card.
Direct link if it's faster: **app.velvetelves.com/settings/connections**

Gmail shows as not connected. Click **Connect**.

Google's window opens and you'll hit **"Google hasn't verified this app."** That's expected, it's there precisely because we haven't been approved yet. Click **Advanced** at the bottom left, then the continue link. **Leave this in the video.** Editing it out looks evasive and they know it should be there.

Then the permission screen appears. **Slow right down here.** This is the single most important shot in the video. Let it sit. If the permissions don't all fit on screen, scroll slowly so every line is readable.

*Roughly:* "Here's what we're asking for. Permission to read incoming email so we can match it to the right transaction, and permission to send email, but only when I approve it. I'll allow that."

Come back to the app, show it now says **Connected** with the address, then click **Test connection** and show the result.

### 4. An email arrives (about 2 minutes)

Send an email from another account to the mailbox you just connected. Mention the property address of one of the test deals in the subject or body, so it has something to match on.

Then show it landing, in this order:

1. Sidebar → **Intelligence** group → **Email** (direct: **app.velvetelves.com/ai-emails**), on the **Inbox** tab
2. Point out it's been filed against the right transaction
3. Open that deal from **Transactions** and show the same message on the deal's **Email** tab

*Roughly:* "A message just came in from the title company. The system read it, worked out which transaction it belongs to, and filed it against that deal on its own. That's what the read permission is for. Without it we'd have no way of knowing this email was about this property."

### 5. The draft, and who's in control (about 90 seconds)

Still on **/ai-emails**, switch to the **Outbox** tab and open the reply the AI has prepared. Show the recipient, subject and body.

**This is the part that matters most.**

*Roughly:* "The system has written a draft reply for me. It has not sent anything. Nothing goes to a client unless I read it and approve it. I can edit it first if I want."

Then actually click **Edit** and change a word or two, so they see you controlling the final text.

### 6. Send it (about 60 seconds)

Click **Approve & send**.

Then switch to the connected Gmail account in another tab and show the message sitting in **Sent**.

*Roughly:* "Now I've approved it, it's gone out from my own address, and there it is in my sent items. That's the send permission. One message at a time, only when I click approve. We never send bulk email and nothing goes out automatically."

### 7. Calendar (about 60 seconds)

**Where:** sidebar → **Workflow** group → **Closing Calendar** (direct: **app.velvetelves.com/calendar**)

Open the **Connect calendar** menu, top right, and choose **Google Calendar**.

You'll get a **second Google permission screen** here. Calendar is a separate approval from Gmail, so show this one properly too, same as before.

Then click **Add my closings**. Switch to Google Calendar in another tab and show the closing date sitting in it.

*Roughly:* "I can connect my calendar too, and it puts my closing dates straight in, so I'm not copying dates across by hand."

### 8. Disconnect (about 45 seconds)

Back to **Settings → Email & E-signature** (**/settings/connections**) and click **Disconnect** on Gmail.

A confirmation box appears explaining what disconnecting does. **Show that box**, then confirm.

*Roughly:* "If I ever want to cut off access, I disconnect right here and the app stops touching my email. I can also remove it from my Google account settings."

### 9. Close out (about 20 seconds)

*Roughly:* "On how we handle this data: we only use it to run the features you've just seen. We don't sell it, we don't use it for advertising, and we don't use it to train AI models. Anyone can disconnect at any time and ask us to delete their data."

Stop recording.

---

## Quick reference

| Step | Where | Direct link |
|---|---|---|
| Sign in | | app.velvetelves.com |
| Connect / disconnect Gmail | Settings → Email & E-signature | /settings/connections |
| Inbox and drafts | Intelligence → Email | /ai-emails |
| One deal's mail | Transactions → open deal → Email tab | /transactions |
| Calendar | Workflow → Closing Calendar | /calendar |

Buttons you'll be clicking, by name: **Connect**, **Test connection**, **Approve & send**, **Edit**, **Connect calendar**, **Add my closings**, **Disconnect**.

## What would get us rejected

- **Saying the AI sends emails on its own.** Always "it writes a draft and I approve it." This is the big one.
- **Recording on stage instead of the live site.**
- **Rushing past the permission screen**, or it being too small to read.
- **Any real client information on screen**, including in background tabs.
- **Cutting out the "Google hasn't verified this app" warning.**
- Background music.

## When you're done

Upload to YouTube as **Unlisted**. Not Private, or the reviewer can't open it.

Then open the link in an incognito window where you're not signed into YouTube. If it plays there, we're fine.

Send me the link and I'll put together the submission package, which is the last step before this goes to Google.

If something small goes wrong, don't redo the whole thing. Tell me what happened and we'll work out whether it actually matters. Usually it doesn't.
