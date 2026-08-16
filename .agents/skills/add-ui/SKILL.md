---
name: add-ui
description: Generate 5 distinct, production-grade UI variations for a requested new or existing section, component, page, flow, or shell, then help the user preview and apply one. Use when the user asks to add or redesign UI like a hero, pricing, navbar, auth flow, dashboard shell, ecommerce surface, or data component.
metadata:
  argument-hint: "[request]"
---

## MANDATORY PREPARATION

Users start this workflow with `/add-ui`. `add-ui` is the canonical skill name in this repository. Some hosts may expose a friendly `/add` alias, but docs, wrappers, and source files should continue to refer to the skill as `add-ui`.

Once this skill is active, load $frontend-design — it contains the design principles, anti-patterns, and the **Context Gathering Protocol**. Follow that protocol before proceeding. If no design context exists yet, you MUST load $setup first.

When the request is for a brand-new landing page, marketing page, or several distinct directions and the aesthetic is still open, use the approved style-selection rules in `frontend-design`'s [design directions](../frontend-design/reference/design-directions.md). Choose directions that fit the product idea and brand context instead of inventing vague vibe labels.

When working inside an existing project with an established visual system, preserve that system first and make the options feel distinct without quietly rebranding the product.

Also gather the smallest set of implementation details needed to generate usable code:

- framework / runtime (React, Next.js, Vue, plain HTML, etc.)
- styling system (Tailwind, CSS modules, styled-components, vanilla CSS, etc.)
- target insertion point (new route, existing page, shared component folder, design system area)
- whether this is a brand-new artifact or a redesign of an existing one
- whether the user wants a section, page, flow, shell, or standalone component
- quality bar (quick draft, production-ready, flagship)

If the request is a redesign of an existing artifact, also identify:

- which parts must remain recognizable (content blocks, section order, interaction model, familiar affordances, brand cues)
- which parts are flexible (style, colors, copywriting, typography, media treatment, density, detail language)
- whether the user wants mostly safe evolution, a broad explore-and-compare pass, or one or two stretch directions

Use this precedence order when deciding implementation defaults:

1. detect and match the existing project's styling and component libraries first
2. if this is a brand-new project and the user explicitly names a styling or component library, use that
3. if this is a brand-new project and the user does not specify, use the framework defaults defined in `frontend-design`

When React-based fallback defaults are relevant, also consult [component library integration](./reference/component-library-integration.md) to decide whether the requested artifact should be led by primitives, reusable patterns, or block accelerators.

Ask only the missing questions. If you can infer the technical stack from the codebase, do so.

Consult these references as needed:

- [artifact taxonomy](./reference/artifact-taxonomy.md)
- [component library integration](./reference/component-library-integration.md)
- [variation quality bar](./reference/variation-quality-bar.md)
- [preview and apply patterns](./reference/preview-apply-patterns.md)
- [request mapping heuristics](./reference/request-mapping.md)
- [examples and command naming](./reference/examples.md)

Use these deterministic helper assets when they improve consistency across hosts and agents:

- [comparison table template](./assets/comparison-table-template.md)
- [component library integration checklist](./assets/component-library-integration-checklist.md)
- [variant naming scheme](./assets/variant-naming-scheme.md)
- [preview page checklist](./assets/preview-page-checklist.md)
- [apply / cleanup checklist](./assets/apply-cleanup-checklist.md)

---

Generate multiple **meaningfully different** UI directions for a requested artifact, help the user compare them, then guide selection and integration.

This includes both **adding new UI** and **redesigning existing UI**.

When the request is to redesign an existing page, section, flow, shell, or component, default to preserving the artifact's recognizable bones unless the user explicitly asks for structural reinvention. In practice that usually means:

- keep the core information architecture, content blocks, and sequence intact when they already support the job to be done
- keep familiar interactions and affordances unless they are clearly broken or the user asks for a larger UX shift
- evolve the visual system through typography, color, copy framing, media treatment, detail language, spacing rhythm, and emphasis strategy
- make it obvious across the options what stayed constant and what changed

If one variant intentionally pushes further on structure, label it clearly as the stretch option instead of quietly bulldozing the existing page.

This skill is for requests like:

- marketing and monetization surfaces: hero, features, pricing, testimonials, FAQ, CTA, logo cloud, gallery, blog, about, contact, plan pickers, upgrade modals, paywalls
- navigation and shell: navbar, footer, dashboard shell, onboarding feed, settings, card nav
- auth and account: login, register, forgot password, reset password, verify email, two-factor auth
- commerce: product overview, product category, product list, filters, cart, checkout, reviews, order summary, gift car
