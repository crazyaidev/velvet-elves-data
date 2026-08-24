# M9j — Subprocessors and AI no-training

Public list (https://velvetelves.com/privacy, Google-data + sharing sections):

| Provider | Use | Google user data? |
| --- | --- | --- |
| Amazon Web Services | Host API (ECS), S3, Textract | Indirect (encrypted app DB is not on Google). Textract is **documents**, not Gmail. |
| Supabase | Auth, Postgres, Storage | Stores Fernet ciphertext of Google tokens and app records |
| Stripe | Payments | No Gmail |
| SendGrid | Transactional mail (invites, etc.) | Not Gmail API send |
| OpenAI or Anthropic | Drafts, triage, contract parse | **Yes** — the message/thread snippet needed for that feature, not a mailbox dump |
| Google APIs | Gmail + Calendar for the connected account | Yes |

Limited Use language is already on the privacy page (no ads, no sale, no creditworthiness, no training generalized/foundation models).

## AWS AI

**Live 20 Aug 2026:** Organizations `AISERVICES_OPT_OUT_POLICY` on org root; policy `velvet-elves-ai-services-opt-out` (`p-90qm6ijnvl`). Textract opted out.

## OpenAI / Anthropic

Privacy copy: providers are prohibited from training on our data. API terms default to no training. Code does not set `store=true`. Prod `OPENAI_ADMIN_API_KEY` is **empty** (checked 22 Aug 2026), so this cannot be pulled from Admin API — **dashboard screenshot only**.

### Capture (owner / org admin on the production OpenAI org)

1. Sign in at [platform.openai.com](https://platform.openai.com) as the Velvet Elves API org owner (the org that owns the live `OPENAI_API_KEY`, not ChatGPT.com).
2. Open **Settings → Organization → Data controls**. Direct: [https://platform.openai.com/settings/organization/data-controls](https://platform.openai.com/settings/organization/data-controls)
3. Confirm **Improve the model for everyone** (or equivalent “share data to train”) is **off**. Do not turn on Zero Data Retention unless we actually have that contract — we do not claim ZDR.
4. Save a PNG that shows the org name, the toggle/state, and the URL/date. Drop it here as `openai-data-controls.png` (no API keys in frame).
5. Anthropic: API Commercial Terms already say no training on Customer Content. Screenshot only if the lab asks.

Until that PNG is in this folder, M9j is not lab-complete.
