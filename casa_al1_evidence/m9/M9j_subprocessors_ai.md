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

There is **no** single control named “Improve the model for everyone.” Platform **Settings → Data controls** has four tabs. Only **Sharing** is the no-training evidence. Do not screenshot Visibility, Hosted tools, or Data retention for this claim.

1. Sign in at [platform.openai.com](https://platform.openai.com) as the Velvet Elves **API** org owner (the org that owns the live `OPENAI_API_KEY`). Not ChatGPT.com. The org name in the sidebar must be the production org, not a personal playground org.
2. Open **Settings → Data controls**, then click the **Sharing** tab. Direct: [https://platform.openai.com/settings/organization/data-controls](https://platform.openai.com/settings/organization/data-controls)
3. On **Sharing**, all three radios must be **Disabled** (API default is off unless someone opted in):
   - **Enable sharing of model feedback from the Platform** — Playground thumbs-down / chat feedback used to train models.
   - **Share evaluation and fine-tuning data with OpenAI** — eval/fine-tune prompts, completions, grading.
   - **Share inputs and outputs with OpenAI** — general API inputs/outputs used to improve services and models. This is the one that used to be described as “Improve the model.”
4. Click **Save** if you changed anything. Leave them Disabled.
5. Save a PNG that shows: sidebar org name, **Sharing** tab selected, all three **Disabled**, and the URL. Drop it here as `openai-data-controls.png`. No API keys in frame.

**Do not treat these other tabs as the training proof:**

| Tab | What it actually is |
| --- | --- |
| Visibility | Who inside the org can see Threads / Usage / Logs. Not training. |
| Hosted tools | Whether Responses API tools (MCP, web search, file search, image gen, code interpreter) are allowed. Not training. |
| Data retention | **Your** audit log + API call logging in the OpenAI dashboard (`Disabled` / `Enabled per call` / `Enabled for all projects`). Not Zero Data Retention. We have no ZDR contract — do not claim ZDR even if logging is disabled. |

Anthropic: API Commercial Terms already say no training on Customer Content. Screenshot only if the lab asks.

**Captured 24 Aug 2026:** `openai-data-controls.png` from **Velvetelves Organization**, Sharing tab, all three radios **Disabled**. No API keys in frame. Do not treat the remaining “eligible for free daily usage on traffic shared with OpenAI” banner as enrollment; sharing is off. Do not claim ZDR.
