# M9c — Scope → Google API methods

Source of truth: `app/services/email/gmail_provider.py` (`GMAIL_SCOPES`, `GOOGLE_CALENDAR_SCOPES`). Do not change Cloud Console to match this doc; this doc matches the code Google already reviewed.

## Gmail consent (`provider=gmail`)

Scopes:

- `openid`
- `https://www.googleapis.com/auth/userinfo.email`
- `https://www.googleapis.com/auth/userinfo.profile`
- `https://www.googleapis.com/auth/gmail.send` (sensitive)
- `https://www.googleapis.com/auth/gmail.readonly` (restricted)

Methods used in code (not a complete Google catalog):

| Method | Why |
| --- | --- |
| OpenID userinfo | Identify the connected mailbox |
| `users.messages.list` / `users.messages.get` | Inbound match after watch/history |
| `users.history.list` | Incremental sync |
| `users.watch` | Gmail push registration (renewed by the hourly EventBridge tick hitting `/api/v1/internal/schedules/tick` — **not** a daily dedicated “renew watch” job) |
| `users.getProfile` | History id / email address |
| `users.messages.send` | Approved reply only (`gmail.send`) |

The app does **not** request `gmail.modify`. It does not delete, label, or rewrite mailbox state.

## Calendar consent (`provider=google_calendar`) — separate OAuth row

Scopes:

- `openid`
- `https://www.googleapis.com/auth/userinfo.email`
- `https://www.googleapis.com/auth/calendar.events` (sensitive)

Methods: `calendars/primary/events` create/update for closing events. Distinct from Gmail so Calendar disconnect does not drop mail tokens.

PKCE is used on both authorize URLs.
