You are designing the NURSE'S side of a product called Mukoti, as a visual-first prototype. The owner's complaint about the current screen is that it is "massively controlled by large amounts of text". A nurse with a full waiting room should grasp the queue in two seconds without reading a paragraph.

Repository: /Users/admin/.t3/projects/heckathon-caimex
Your folder (create it; write nothing anywhere else): design/entries/nurse/

Start by reading design/BRIEF.md in full (the product, the owner's fixed design rules, the illustration and technical rules), then web/app.css, web/nurse.html (the current screen and the shape of a visit: status, triage.level, triage.checks, live_signs, note, turns, trace, placed_ahead), and look at docs/screens/after_nurse.png and docs/screens/after_demo.png.

What a visit holds, for your mock data (use these real examples):
- Ticket 1, emergency: "Difficulty breathing and fever in an 8-month-old child". Danger sign matched by fixed rules: Difficulty breathing. Alarm raised on the patient's first sentence. Waiting 2 minutes. Spoke Shona. Patient's words: "Mwana wangu ane mwedzi misere ari kutadza kufema, uye ari kupisa muviri." English: "My eight-month-old child is struggling to breathe and has a fever." Check first: respiratory rate and oxygen saturation; chest indrawing; temperature.
- Ticket 2, emergency: "Diarrhoea since yesterday in a 1-year-old; cannot drink or breastfeed, vomits everything". Danger sign: Child cannot drink or vomits everything. Placed ahead of 2 patients who arrived earlier.
- Ticket 3, emergency: "Very bad chest pain since this morning, with sweating", man aged 58, spoke English.
- Ticket 4, emergency: "Severe headache, fever and a stiff neck".
- Ticket 5, urgent: "Fell from a ladder, arm may be broken".
- Ticket 6, routine: "Headache and cough for two days", woman aged 32.
- Ticket 7, routine: "Came to collect blood pressure tablets".
- One patient still speaking to the helper now; two already seen.
Each visit has four checks that vote on the level, and the highest wins: Danger-sign rules, Interview model, Note model, Second opinion (the second opinion also gives three scores, for example routine 1%, urgent 12%, emergency 87%). The nurse can change the level, mark the patient seen, play each recorded sentence, print the note, and delete the visit. Every note is a computer's draft and must say so.

Deliver:

1. design/entries/nurse/index.html : a self-contained prototype (HTML, CSS, a little plain JavaScript; local Figtree from ../../../web/fonts/; no network, no libraries) showing:
   a. The queue on a desktop (1366 wide) with one patient open, and the same on a phone (390 wide). Design the row so that level, who it is, what is wrong and how long they have waited are read from shape, position, a small pictogram and at most one short line of words. Level must never depend on colour alone.
   b. The open visit, visual-first: the level and why; the danger signs as pictogram chips; the four checks as one clear graphic a nurse understands at a glance (for example four lights or four segments, with the second opinion's three scores shown as a small bar); "placed ahead of 2 who arrived earlier" as a graphic; the talk as a compact timeline with a play control on each of the patient's sentences and the English under the Shona; what to check first; the actions.
   c. The moment a new emergency arrives while the nurse is looking at something else: calm, but impossible to miss, and it must not move what she is reading out from under her finger without warning. Animate it; put a button on the page that replays it.
   d. The state while a note is still being written, and the state when a note could not be written (the visit is then shown as urgent, with the patient's words).
   e. A light and dark switch with a check mark on the chosen one.
2. design/entries/nurse/icons/ : the small pictograms you use (24 by 24 viewBox SVG files, colours through the CSS variables in the brief), for the complaints and for the four checks.
3. design/entries/nurse/README.md : at most 40 lines: the idea, what you removed and why, the motion, what to look at first.

Keep every rule in design/BRIEF.md: the cool grey and blue palette, red only for emergencies, the orange dot with slate words for urgent, green for done, no gradients or glows, calm motion with a reduced-motion fallback, AA contrast, touch targets of 44px. Do not start or stop any server, do not read .env, do not call any network service, and do not touch any file outside design/entries/nurse/. If you have a browser tool, look at your page in light and dark at both widths and fix what you see.

Finish with the report described at the end of design/BRIEF.md.
