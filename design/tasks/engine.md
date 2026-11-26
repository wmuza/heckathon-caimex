You are designing one page of a product called Mukoti as a visual-first prototype: the "Engine" page, which shows hackathon judges exactly how the product uses the CAIMEx AI gateway. The current page explains this in paragraphs and tables. The owner wants it led by a clear animated diagram and simple charts, with very few words.

Repository: /Users/admin/.t3/projects/heckathon-caimex
Your folder (create it; write nothing anywhere else): design/entries/engine/

Start by reading design/BRIEF.md in full (the product, the owner's fixed design rules and the technical rules), then web/app.css, web/engine.html (the current page), and look at docs/screens/after_engine.png.

The facts to show (all true; do not change the numbers and do not add any):

One sentence from a patient goes through five steps:
1. Hear: CAIMEx speech to text, model languages-lab-stt-large-1.3, about 0.76 s.
2. Check the words: Mukoti's own code, no AI. Fixed danger-sign rules read the sentence; an emergency stops the questions and calls the nurse at once.
3. Choose a topic: CAIMEx chat, model deepseek-v4-flash, about 0.68 s. It chooses what to ask next; it does not write the question.
4. Say only fixed sentences: Mukoti's own code, no AI. The sentence spoken was written in advance (28 of them in each language), so the helper cannot give advice.
5. Speak: CAIMEx text to speech, model languages-lab-tts-large-1.3, voice "getrude". Every sentence was made once and saved, so this step adds no waiting.
From the end of the patient's sentence to the helper answering: about 1.4 s.

When the talk ends:
6. Write the note: CAIMEx chat with reasoning, deepseek-v4-flash, about 6 s.
7. Second opinion: CAIMEx decisions, model d3-nano, about 0.15 s; it scores each level.
8. Combine: Mukoti's own code. Four checks vote (danger-sign rules, interview model, note model, second opinion); the highest level wins; only the nurse can lower it.

Four CAIMEx models through four services, each listed by the CAIMEx catalogue as hosted in Zimbabwe.
Cost of one visit at list prices: about $0.04, of which 98% is speech recognition.
Tried on 60 patient statements it was never written against: the four checks together gave 24 of 24 emergencies the emergency level, put 12 of 12 urgent cases ahead of the queue, and left 18 of 24 ordinary visits as routine. The fixed rules alone caught 11 of 24 emergencies.
Tried on 30 made-up sample patients spoken aloud: 30 of 30 visits completed, none given too low a level.
None of this is a clinical test, and every such number on the page must carry that caveat close to it.
24 technical issues were logged for the CAIMEx team.

Deliver:

1. design/entries/engine/index.html : a self-contained prototype (HTML, CSS, inline SVG, a little plain JavaScript; local Figtree from ../../../web/fonts/; no network, no libraries) with:
   a. An animated diagram of one sentence travelling through steps 1 to 5 and back to the patient, then steps 6 to 8 to the nurse. A viewer must see at a glance which steps are CAIMEx models (solid) and which are Mukoti's own code with no AI (dashed), and where the time goes. Model names are shown, small but readable. Give it a replay control. It must also make sense as a still picture.
   b. The four checks as a graphic, showing that the highest wins and that a model failing can never lower a level.
   c. The evidence as simple unit charts (for example 24 dots of which 24 are filled, beside 24 dots of which 11 are filled), the cost split as one bar, and the count of issues. Each with its caveat in a few words.
   d. It works at 1366 wide and at 390 wide, in light and in dark, with a switch that shows a check mark on the chosen one.
2. design/entries/engine/README.md : at most 40 lines: the idea, what you turned from words into pictures, the motion, what to look at first.

Keep every rule in design/BRIEF.md: the cool grey and blue palette, tints only in small shapes, no gradients or glows, one typeface, calm motion with a reduced-motion fallback, AA contrast. Do not start or stop any server, do not read .env, do not call any network service or API, and do not touch any file outside design/entries/engine/. If you have a browser tool, look at your page in light and dark at both widths and fix what you see.

Finish with the report described at the end of design/BRIEF.md.
