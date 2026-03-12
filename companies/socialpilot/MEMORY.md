# socialpilot — Agent Memory

## Key Decisions

- **[2026-03-11] Landing page deployed to site/index.html** — Created full production-ready landing page with hero, features (6), how-it-works (3 steps), testimonials, pricing (3 tiers), and waitlist CTA form. Based on existing landing-page.html draft but significantly expanded with: mock post previews in hero, testimonials section, 6 features (up from 3), styled pricing cards with Pro highlighted, animated loading state on form button, active nav highlighting, localStorage stub for waitlist emails.

- **Waitlist form**: Stubbed with working UX (loading state, success state, error handling). Has clear TODO comments for two wiring options: Formspree (no backend needed) or `/api/waitlist` endpoint. Backend wiring is next priority.

- **Pricing confirmed**: Free ($0 / 1 account / 10 posts) · Pro ($29 / 3 accounts / unlimited) · Scale ($79 / 10 accounts / teams)

## Lessons Learned

- Always check for existing files before creating from scratch — landing-page.html already existed and was 80% complete
- site/ is the deployable directory; landing-page.html in root was just a draft
- The waitlist form is a critical conversion point — must wire to real backend (Formspree or API) before launch

## Important Context

- Stack: Pure HTML/Tailwind CDN — no build step needed, Vercel-ready as-is
- Next dev priorities: (1) Wire waitlist form to Formspree or API endpoint, (2) Build signup/auth flow, (3) Add analytics (Plausible or Posthog)
- COMPANY.md says "needs signup form" — form exists in site/index.html but uses stub; needs real endpoint wired
