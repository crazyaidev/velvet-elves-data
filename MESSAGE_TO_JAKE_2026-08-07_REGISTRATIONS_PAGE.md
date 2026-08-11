# Message to Jake — 2026-08-07

Draft for WhatsApp. Two versions: the short one is what I would send; the long
one is there if Jake asks for detail.

---

## Short version (send this)

> Hey Jake — the page for watching new registrations is done.
>
> It's under Platform › Registrations and it lists every account created across
> all workspaces: who they are, which workspace, their role, whether they
> signed up themselves or were invited by someone, when they registered, and —
> the useful part — whether they've actually done anything since (never signed
> in / signed in / finished onboarding / created a transaction). It defaults to
> hiding our own test accounts, so if a row shows up there, it's a real
> outsider. You can filter by date and activity, sort any column, search, and
> export to CSV.
>
> On the email alerts you asked about: rather than hard-coding addresses, I
> built a small settings page so you can add or remove recipients yourself —
> and a second list for our own test addresses, so our testing doesn't set off
> alerts. No code change or deploy needed to adjust either.
>
> One holdup: I can't deploy to production yet. The GitHub Actions runners have
> been down for a few hours, so the pipeline can't build or ship. Nothing wrong
> on our end — it's their outage. Everything's built, tested and waiting; I'll
> push it out the moment they're back, and I'll tell you when it's live.
>
> Two things I need from you when you get a chance:
> 1. The email address of the production account you created — I'll give it
>    platform admin so you can see this page yourself.
> 2. Who should get the alert emails? You, you and Audri, or all three of us?
>
> Until it's deployed I'm still watching production, so if anybody registers
> you'll hear it from me.

---

## Long version (only if he wants detail)

> Hey Jake — new-registration visibility is finished. Rundown:
>
> **Platform › Registrations** — every account created across every workspace,
> in one table:
> - who registered (name, email), their role, and which workspace
> - self sign-up vs invited, and who invited them — so you can tell a genuinely
>   new customer from a teammate someone added
> - when they registered
> - what they've actually done: never signed in, signed in, finished
>   onboarding, or created a transaction. That last part is the bit you'd want
>   for a committee "test drive" — it tells you whether someone poked around or
>   actually tried the product
>
> **Filtering out our own testing.** The default view is "Outside", which
> hides our test accounts, so anything listed there is a real outsider. You can
> switch to All (ours are tagged "Internal"), Founders, or Invited. There's
> also a date filter, an activity filter, sorting on every column, search, and
> CSV export.
>
> **Alerts.** You asked for an email when someone registers, and flagged that
> our own testing would drown it. Instead of hard-coding addresses in the code,
> there's a settings page (Registrations › Alerts) with two lists you control:
> who gets notified, and which addresses are ours and should stay quiet. Both
> take effect immediately — no deploy. The alert only ever fires in
> production, and only for accounts that aren't on the internal list.
>
> **What's blocking go-live.** GitHub Actions has been down for several hours,
> so the deploy pipeline can't build or ship anything. It's their outage, not
> our code. The work is finished and tested — 59 backend tests plus a full
> browser pass against 77 real accounts — and it goes out as soon as their
> service is back. I'll confirm when it's live in production.
>
> **What I need from you:**
> 1. The production account email you registered with, so I can grant platform
>    admin and you can open the page yourself.
> 2. Who receives the alerts — you, you + Audri, or all three of us? I'll seed
>    the list, and you can change it yourself afterwards.
> 3. If you and Audri have test accounts on production, send me those addresses
>    and I'll add them to the internal list so they don't trip the alert.
>
> Meanwhile I'm still watching production directly — if anyone registers before
> this ships, I'll tell you straight away.

---

## Notes for me (not for Jake)

- Do not say "deployed" or "live" until the pipeline actually runs. Right now
  the honest status is **built, tested, uncommitted, not deployed**.
- The GitHub Actions outage is the stated reason for the delay — confirm it is
  still down before sending, and if it has recovered, deploy first and send a
  different message.
- Outstanding from Jake since 2026-08-05: his production account email (Q3).
  Asking again here.
- Alert recipients (Q2) were never answered. The settings UI means this no
  longer blocks anything, but the list is empty until someone is named, so the
  alert is inert. Worth being explicit about that if he assumes it is already
  emailing him.
