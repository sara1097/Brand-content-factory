VARIANT_SYSTEM_PROMPT = """
You are an expert marketing copywriter specialized in social media ads.
You write 3 ad variants from the same core message using different psychological angles.
You never reuse a sentence opener, structure, or CTA phrasing that has already appeared
in this campaign, even if the topic is similar.
You ALWAYS return valid JSON only. No explanation. No markdown. Just JSON.
"""

# Banned patterns — extend this list every time you notice the model falling
# into a habit (this is exactly what happened with "Feel the..." and
# "Grab yours before it's..." in your current output).
BANNED_OPENERS = [
    "Feel the",
    "Imagine holding",
    "Why do collectors choose",
    "Only a few left",
    "This is your final opportunity",
    "For every fan",
    "Step into",
]

BANNED_CTA_PATTERNS = [
    "Grab yours before it's",
    "Secure your piece of history",
    "Add to your collection",
    "Before it's gone",
]

BANNED_WORDS_OVERUSED = [
    "authentic", "authenticity", "legacy", "craftsmanship",
    "premium", "collectors who", "true fans",
]


def format_used_list(items, label):
    """Turn a plain list into a readable block for the prompt.
    Returns a clear 'none yet' message instead of an empty section,
    so the model doesn't silently ignore a blank block."""
    if not items:
        return f"(no {label} used yet — this is day 1)"
    return "\n".join(f"- {item}" for item in items)


VARIANT_TASK_PROMPT = """/no_think

You are given a COMPLETE Marketing Strategy.

Your job is NOT to create a new strategy.

Your job is to transform the existing strategy into THREE social media ad variants.

==================================================
CREATIVE BRIEF
==================================================

Campaign Goal:
{campaign_goal}

Target Audience:
{target_audience}

Platform:
{platform}

Brand Voice:
{brand_voice}

Brand Message:
{brand_message}

Value Proposition:
{value_proposition}

Storytelling Angle:
{storytelling_angle}

Campaign Ideas:
{campaign_ideas}

Discount Strategy:
{discount_strategy}

Promotional Tactics:
{promotional_tactics}

Recommended CTAs:
{call_to_actions}

Content Calendar (already planned posts -- keep variants complementary, do not duplicate a hook already used there):
{content_calendar_summary}

==================================================
ANTI-REPETITION MEMORY (CRITICAL — READ CAREFULLY)
==================================================

These are the EXACT hooks already used on previous campaign days:
{previous_hooks}

These are the EXACT CTAs already used on previous campaign days:
{previous_ctas}

Rules:
- Do NOT reuse any of the above hooks or CTAs, in full or in paraphrased form.
- Do NOT reuse the sentence STRUCTURE of any hook above (e.g. if a previous hook
  was "Feel the X of Y", do not write "Feel the Z of W" — that is still a repeat).
- Do NOT open any variant with any of these banned phrases or close variants:
{banned_openers}
- Do NOT end any CTA with these banned patterns:
{banned_ctas}
- Avoid overusing these words unless the strategy text itself uses them:
{banned_words}

==================================================
TASK
==================================================

Generate THREE different ad variants.

Variant A
- Emotional

Variant B
- Rational

Variant C
- Urgency

The urgency variant should use a different urgency trigger depending on the campaign day, such as:
- Product launch
- Limited stock
- Best seller
- Weekend promotion
- Offer ending soon
- Final chance
- Last hours

Do NOT use the same urgency reason as any previous day (see ANTI-REPETITION MEMORY above).

IMPORTANT — GROUNDING RULES:

- Follow the marketing strategy exactly.
- Do NOT invent a new strategy.
- Do NOT invent new discounts. Only mention a discount if it is explicitly present
  in "Discount Strategy" above — if that field is empty or says none, do not
  mention any percentage, code, or offer anywhere in the copy.
- Do NOT invent coupon codes.
- Do NOT invent fake statistics, numbers, or claims not present in the brief above.
- If promotional tactics exist, use them naturally.
- Use the recommended CTA as inspiration, not verbatim.
- Every hook must be structurally different from every other hook, not just reworded.
- Every CTA must be structurally different from every other CTA.
- This advertisement represents ONE day of a 7-day campaign.
- Make today's messaging clearly different from the other campaign days.
- Stay consistent with the content calendar's tone and campaign angle.
- Use the content calendar topic as the primary inspiration for today's copy —
  the hook must directly reference something specific from today's topic, not
  a generic product statement that could apply to any day.
- The body should expand today's content idea, not repeat generic product information.

Write naturally. Vary sentence length and rhythm across variants.
Return ONLY valid JSON, matching exactly this schema:

{{
  "variant_a": {{
      "angle":"",
      "hook":"",
      "body":"",
      "cta":""
  }},
  "variant_b": {{
      "angle":"",
      "hook":"",
      "body":"",
      "cta":""
  }},
  "variant_c": {{
      "angle":"",
      "hook":"",
      "body":"",
      "cta":""
  }}
}}
"""


def build_variant_prompt(
    campaign_goal, target_audience, platform, brand_voice, brand_message,
    value_proposition, storytelling_angle, campaign_ideas, discount_strategy,
    promotional_tactics, call_to_actions, content_calendar_summary,
    previous_hooks=None, previous_ctas=None,
):
    """
    previous_hooks / previous_ctas: lists of strings collected from all
    variants generated on earlier days of THIS SAME campaign (variant_a,
    variant_b, variant_c hooks/ctas from day 1..N-1). Pass them in from your
    agent's running state — this is the piece that was missing before, and
    it's the main reason the model kept repeating "Feel the..." and
    "Grab yours before it's...": it never actually saw what it had already written.
    """
    return VARIANT_TASK_PROMPT.format(
        campaign_goal=campaign_goal,
        target_audience=target_audience,
        platform=platform,
        brand_voice=brand_voice,
        brand_message=brand_message,
        value_proposition=value_proposition,
        storytelling_angle=storytelling_angle,
        campaign_ideas=campaign_ideas,
        discount_strategy=discount_strategy,
        promotional_tactics=promotional_tactics,
        call_to_actions=call_to_actions,
        content_calendar_summary=content_calendar_summary,
        previous_hooks=format_used_list(previous_hooks, "hooks"),
        previous_ctas=format_used_list(previous_ctas, "CTAs"),
        banned_openers=format_used_list(BANNED_OPENERS, "openers"),
        banned_ctas=format_used_list(BANNED_CTA_PATTERNS, "CTA patterns"),
        banned_words=format_used_list(BANNED_WORDS_OVERUSED, "words"),
    )