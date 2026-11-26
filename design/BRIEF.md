# Design brief: a visual-first Mukoti

Shared by every design entry. Read all of it before you draw anything.

## The product

Mukoti is a voice helper at the door of a primary care clinic in Zimbabwe. A patient, often
older, often unable to read well, sometimes holding a sick child, speaks to a phone or tablet in
Shona or English. The helper asks up to six short questions aloud, one at a time, and the patient
answers by voice. The clinic nurse then sees a queue ordered by urgency, with a short note per
patient. It never diagnoses and never gives advice.

It works today. The running code is in `app/` and `web/` (plain HTML, CSS and JavaScript, no
framework, no build step). Screenshots of the current look are in `docs/screens/after_*.png`.
`web/app.css` holds the colour tokens. You may read anything in the repository. You may not
change anything outside your own entry folder.

## What the owner asked for

The screens are still "massively controlled by large amounts of text". He wants a UI led by
**excellent graphics, illustrations and animation**, where a patient who cannot read still knows
what is being asked and what to do. Text stays, but as support for the picture, not the other way
round.

The core idea: **a picture for every question.** When the helper asks "Are you struggling to
breathe?", the patient sees an animated illustration of breathing difficulty while hearing the
question. The sentence appears under it, smaller.

## The owner's design standard (fixed rules, do not break them)

- Cool, clean and plain. Light theme: page `#F4F5F7`, white panels (about 22px corners, hairline
  `#E5E7EB`, a soft cool shadow), ink `#1F2430`, quiet ink `#5B6474`, a pale blue band `#EDF2FA`
  behind the page title. Dark theme: page `#0B0F17`, panels `#141A24`, text `#F3F5F9`, quiet text
  `#C3CAD6`.
- Blue is for what you press and what is chosen: fill `#2563EB` (dark `#2F66E8`), blue text and
  icons `#1D4ED8` (dark `#9DBBFB`), selected ground `#E8F0FE` (dark `#1B2A4A`).
- Red `#CF2A30` only for recording, Stop, errors, blood and emergencies. Green `#1F6B43` on
  `#E3F4EA` for done. Waiting or warning: an orange dot `#D9650A` with slate words.
- **No cocoa, gold, brown or warm paper anywhere.** No purple gradients, glow blobs, neon,
  glassmorphism or cluttered dashboards. Nothing that looks like a default AI-generated page.
- Tints only in small shapes, chips and tags, never as big fills.
- One typeface: Figtree, weights 400, 600, 700, from the local files in `web/fonts/` (never a
  web font link). Titles plain bold. No italics, no serif.
- Buttons in sentence case. The main action is a blue pill with a white label. One clear action
  per row. Touch targets at least 44px.
- A selected state is shown with a check mark, not colour alone.
- **Calm motion.** Slow, purposeful, a few seconds per loop. Nothing flashes, bounces hard or
  spins fast. Everything must still read with motion switched off
  (`@media (prefers-reduced-motion: reduce)`).
- Every text and icon meets WCAG AA contrast on its background; controls at least 3:1. It must
  hold at 130% text size on a 360x640 phone.

## Illustration style (so the set reads as one family)

- Simple, warm-hearted, human figures with rounded forms: no facial detail beyond what the
  meaning needs, no skin-tone fills (figures are drawn in ink line with white or pale blue fill),
  no gender or ethnic stereotypes, no Western-only symbols (a birthday cake does not mean "age"
  here; use figures of different sizes, or a baby, a child and an adult).
- Line: round caps and joins, one stroke weight per illustration (about 6 units on a 240 canvas).
- Colour only through these CSS variables, each with the light value as fallback, so the same
  file works in both themes:
  `var(--ink, #1F2430)`, `var(--accent, #2563EB)`, `var(--tint, #E8F0FE)`,
  `var(--danger, #CF2A30)`, `var(--paper, #FFFFFF)`, `var(--quiet, #5B6474)`.
- No text or letters inside any illustration. They must mean the same in Shona and English.
- The meaning must be clear in one second to someone who cannot read. If a picture needs a
  caption to be understood, redraw it.
- One calm looping animation per illustration that carries the meaning (lungs filling, a drop
  falling, a thermometer rising), 2 to 4 seconds per loop.

## Technical rules

- No network at all: no CDN, no web fonts, no remote images, no analytics. No JavaScript
  libraries. CSS animation, SMIL inside SVG, or the Web Animations API only.
- Each illustration is its own standalone `.svg` file, `viewBox="0 0 240 240"`, with its
  animation in a `<style>` element inside the file. Prefix every class name and keyframe name
  with the file's name (for example `.breathing-lung`, `@keyframes breathing-fill`) so that
  several illustrations can be placed inline on one page without clashing.
- Include `@media (prefers-reduced-motion: reduce)` inside each file, leaving a clear still.
- Keep each file under 12 KB. Hand-written, tidy SVG: no editor metadata, no base64, no filters
  that blur, no `<foreignObject>`, no scripts.
- Do not read `.env`, do not call any API, do not use the CAIMEx key, do not start or stop any
  server (one is running on port 8000; leave it alone), do not run `git` commands that change
  anything, and do not edit, create or delete any file outside your entry folder.

## Check your own work

If you have a browser tool, open your pages and look at them, in light and in dark, at 390 wide
and at 360x640 with 130% text. Look at every illustration at 96px and at 240px: if it turns to
mush at 96px, simplify it. Fix what you see before you report.

## Report

End with a short report: what you made (file list), the one idea you are proudest of, what you
are least sure about, and anything you could not check.
