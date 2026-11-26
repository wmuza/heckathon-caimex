# Second round: redraw the weak pictures of the winning set

Your set in `design/entries/codex/pictograms/` won a three-way contest. It was then put through a
blind test: a judge saw the 26 pictures with no captions and wrote down what each one meant. A
second judge compared the three sets side by side. Most of your pictures were read correctly. The
ones below were not, or were called weak. Redraw them in exactly your existing style (same line
weight, same figure proportions, same six colour variables, same technical rules as
`design/BRIEF.md`), so the family still reads as one.

Write the new files into a NEW folder, `design/entries/codex/pictograms-v2/`, using the same file
names. Only put files there that you have changed. Do not edit `pictograms/`, and do not touch
anything outside `design/entries/codex/`.

## Misread in the blind test (most important)

1. **breathing.svg** ("Are you struggling to breathe?"). It was read as "Are you coughing?",
   because air is shown leaving the mouth. Show the struggle inside the body instead: a person
   facing us, with two lungs visible in the chest that fill slowly and with effort, shoulders
   rising, mouth open. No puffs of air leaving the mouth, and remove the tick on the chest.
2. **thinking.svg** (the helper is working). The pulse line in a bubble was read as a heartbeat.
   Use one bubble with three calm dots that light in turn. Nothing else.
3. **repeat.svg** ("Please say that again, I did not hear you"). Two bubbles were read as
   "translation" or "a conversation". Use a person with a hand cupped behind one ear, and one
   curved arrow that returns to them.
4. **where.svg** ("Where is the pain?"). It was read as "Do you have chest pain?" because one
   ring sits on the chest. Draw the whole standing figure and let a ring appear in turn at the
   head, the chest, the belly and a knee, so the question is "which place?".
5. **severity.svg** ("Is the pain very bad?"). Hands on the head made it "a bad headache". Keep
   the face with its expression (it was the only warm face in the contest), take the hands off
   the head, and show the pain itself growing: pain marks that step from small to large.
6. **not_doctor.svg** ("This helper is a computer, not a doctor"). The slash between the screen
   and the person was read both as "not" and as "and". Draw the device with its voice bars, clear
   and whole, and beside it a stethoscope with one bold strike through it.
7. **recording.svg** ("Your voice is recorded so the nurse can listen"). The frame and play
   triangle read as a media player. Use only a microphone, a short waveform and a red dot.

## Called weak by the craft judge

8. **chronic.svg** ("a long-term illness, such as diabetes or high blood pressure"). The calendar
   with a gauge is too abstract. Draw a person with a heart on the chest and, beside or under
   them, a short row of day marks with an arrow that loops round and keeps going: "this goes on
   and on".
9. **worse.svg** ("Is it getting worse?"). Show growth on the pain mark itself: the same mark
   three times, small, larger, largest, with one rising arrow. Not a chart.
10. **neck.svg** ("Is your neck stiff?"). The blue marks are too thin to read. Put one bold blue
    band at the neck, and let the head try to turn and stop short.
11. **drinking.svg** ("Is the child able to drink or breastfeed?"). It shows an adult. Make it a
    small child drinking from a cup held by an adult's hand.
12. **who.svg**. The single blue dash under the adult explained nothing. Let a ring settle on the
    adult, then on the child, in turn: "which one?".
13. **welcome.svg**. Remove the logo bubble from the door; it is clutter at small size. Keep the
    figure waving at an open door with the plus.
14. **pregnancy.svg**. Remove the signal arcs behind the back; they were read as back pain.
15. **nurse_coming.svg** and **fits.svg**. Both tangle at 64px. Fewer strokes. In nurse_coming the
    direction must be unmistakable: the nurse moves towards the seated patient.

## Also

16. **logo.svg**: write an improved `design/entries/codex/logo-v2.svg`. Keep your idea (a speech
    bubble with the clinic plus), but thicken it so the bubble and the plus are both still clear
    at 16px.
17. Check every new picture at 64px on white and on the dark panel colour `#141A24` before you
    finish. If a picture needs more than a second to read at 64px, simplify it again.

Rules as before: no text inside any picture, colours only through the six CSS variables with
fallbacks, red (`--danger`) only for blood and the recording dot, class and keyframe names
prefixed with the file name, one calm loop of 2 to 4 seconds, a reduced-motion still, under
12 KB each, no network, no server, no `.env`, nothing outside `design/entries/codex/`.

Finish with a short report: which files you redrew, which one you are still least sure of, and
anything you could not check.
