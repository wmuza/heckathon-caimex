# How the pictures were chosen

Mukoti shows a picture for every question, so a patient who cannot read still knows what was
asked. This folder is the record of how the 26 pictures in `web/art/` came to be.

## The contest

`BRIEF.md` is the brief. Three AI coding agents each drew a full set from it, without seeing each
other's work: Codex (`entries/codex/`), Antigravity (`entries/antigravity/`) and Cursor
(`entries/cursor/`). The task files are in `tasks/`.

Each set was then put on the same plain sheet with numbers in place of names
(`sheet.html?entry=NAME&blind=1`), and a fresh AI reader that had seen nothing else was asked what
each picture meant. A fourth reader compared the three for craft and for Wilbert's design
standard.

| Set | Read correctly, of 26 | Notes |
|---|---|---|
| Codex | 19 | Clearest drawing, kept to the colour rules. Chosen as the base |
| Antigravity | 22 | More right, but more of them guesses, and red used outside its meaning |
| Cursor | about 17 | Mostly guesses. Good ideas: the whole body for "where", the trail of pictures |

These first-round totals were noted during the session; the answer sheets were not kept.

Two more tasks were given out and neither produced a design: the nurse's queue (Cursor, stopped
with a "resource exhausted" error) and the Engine page (the CAIMEx harness, cancelled after an
hour with nothing written). Both screens were then built in the main session.

## The redraw

Codex redrew 16 pictures and the mark (`entries/codex/pictograms-v2/`, `logo-v2.svg`), borrowing
lungs for breathing, dots for thinking and the ear with a return arrow from Antigravity, and the
whole body and the struck-out stethoscope from Cursor. `entries/final/` is the merged set, the
same files as `web/art/`.

## The final check

`blind_final.png` is the sheet a fresh AI reader was shown. It named the intended question or
message for 26 of 26, marking 13 "sure" and 13 "guess". Its first reading of each, with the
second meaning it offered:

| No. | Picture | Read as | Sure? |
|---|---|---|---|
| 1 | welcome | Welcome, you have come to the clinic | sure |
| 2 | who | Who is the patient, you or a child you brought? | guess |
| 3 | age | How old are you? | sure |
| 4 | onset | When did it start? | sure |
| 5 | worse | Is it getting worse? (or: how bad is the pain?) | guess |
| 6 | where | Where on your body is the problem? (or: a headache?) | guess |
| 7 | severity | Is the pain strong? | sure |
| 8 | fever | Do you have a fever? | sure |
| 9 | breathing | Is it hard to breathe? (or: a cough?) | sure |
| 10 | drinking | Can the child drink? | guess |
| 11 | vomiting | Have you been vomiting? | sure |
| 12 | fits | Have you had fits? (or: did you faint?) | guess |
| 13 | bleeding | Are you bleeding? | sure |
| 14 | neck | Is your neck stiff? (or: a sore throat?) | guess |
| 15 | pregnancy | Are you pregnant? | sure |
| 16 | chronic | A long-lasting illness? (or: a heart problem?) | guess |
| 17 | medicines | Are you taking any medicine? | sure |
| 18 | allergy | Does any medicine give you a reaction? (or: a rash?) | guess |
| 19 | other | Anything else you want to tell us? | guess |
| 20 | listening | I am listening, speak now | sure |
| 21 | thinking | Please wait, I am thinking | guess |
| 22 | repeat | I did not hear you, please say it again | sure |
| 23 | nurse_coming | The nurse will come to you | guess |
| 24 | wait | Please sit down and wait | sure |
| 25 | recording | Your voice is being recorded (or: I am listening) | guess |
| 26 | not_doctor | This machine is not a doctor or nurse | guess |

It found 16, 26 and 6 hardest. Two were changed afterwards and have not been read again: "where"
now shows a faint ring on every body spot, not only the one lit at that moment, and "not_doctor"
has a full "no" circle round the stethoscope.

## What this does not show

The readers were AI models looking at still pictures. No patient has seen these pictures, on any
phone. Whether a person in a waiting room reads them in a second is not known until someone
watches patients use them.
