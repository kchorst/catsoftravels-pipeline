# Managing LLM Voice (GUI-Only) — COT YouTube Movie Creator Suite

This document explains how to control and refine your metadata “voice” **using only the GUI**.

You do **not** need to edit Python files.

---

## 1) Where the voice settings live

Open:

- `master_launcher.py` → **Settings** → **YOUTUBE**

You will see two text boxes:

- **LLM voice/style override**
- **LLM examples override**

These fields are saved into your local `cot_config.json` and are used automatically by the metadata generator.

---

## 2) What each field does

### LLM voice/style override

Use this to define:

- Tone (dry, warm, journal-like, documentary, comedic)
- Rules (no clickbait, no emojis, word limits)
- Structure preferences (paragraph count, include tags, include “what to expect”)
- Channel-agnostic closing behavior (“Follow the channel for more”)

If this field is blank:

- The suite uses its built-in default voice block.

### LLM examples override

Use this to show the LLM:

- The exact output format you expect (TITLE / DESCRIPTION / TAGS)
- The “vibe” via real examples
- How long the title/description should be
- What kinds of words you do (and do not) like

If this field is blank:

- The suite uses its built-in example block.

---

## 3) Recommended workflow: how to tune your voice

### Step A — Start simple

1. Paste a short voice block (5–15 lines) into **LLM voice/style override**.
2. Leave **LLM examples override** blank at first.
3. Click **Save and Close**.

Generate metadata for one video and see the output.

### Step B — Fix the biggest issue first

Common tweaks:

- Too hype → add “Avoid hype/marketing words; no excessive exclamation points.”
- Too long → add “Title max 60 chars; description max 1200 chars; 2–4 paragraphs.”
- Too generic → add “Prefer concrete details and specific images over generic adjectives.”
- Too repetitive → add “Avoid repeating the location name more than once in the title.”

### Step C — Add examples when you want consistency

Once you like the general voice, paste 1–3 examples into **LLM examples override**.

Good examples are:

- Similar to your real channel output
- Similar length to what you want
- In the exact output format you want every time

---

## 4) Two starter voice templates (optional)

Paste ONE into **LLM voice/style override**.

### Option A: Mark Twain–style travel narrator

```text
You are writing YouTube metadata.

VOICE:
- Write in a dry, witty, observant travel-narrator voice (Mark Twain–style).
- Use clean, plain language. Avoid hype and marketing fluff.
- Prefer concrete details and specific images over generic adjectives.

RULES:
- Title: short, specific, curiosity-driven; no clickbait.
- Description: 2–5 short paragraphs; friendly and readable.
- Include a few natural keywords, but do not keyword-stuff.
- Avoid excessive emojis, excessive exclamation points, and repetitive phrasing.

CLOSER:
- End with a short, natural closer that fits the place.
- Use a generic closer like “Follow the channel for more.” if needed.
```

### Option B: Generic travel journal vibe

```text
You are writing YouTube metadata.

VOICE:
- Write in a calm, modern travel-journal voice.
- Friendly, grounded, and descriptive — no hype.
- Short sentences are fine. Keep it easy to read.

RULES:
- Title: clear and specific; avoid clickbait.
- Description: 2–4 short paragraphs.
- Include practical details (what it felt like, what you saw, a small highlight), but keep it concise.
- Add a short “what to expect” line if it fits.

CLOSER:
- End with a simple closer (e.g., “Subscribe for more travel stories.”) or a natural sign-off.
```

---

## 5) Example block starter (optional)

Paste into **LLM examples override**.

```text
=== REAL EXAMPLES — MATCH THIS OUTPUT FORMAT ===

Location: Kyoto, Japan
TITLE:
Kyoto After Dark: Lantern Streets and Quiet Temples
DESCRIPTION:
Kyoto doesn’t shout; it murmurs. Step off the bright avenues and the city turns to lantern light, narrow alleys, and temple gates that close like a book.

In this visit we wander the old lanes, pause for small meals, and let the night do most of the talking. If you’ve ever wanted Japan to slow down for a moment, Kyoto is willing.

TAGS:
Kyoto, Japan travel, lanterns, temples, night walk, Gion
```

---

## 6) Troubleshooting

### “My changes didn’t apply”

- Re-open **Settings → YOUTUBE** and confirm you clicked **Save and Close**.
- Confirm you are running the metadata tool from the same folder where `cot_config.json` is saved.

### “I want to go back to default”

- Clear both override boxes
- Save

### “The model ignores my rules”

- Make your rules shorter and more explicit
- Add 1–2 examples that demonstrate the rule
- Avoid contradictory rules (e.g., “very short” plus “include lots of detail”)

---

## 7) What gets saved (FYI)

The GUI writes these keys into `cot_config.json`:

- `LLM_VOICE_STYLE`
- `LLM_EXAMPLES_BLOCK`

You can manage them entirely through the GUI; editing the JSON is not required.
