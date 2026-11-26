# Mukoti — Visual-First Patient Entry (Antigravity)

## Idea
A calm, human-figure pictogram leads every question and state so a patient who cannot read understands what is asked in one second, before reading a word. Shona speech and concise text stay underneath as quiet support rather than a wall of instructions.

## Picture & Word Balance
- **Welcome** trims the screen to one friendly clinic doorway illustration (`welcome.svg`), the ChiShona/English check-marked toggle, two visual trust chips (`recording.svg`, `not_doctor.svg`), and one primary blue start pill.
- **Interview** anchors the active question pictogram at 204px above the Shona sentence and keeps a smaller visual reminder on screen during listening and thinking so the patient never loses context.
- **Tickets** pair the queue number with `wait.svg` (routine) or calm `nurse_coming.svg` (urgent, orange dot `#D9650A` and zero red alarm).

## Motion Principles
- **Arrival**: each new pictogram fades and lifts gently (440 ms ease-out) into place.
- **Calm loops**: every SVG runs one meaningful 2.2–4.0 s loop (breathing lungs, rising thermometer, falling droplet, nodding stiffness) with full `prefers-reduced-motion: reduce` stills.
- **Voice & progress**: a slow blue breathing halo invites tapping the mic; active steps widen nearly 2× with a pulsing dot so progress reads without relying on numbers alone.

## Where to Look First
1. Open [index.html](index.html) and scan the **six 390×800 phone frames** top-to-bottom, toggling **Light / Dark** in the header.
2. Test the **Motion** cards (pictogram arrival, mic states, 6-step visual progress).
3. Inspect the **side-by-side Light & Dark gallery** at **96px** and **240px** to verify stroke legibility and shared CSS-variable theming, and check [logo.svg](logo.svg) at **16px** in the header bar.
