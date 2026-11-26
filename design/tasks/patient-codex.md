You are one of three competing design entries for the PATIENT side of a product called Mukoti. Independent judges will compare the three and the winner is built into the real app, so aim to win on clarity for a patient who cannot read, on craft, and on motion.

Repository: /Users/admin/.t3/projects/heckathon-caimex
Your folder (create it; write nothing anywhere else): design/entries/codex/

Start by reading, in this order: design/BRIEF.md (the rules, all of it), then web/app.css (colour tokens), web/index.html (the current patient screen and its Shona and English strings in the object T), app/prompts.py (BANK: the exact sentence spoken for each question), and look at docs/screens/after_patient.png and docs/screens/after_demo.png.

Deliver four things.

1. design/entries/codex/pictograms/ : one animated SVG per item, with exactly these file names. The English is what the helper is asking or saying; the patient hears it in Shona.

Questions:
- who.svg : "Who is unwell, you or a child?"
- age.svg : "How old are you?"
- onset.svg : "When did it start?"
- worse.svg : "Is it getting worse?"
- where.svg : "Where is the pain?"
- severity.svg : "Is the pain very bad?"
- fever.svg : "Do you have a fever?" (the body is hot)
- breathing.svg : "Are you struggling to breathe?"
- drinking.svg : "Is the child able to drink or breastfeed?"
- vomiting.svg : "Are you vomiting?"
- fits.svg : "Have there been any fits?" (convulsions)
- bleeding.svg : "Have you seen any blood?"
- neck.svg : "Is your neck stiff?"
- pregnancy.svg : "Are you pregnant?"
- chronic.svg : "Do you have a long-term illness, such as diabetes or high blood pressure?"
- medicines.svg : "Are you taking any medicines these days?"
- allergy.svg : "Is there any medicine that does not agree with you?"
- other.svg : "Is anything else troubling you?"

States:
- welcome.svg : the helper greeting a patient at the clinic door ("What brings you here today?")
- listening.svg : "Speak now, I am listening"
- thinking.svg : the helper is working on what was said
- repeat.svg : "Please say that again, I did not hear you"
- nurse_coming.svg : "The nurse is coming to you now" (calm and reassuring, never alarming)
- wait.svg : "Please take a seat, the nurse will call you"
- recording.svg : "Your voice is recorded so the nurse can listen to it"
- not_doctor.svg : "This helper is a computer, not a doctor"

Follow the illustration style and the technical rules in design/BRIEF.md exactly: viewBox 0 0 240 240, colours only through the six CSS variables with fallbacks, no text inside, class and keyframe names prefixed with the file name, one calm meaningful loop of 2 to 4 seconds, a reduced-motion still, under 12 KB each, readable at 96px.

2. design/entries/codex/logo.svg : an app mark, viewBox 0 0 64 64: a white mark on a blue rounded tile (the tile, and only the tile, may use the gradient #4F86F7 to #2563EB to #1D4ED8). It should say "a helper that listens, at a clinic" better than the current plain white plus in web/icon.svg, and still read at 16px.

3. design/entries/codex/index.html : one page that presents your design. It may load the local Figtree files with a relative path (../../../web/fonts/figtree-400.ttf and the 600 and 700 files) and your own SVG files; nothing else external. It contains:
   a. A row of phone frames, 390 by 800 CSS pixels each, built as real HTML and CSS (not pictures of screens), one per state: (1) welcome, with the Shona or English choice and one start button, using as few words as you can; (2) a question being asked while the helper speaks, with its pictogram large and the sentence under it; (3) the patient's turn, listening, with the microphone; (4) what was heard, shown back, while the helper thinks; (5) the ticket at the end with the patient's number; (6) the ticket when the nurse has been called. Use the real Shona strings from web/index.html and app/prompts.py; do not write your own Shona. Show a quiet English caption under the Shona where it helps a judge.
   b. Motion between and within states: how a pictogram arrives, how the microphone invites speech, how the progress through six questions is shown without numbers being the only cue.
   c. Below the frames, a gallery of every pictogram at 96px and at 240px, on the light page and on the dark page side by side (wrap the dark half in an element with data-theme="dark" that sets the six variables to the dark values: ink #F3F5F9, accent #5B8DEF, tint #1B2A4A, danger #FF8A8F, paper #141A24, quiet #C3CAD6).
   d. A control that switches the whole page between light and dark, with a check mark on the chosen one.

4. design/entries/codex/README.md : at most 40 lines. Your idea in two sentences, how you balance picture and words, your motion principles, and what a reviewer should look at first.

Do not start or stop any server, do not read .env, do not call any network service, and do not touch any file outside design/entries/codex/. If you have a browser tool, look at your page in light and dark, at 390 wide, and at 360 by 640 with the root font size at 130%, and fix what you see.

Finish with the report described at the end of design/BRIEF.md.
