# Help Center — Local Testing Guide

Date: 2026-06-25

This walks through testing the whole help center locally, end to end, entirely
through the UI. Three pieces run together:

1. Backend (`velvet-elves-backend`) — serves the authoring + public help APIs.
2. Admin app (`velvet-elves-frontend`) — where platform admins write content.
3. Help website (`velvet-elves-help-center`) — the public site readers see.

---

## 0. One-time setup (a developer does this once)

- The tester's account must have the platform-admin flag. There is no UI for
  this by design; a developer sets `users.is_platform_admin = true` for the
  tester's user (the same way other platform tools are granted).
- Enable the help center flag for the public API/website. In the backend `.env`:

  ```
  VE_HELP_CENTER_V1=true
  ```

- (Optional) For the AI answers in the support widget, a real `OPENAI_API_KEY`
  (or `ANTHROPIC_API_KEY` with `AI_PROVIDER=anthropic`) must be set. Without a
  key, the support widget still works — it returns the best-matching articles as
  citations (the "retrieval" path). Either way is fully testable.

CORS for the website's dev port (`5180`) is already allowed by default.

---

## 1. Start the three apps

In three terminals:

```bash
# 1. Backend  (from velvet-elves-backend)
uvicorn app.main:app --reload --port 8000

# 2. Admin app  (from velvet-elves-frontend)
npm run dev            # http://localhost:5173

# 3. Help website  (from velvet-elves-help-center)
npm install            # first time only
npm run dev            # http://localhost:5180
```

The website reads `VITE_HELP_API_BASE_URL` from its `.env` (defaults to
`http://localhost:8000`).

### Shortcut: test the website UI with no backend (mock data)

If you only want to test the **website's** look and flows and don't want to run
the backend or author content yet, use the opt-in mock mode: open
`http://localhost:5180/?mock=1`. The site then serves built-in sample
collections/articles (and search, related, feedback, and the Ask AI widget all
work against the mock), with a small **Mock data** badge bottom-left. Append
`?mock=0` to turn it off. Mock mode is OFF by default and never appears on the
real site. Steps 2 and 4 below (real authoring + the feedback loop) still need
the backend.

---

## 2. Author content (admin app, as a platform admin)

1. Sign in at `http://localhost:5173`. In the left sidebar, open the **Platform**
   group and click **Help center**. (If you don't see it, your account isn't a
   platform admin yet — see step 0.)
2. Click **New collection**. Pick an icon, type a name (e.g. *Getting Started*)
   and a one-line description, set it **Published**, and **Create collection**.
   Expect the new card in the table.
3. Click the collection row to open its articles. Click **New article** — it
   opens the editor on a fresh draft.
4. Type a **Title** (watch the slug fill in). Write a few lines in the body
   using the toolbar buttons (**Bold**, **Heading**, **bullet list**). Drag an
   image into the body, or click the image button to upload one. The **right
   pane updates live** — that's exactly what readers will see.
5. Add an **Excerpt** (one or two sentences; it powers search snippets).
6. Click **Save**, then flip the status to **Published** (top-right). You can
   also click **Preview** to open the in-app preview, and **History** to view
   and restore earlier saved versions.

---

## 3. Read it on the public site

1. Open `http://localhost:5180`. Expect the navy hero, the search box, and your
   published collection card with its article count.
2. Open the collection, then the article. Expect the breadcrumb
   (*All Collections › … › …*), the date, the rendered body, and — if the
   article has two or more headings — a **table of contents** on the right that
   highlights the section as you scroll.
3. If you set up related articles, follow a **Related articles** link.
4. **Search**: type a phrase from the article in the header search. Expect a
   results page with the title + a snippet; click it to open the article.
5. **Feedback**: under *Did this answer your question?*, click a face. A 👍 sends
   immediately; 😐/👎 reveal an optional comment box and a **Send feedback**
   button. Expect a thank-you state.
6. **Support widget** (only if the chat provider is set to *Ask AI* on the admin
   *Help center settings* page): click the green bubble bottom-right, type a
   question, and send. Expect an answer plus **numbered source chips** that link
   into the matching articles.

---

## 4. Close the loop (back in the admin app)

1. In the Help center, click **Feedback**. Expect the reaction you submitted to
   appear against that article, with the helpful-percentage and 👍/😐/👎 counts.

---

## 5. Settings to try

On **Help center → Settings** (admin app) you can set, with no redeploy:

- **Site title** — shown in the website hero and footer.
- **Book a Call URL** — adds a *Book a Call* link to the website header/footer.
- **Support email** — powers the *Email us* link.
- **Chat provider** — *None* (no widget), *Ask AI* (the in-house widget above),
  or *Intercom* / *Crisp* (embeds that messenger using the **Chat app ID**).

After saving, refresh the website to see the change.

---

## 6. What "good" looks like

- A platform admin can create, write, publish, reorder, and delete collections
  and articles using only the mouse and minimal typing.
- A non-platform-admin user cannot see the Help center nav and is blocked from
  the authoring API.
- The public site shows only **published** content; drafts never appear.
- Search returns ranked title + snippet results.
- Feedback submitted on the site shows up on the admin Feedback page.
- If any step required editing code, a config file, or the database directly,
  that is a bug to report — the whole flow is designed to be UI-only.
