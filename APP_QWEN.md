# app_qwen.py — Qwen Configuration Reference

## Introduction

`app_qwen.py` is a standalone Streamlit app that runs the same pipeline as
`app_enhanced.py`, configured to use Qwen models for its text agents.
Vision uses the platform default (Llama). Both apps run independently.
Neither modifies the other.

```bash
streamlit run app_qwen.py
```

This document describes the configuration: which models each agent uses,
the token budgets applied, and why they differ from the default app.

## Why this configuration exists

Different Groq accounts carry different per-model rate limits. On some
accounts, Qwen's text model has a lower tokens-per-minute (TPM) ceiling
than Llama models. `app_qwen.py` exists for that case: its text agents use
Qwen, with request sizes tuned to stay within a lower TPM budget.

Qwen's text model is also a reasoning model. It generates an internal
chain-of-thought before producing its answer. This reasoning step consumes
additional tokens beyond the visible output, and can be disabled per
request. `app_qwen.py` disables it, which reduces both token consumption
and output variance.

Vision uses the platform default (Llama) rather than Qwen's vision model.
Qwen's vision model has shown repeated server-side capacity outages on
this account, independent of token budget or image size — a reliability
issue, not a rate-limit issue, so a smaller token budget would not resolve
it.

## Model configuration

| Agent | Model |
|---|---|
| Vision / Product | `config.PRODUCT_MODEL` (Llama) |
| Research | `qwen/qwen3-32b` |
| Marketing Strategy | `qwen/qwen3-32b` |
| Content Calendar | `qwen/qwen3-32b` |
| Variants | `qwen/qwen3-32b` |
| Compliance | `qwen/qwen3-32b` |
| Video | `config.DEFAULT_MODEL` (Llama) — the video agent produces a storyboard only, no rendered video, so it is left on the platform default |
| Report | `qwen/qwen3-32b` |

Reasoning is disabled automatically for any model whose name contains
`"qwen"`, via `reasoning_effort="none"` in `tools/groq_client.py`. If a
model rejects this parameter, the request is retried without it. This
applies to the text agents only, since vision runs on Llama.

## Token budgets

Defined at the top of `app_qwen.py`:

```python
VISION_MAX_TOKENS = 700
RESEARCH_SETTINGS = {"num_predict": 1500}
RESEARCH_MAX_PRICE_SOURCES = 5
RESEARCH_MAX_COMPETITOR_SOURCES = 3
MARKETING_SETTINGS = {"num_predict": 900}
CONTENT_MAX_TOKENS = 2000
VARIANT_SETTINGS = {"num_predict": 1200}
COMPLIANCE_SETTINGS = {"num_predict": 1200}
REPORT_SETTINGS = {"num_predict": 1200}
REPORT_SECTION_MAX_CHARS = 300
```

These are lower than `app_enhanced.py`'s defaults (for example, research is
4000 there, content calendar is 4096, report is 3500). The tradeoff is more
concise output in exchange for staying within a smaller rate limit.
`VISION_MAX_TOKENS` applies to the vision call regardless of provider; it
is unrelated to the Qwen rate-limit budgets, since vision runs on Llama.

Every agent function accepts these values as parameters — either a
`settings_overrides` dict or a `max_completion_tokens` argument, depending
on the agent. This parameter support lives in the agent modules themselves,
so `app_qwen.py` only needs to supply values, not duplicate logic.

**Research evidence.** `research_market()` accepts `max_price_sources` and
`max_competitor_sources`. When set, only the top N sources by confidence
score are included in the model prompt. The full evidence list is still
returned in the result and shown in the UI — the cap applies only to what
the model reads.

**Report input.** The report prompt combines the system prompt (about
2,100 tokens on its own) with every prior stage's output. Two layers of
size control apply:

1. `report_agent.py` strips bookkeeping fields (`data_sources`, `metadata`,
   `evidence`, `strategy_score`) from every input before building the
   prompt. This applies in both apps.
2. `app_qwen.py` additionally caps each input section to
   `REPORT_SECTION_MAX_CHARS` characters via `_condense_for_report()`.

## Agent reference

| Agent | Input | Output |
|---|---|---|
| Vision / Product | Text description, optional photo | `product_name, brand, category, subcategory, product_type, colors, materials, features, design_style, shape, surface_finish, packaging, visible_text, visible_logos` |
| Research | Product output | `executive_summary, market_context, audience_persona, customer_psychology, competitive_analysis, product_insight, platform_strategy, decision, action_items, evidence, data_sources` |
| Marketing Strategy | Product output, Research output, business constraints | `executive_strategy, stp_analysis, swot_analysis, pricing_strategy, go_to_market_strategy, channel_strategy, content_strategy, campaign_strategy, budget_strategy, kpi_framework, risk_management, data_sources, strategy_score` |
| Content Calendar | Marketing output | `campaign_name, days[]` (platform, format, hook, caption, hashtags, CTA per day), `generated_at, model_used` |
| Variants | Marketing output, Content Calendar output | `variant_a/b/c` (angle, hook, body, CTA), `data_sources` |
| Compliance | Marketing output, Variants output | `variant_a/b/c` (safe_campaign_text, compliance_flags, explanation_of_modifications), `data_sources` |
| Video | Product, Marketing, Content outputs | `storyboard, scene_prompts, video_paths, final_video, is_placeholder: true` |
| Report | Product, Research, Marketing (required); Variants, Compliance, Content (optional) | Full report as JSON, plus `narrative_report` (plain text) |

The pipeline order is: Product → Research → Marketing Strategy → Content
Calendar → Variants → Compliance → Video → Report. Variants takes the
Content Calendar's output as input so its ad hooks stay distinct from, and
consistent with, what is already scheduled.

## Report output

`generate_report()` returns the structured JSON report and a
`narrative_report` field: a plain-English rendering of the same content,
built from the JSON without a second model call. The UI presents both in
separate tabs, and a download button exports `narrative_report` as a `.txt`
file. `video` is not part of the report input.

## Comparison with app_enhanced.py

| | app_enhanced.py | app_qwen.py |
|---|---|---|
| Vision model | `meta-llama/llama-4-scout-17b-16e-instruct` | Same (`config.PRODUCT_MODEL`) |
| Text model | `llama-3.3-70b-versatile` | `qwen/qwen3-32b` |
| Token budgets (text) | Standard | Reduced |
| Research evidence in prompt | Full (up to 10 price + 8 competitor sources) | Top 5 + 3 by confidence |
| Report input | Bookkeeping stripped | Bookkeeping stripped + condensed to 300 chars/section |
| Reasoning suppression | Not applicable | Applied automatically, text agents only |

## Rate limit handling

`tools/groq_client.py` retries rate-limit (429) and server-error (5xx)
responses automatically, with exponential backoff and up to 5 attempts,
honoring the provider's retry-after guidance when present.

A request-too-large response (413) is not retryable — the request exceeds
the account's per-minute ceiling regardless of timing. If this occurs on a
text agent, reduce the relevant `num_predict` value in `app_qwen.py`, or
lower `REPORT_SECTION_MAX_CHARS` to shrink the report step's input
further. It does not apply to the vision step, which runs on Llama.

Every agent returns `{"error": ...}` on failure rather than raising an
exception, so a single failed request does not stop the pipeline or crash
the app.
