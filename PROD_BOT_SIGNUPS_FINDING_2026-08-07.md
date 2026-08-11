# Production is full of bot registrations — reported as "garbled text"

Date: 2026-08-07
Author: Jan (with Claude)
Status: **Diagnosis confirmed. Detection + rate limiting implemented, uncommitted. Production cleanup NOT done — needs a decision (§6).**
Trigger: garbled-looking names on `/platform/registrations`, reported as a display defect.

---

## 1. The finding, in one line

The text is not garbled. **81 of the 87 accounts in the production database are
automated signups**, and the page is rendering their names exactly as stored.

---

## 2. Why it is not a rendering or decryption bug

Four independent checks, all pointing the same way:

| Check | Result |
|---|---|
| Does `users.full_name` decrypt? | **Yes — successfully.** It decrypts *to* `KswIlezfEhcDVtdHxSeAy`. That string is the stored plaintext, not ciphertext leaking through. |
| Is `tenants.name` encrypted at all? | **No.** It is read raw at `platform_registrations.py:310`, never passed through `_safe_pii` — yet it is equally garbled (`jNURTMruGIEpuvRZyko`). A decryption bug cannot garble a column that is never decrypted. |
| How many decryption failures in production? | **Zero**, across all 87 accounts. |
| Do good and bad rows share a key? | **Yes.** `Margaery Stone` and `Al Goforth` render correctly in the same table, same request, same Fernet key. |

A Fernet failure raises `InvalidToken`; it never yields plausible-looking
random text. And `_safe_pii` already turns a failure into `None`, which the UI
shows as "Unnamed" — not as garbage.

**Environment check.** The rows do not exist in dev (77 accounts, 0 decryption
failures, 0 random names) or stage (50 accounts, 0 random names). They exist
only in production.

---

## 3. What the production data actually looks like

87 accounts, 87 tenants — one workspace minted per signup.

| | Suspected automated | Plausibly genuine |
|---|---|---|
| Accounts | **81** | 6 |
| Ever signed in | **0** | — |
| Completed onboarding | **0** | — |
| Created a transaction | **0** | 2 |
| Arrived by invitation | 0 (all self sign-up) | — |
| Role | Agent ×81 | mixed |

- **All 81 landed in a single month**, 2026-07-03 → 2026-07-28.
- 37 use Gmail addresses with 3+ dots in the local part — the dot-insensitivity
  trick, where `j.u.mo.b.o.d.92.2@gmail.com` and `jumobod922@gmail.com` are one
  inbox. One mailbox, many "distinct" accounts.
- Names *and* workspace names are both random mixed-case tokens, which is why
  two differently-stored columns are garbled identically. One actor wrote both.

The six real accounts are Jake ×2, Al Goforth, Margaery Stone, and two early
test accounts.

**This costs money.** Each signup mints a tenant, a trial and a workspace.
Nothing so far has consumed AI credits (none signed in), but the trial and
tenant rows are real, and an automated account that *did* proceed to upload
documents would bill Textract and model calls against us.

---

## 4. Root cause

`POST /api/v1/users/register` had **no rate limiting, no captcha and no
proof-of-work**, while the codebase's own `build_rate_limiter` was already
guarding the marketing, help and advertising public endpoints. Registration —
the one public endpoint that creates durable, billable records — was the only
one left open.

---

## 5. What I implemented

### 5.1 The page now tells the truth (`app/services/signup_authenticity.py`)

A read-time classifier scoring four independent signals: a machine-looking
person name, a machine-looking workspace name, a dot-sprayed Gmail address, and
a name with no vowel rhythm. **Two signals is the threshold**, so no single
quirk of a real account is enough on its own.

Two rules govern it:

- **Flag, never hide.** Suspected rows stay in the default view, marked. Hiding
  one genuine prospect before a pitch costs far more than showing a labelled bot.
- **Say why.** Each row carries the signals that produced the flag, shown on
  hover, so the judgement is auditable rather than magic.

Surfaced as: a red "Suspected bot" chip per row; a `Real & automated / Real
people only / Suspected bots only` filter; `suspected_bot` + `bot_signals`
columns in the CSV; and the "Outside accounts" tile replaced by **"Real outside
signups"**, which excludes them. That tile mattered — unqualified, it read
**81** and looked like traction.

### 5.2 Registration is rate limited (`app/api/v1/users.py`)

5 attempts per minute per IP, using the existing limiter. Honestly labelled in
code as a speed bump: it is per-process (two ECS tasks = two buckets) and an
attacker rotating IPs walks past it. It belongs *with* the email-confirmation
gate, not instead of it.

### 5.3 Verification

- **Against the real production population**: 81 flagged, 6 not. **Zero false
  positives** — no flagged account had ever signed in, onboarded or created a
  transaction. The six genuine accounts score **0**, not 1, so this is a clean
  margin rather than a knife-edge.
- 27 classifier tests, pinned to the verbatim production strings in both
  directions, including `RE/MAX`, `eXp Realty`, `McDonald`, `O'Brien`, `Jean-Luc`
  and a real person on a dotted Gmail — none of which flag.
- Full backend suite: **1648 passed**. Frontend typecheck clean.

---

## 6. Not done — needs a decision

1. **Deleting the 81 accounts.** A destructive production operation; I did not
   run it. Recommended, but it should be a reviewed script with a dry-run, and
   it must decide what happens to their 81 tenant rows and trials.
2. **Email confirmation before a tenant is minted.** The real fix. Today
   registration creates a workspace before the address is proven. Requiring
   confirmation first makes a throwaway address worthless to a bot and would
   have prevented all 81. Bigger change — worth its own plan.
3. **Captcha (Turnstile/hCaptcha) on the signup form** if the pattern resumes
   after 1 and 2.

---

## 7. Two side findings, not fixed here

- **`last_login_at` is null for every production account**, including Jake, who
  has created a transaction and therefore certainly signed in. `touch_last_login`
  exists but is only called on the *password* login path (`auth_service.py:320`)
  — not on OAuth sign-in or refresh. Prod may also be running an image that
  predates it. Effect on this page: the Activity column understates engagement,
  and "Signed in, not onboarded" is currently unreachable in production. It does
  not affect the bot finding — those accounts have no activity by any measure.
- **Registration accepts any role, including Agent, with no verification**,
  which is how 81 accounts became Agents. Related to the existing role-autonomy
  findings.

---

## 8. What to tell Jake

He asked to be told when someone registers. Given §3, the honest version is:

> The signups you're seeing on the registrations page are almost all bots — 81
> of 87 accounts, all created in July, none of which ever signed in. It's a
> known pattern: automated scripts making throwaway Gmail addresses. It doesn't
> put customer data at risk, but it means the raw signup number isn't real
> traction. I've added detection so they're marked and filterable, and closed
> the hole that let them in. Real outside signups so far: **2** (you, and Al
> Goforth).

Do **not** report the raw count to the pitch battle committee as traction.
