# Jake's Requirements: New-User Registration Visibility (Pitch Battle)

Date: 2026-08-05
Author: Jan (with Claude)
Source: WhatsApp chat with Jake, 2026-08-05, 1:03 PM – 1:35 PM. `rich` in the transcript is me (Jan).
Status: **REQUIREMENTS ONLY.** Nothing built yet. This document records what Jake asked for and what I committed to, so the build can start from an agreed scope.

---

## 1. Why Jake raised this

Velvet Elves registered for a pitch battle. Jake believes the selection committee will "take a 'test drive'" of the product before picking competitors, and he needs to know if and when that happens.

> "We think that the pitch battle we registered for is going to try to get in and use our product and we just need to know if that's the case or not."

Two things follow from that motive and both matter for how this gets built:

- The signal Jake needs is **an outsider touching the product**, not a headcount metric. A notification that fires for our own test accounts does not answer his question.
- It is **time-boxed and urgent** — it only helps if it is live before the committee looks.

---

## 2. What Jake asked for

| # | Requirement | Jake's words | Notes |
|---|---|---|---|
| R1 | Jake (and Audri) must be able to see whether anybody registers to try the product | "is there anyway that you can either give us an admin login or just monitor to see if anybody registers" | Jake offered either option: give them access, or I watch it for them |
| R2 | Coverage must include **account creation / registered users**, not just the waitlist | "What about account creation (or users registered)?" | My first answer only covered the waitlist page; Jake corrected the scope. This is the core of the request |
| R3 | Delivery mechanism is an **email alert on new user registration** | "Can you set it up to just send an email out when a new new user registers?" | Push, not pull. Jake does not want to have to go look |
| R4 | The alert must not be drowned in noise from our own testing | "Or would that be stupid because we keep testing and we use new accounts for that?" | Jake raised this objection himself and left it to me to solve |
| R5 | Distinguish/flag the kind of registration so a real signup stands out | "Could we identify it as a new admin user? I don't know." | Jake was explicitly unsure of the mechanism — see open question Q1 |
| R6 | Keep it minimal — this must not become a project | "we don't need a whole UI right now… I'm just trying to keep it minimalistic so we can keep our eye on the prize" | Jake killed my proposed monitoring UI before I built it |
| R7 | Priority stays on tasks and production readiness | "The most important thing is building out the tasks and getting all that stuff ready so we can go production as soon as possible" | This work is subordinate to the task-engine / go-live work. It gets the smallest slice of effort that satisfies R1-R5 |

## 3. What I committed to in reply

Jake did not push back on any of these, so they are in scope:

| # | Commitment |
|---|---|
| C1 | The notification is **production-only**. Local, dev, and stage signups never notify |
| C2 | The email carries **email address, role, workspace, and signup time** |
| C3 | **Known test accounts and domains are excluded** where possible, so our own testing stays quiet (this is the answer to R4) |
| C4 | No monitoring UI is built now (withdrawn per R6) |
| C5 | Jake gets **platform admin permission** on his production account, giving him the existing Platform > Waitlist page — pending Jake sending me the email address he registered with |

---

## 4. Explicitly out of scope

- **A registration/users monitoring UI.** I offered one ("I'll show you the completed UI tomorrow morning") and Jake declined it. Do not build it. It can come back later as its own item.
- **Anything beyond signup visibility.** No analytics, no funnel reporting, no dashboards.
- **Changes to the waitlist feature.** It already works; the Platform > Waitlist page exists and currently holds one row, `ngozi.evalie@minafter.com`, which I created as a test entry.

---

## 5. Open questions for Jake

| # | Question | Why it blocks / matters |
|---|---|---|
| Q1 | R5 — "identify it as a new admin user": do you mean (a) label each alert as internal-test vs. outside-signup, (b) only notify for the first user of a brand-new workspace (the founder/owner, i.e. a genuinely new customer rather than an invited teammate), or (c) something else? | Changes what triggers the email. My working assumption if you don't answer: **(b) plus (a)** — notify on a new workspace founder, and label anything matching a known test account so you can ignore it at a glance |
| Q2 | Who receives the alert? Just you, or you + Audri + me? | Working assumption: you, Audri, and me |
| Q3 | Which production account email should get platform admin (C5)? | You have not sent it yet. Nothing else is blocked by this, but you can't see the waitlist page until you do |
| Q4 | One email per registration, or a batched digest if several land at once? | Working assumption: one email per registration — volume is near zero today, so a digest would only add delay |

---

## 6. Acceptance criteria

This is done when, in production:

1. A new user registering triggers an email to the recipients in Q2 within minutes of signup.
2. The email states the registrant's email address, role, workspace, and signup time (C2).
3. A signup on local/dev/stage triggers nothing (C1).
4. A signup from a known internal test account or domain either sends nothing or is clearly marked as internal (C3/R4).
5. No new page, nav entry, or admin screen has been added (R6/C4).
6. Jake can reach Platform > Waitlist on his production account (C5), once he provides the address in Q3.
