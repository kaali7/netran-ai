---
name: critique
description: Evaluate an interface from a UX perspective, assessing hierarchy, information architecture, emotional resonance, cognitive load, and overall quality with quantitative scoring and actionable feedback. Use when the user wants an overall design or UX review—not when the main need is measurable accessibility/performance diagnosis, or final micro-detail polish.
metadata:
  argument-hint: "[area (feature, page, component...)]"
---

## MANDATORY PREPARATION

Users start this workflow with `/critique`. Once this skill is active, load $frontend-design — it contains design principles, anti-patterns, and the **Context Gathering Protocol**. Follow that protocol before proceeding — if no design context exists yet, you MUST load $setup first. Additionally gather: what the interface is trying to accomplish.

---

Conduct a holistic design critique, evaluating whether the interface actually works — not just technically, but as a designed experience. Think like a design director giving feedback.

Consult the [hierarchy checklist](../frontend-design/reference/hierarchy-checklist.md) for grayscale tests, action prioritization, and label/value treatment.
Consult the [text hierarchy and readability](../frontend-design/reference/text-hierarchy-and-readability.md) for line length, line-height, baseline, alignment, and title restraint.
Consult the [cognitive load](../frontend-design/reference/cognitive-load.md) for working-memory limits and the 8-item checklist.
Consult the [interaction design](../frontend-design/reference/interaction-design.md) when evaluating familiar patterns, target sizing, focus treatment, and overlay behavior.
Consult the [search and findability](../frontend-design/reference/search-and-findability.md) when the interface depends on site search, command palettes, autosuggest, result relevance, or no-results recovery.
Consult the [legacy modernization](../frontend-design/reference/legacy-modernization.md) when the critique involves legacy systems, old/new seams, migration candidates, or high-risk operational workflows.
Consult the [ai slop detection](../frontend-design/reference/ai-slop-detection.md) for the consolidated anti-pattern list.
Consult the [action hierarchy](../frontend-design/reference/action-hierarchy.md) when evaluating primary/secondary/tertiary actions.
Consult the [semantic color](../frontend-design/reference/semantic-color.md) when color is carrying meaning.
Consult the [surface separation](../frontend-design/reference/surface-separation.md) when judging borders, card usage, overlap, or background-shift decisions.
Consult the [image treatment](../frontend-design/reference/image-treatment.md) when screenshots, icons, and media affect readability or polish.

Treat the shared frontend-design references as canonical for hierarchy, readability, and cognitive-load doctrine, then keep this skill focused on evaluation, scoring, and prioritization.

When empty states are relevant, evaluate the zero-data surface itself through `empty-state` thinking, and evaluate broader activation, aha moments, and first-run education through `onboard` thinking.

## Phase 1: Design Critique

Evaluate the interface across these dimensions:

### 1. AI Slop Detection (CRITICAL)

**This is the most important check.** Does this look like every other AI-generated interface from 2024-2025?

Review the design against ALL the **DON'T** guidelines in the frontend-design skill and the [ai slop detection](../frontend-design/reference/ai-slop-detection.md) reference — they are the fingerprints of AI-generated work. Check for the AI color palette, gradient text, dark mode with glowing accents, glassmorphism, hero metric layouts, identical card grids, generic fonts, and all other tells.

**The test**: If you showed this to someone and said "AI made this," would they believe you immediately? If yes, that's the problem.

### 2. Visual Hierarchy
- Does the eye flow to the most important element first?
- Is there a clear primary action? Can you spot it in 2 seconds?
- Does the right thing stand out, or is emphasis spread so evenly that nothing is memorable? (von Restorff effect)
- Do size, color, and position communicate importance correctly?
- Is there visual competition between elements that should have different weights?
- Is the hierarchy clear even if you imagine the screen in grayscale?
- Are section titles quieter than the content they introduce, or are they stealing focus?
- Has action hierarchy flattened so multiple buttons feel equally urgent?

### 3. Information Architecture & Cognitive Load
> *Consult [cognitive-load](../frontend-design/reference/cognitive-load.md) for the working memory rule and 8-item checklist*
- Is the structure intuitive? Would a new user understand the organization?
- Is related content grouped logically?
- Do common patterns behave the way users already expect? Check navigation, search, tables, filters, forms, tabs, dropdowns, pagination, and settings for unnecessary novelty.
- Is avoidable complexity pushed into the system through defaults, prefills, and guidance, or dumped on the user to manage manually? (Tesler's Law)
- Are there too many choices at once? Count visible options at each decision point — if >4, flag it
- Is the navigation clear and predictable?
- If search is present, does it understand intent, synonyms, typos, and likely destinations, or does it punish users for not knowing internal vocabulary?
- In mixed legacy/modern flows, does one fragile step make the entire product feel unreliable or inconsistent?
- **Progressive disclosure**: Is complexity revealed only when needed, or dumped on the user upfront?
- **Run the 8-item cognitive load checklist** from the reference. Report failure count: 0–1 = low (good), 2–3 = moderate, 4+ = critical.

### 4. Emotional Journey
- What emotion does this interface evoke? Is that intentional?
- Does it match the brand personality?
- Does it feel trustworthy, approachable, premium, playful — whatever it should feel?
- Would the target user feel "this is for me"?
- Do frequent interactions respond fast enough to preserve flow, or do repeated waits keep breaking concentration? (Doherty Threshold)
- **Peak-end rule**: Is the most intense moment positive? Does the experience end well (confirmation, celebration, clear next step)?
- **Emotional valleys**: Check for onboarding frustration, error cliffs, feature discovery gaps, or anxiety spikes at high-stakes moments (payment, delete, commit)
- **Interventions at negative moments**: Are there design interventions where users are likely to feel frustrated or anxious? (progress indicators, reassurance copy, undo options, social proof)

### 5. Discoverability & Affordance
- Are interactive elements obviously interactive?
- Would a user know what to do without instructions?
- Are primary and frequent targets large enough and close enough to use confidently, especially on touch devices?
- Do powerful features have safeguards proportional to their risk — permissions, previews, undo, confirmation, history, or explicit consequence language?
- Are hover/focus states evident and responsive?
