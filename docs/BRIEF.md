# What to know before you present Mukoti

Read this once and you can answer anything a judge asks. Everything here is true of the code as
it stood on the evening of 25 November 2026. Where something is not done, it says so.

## The one sentence

Mukoti is a Shona-speaking helper that listens to patients while they wait and gives the clinic
nurse a short note and a queue with the most urgent patient first.

## The story in a minute

A clinic has one nurse and a full bench. She sees people in the order they arrived. WHO's own
guide says the person at reception "should assess the general condition of the careseeker(s)
immediately on arrival" and "periodically repeat this procedure if the line is long". In a clinic
with two nurses, nobody is free to do that.

Mukoti is that person. A patient speaks to a phone or tablet at the door, in Shona or English. It
asks up to six short questions aloud. The nurse gets a queue ordered by urgency, and for each
patient a four-line note in English, the patient's own words, and the recording.

It never diagnoses and never gives advice. If a patient says a danger sign, it stops asking and
calls the nurse.

## How it works, in the words to use

**One sentence goes through five steps.**

1. **Hear.** A CAIMEx speech model writes down what the patient said.
2. **Check.** Our own code, with no AI, reads the sentence against a fixed list of danger signs.
   An emergency stops the questions.
3. **Choose.** A CAIMEx chat model chooses what to ask about next. It does not write the question.
4. **Say only fixed sentences.** Our own code speaks the sentence written in advance for that
   topic. There are 28 of them in each language.
5. **Speak.** A CAIMEx voice model made each of those sentences once, when the server started.

**When the talk ends,** the chat model writes the nurse's note with its reasoning switched on,
and a second, smaller model reads the note cold and scores each level.

**Every question has a picture.** The patient hears the question, sees a picture of it and can
read the words. There are 26 pictures, drawn for Mukoti. The nurse's queue uses the same ones.

**Four checks vote** on the level: the fixed rules, the interview model, the note model and the
second opinion. The highest wins. Nothing can lower a level except the nurse.

## The numbers you may quote

| Say this | It comes from | Say this too |
|---|---|---|
| "On 60 patient statements it had never seen, it gave all 24 emergencies the emergency level." | `eval/heldout_results.json`, made by `tools/heldout.py` | "Written by an AI that could not see our rules, not collected from patients." |
| "The fixed rules alone caught 11 of those 24." | The same file | "Which is why there are four checks and a nurse in charge." |
| "It pushed 6 of 24 ordinary visits ahead of the queue." | The same file | "It errs towards caution. That costs the nurse time, and we count it." |
| "On our 30 sample patients, spoken aloud, nobody was given too low a level." | `eval/results.json`, made by `tools/evaluate.py --spoken` | "We wrote those patients ourselves, so that only shows the pipeline holds together." |
| "It answers about 1.4 seconds after the patient stops speaking." | The same file: 0.76 s to hear plus 0.68 s to choose | "The voice adds nothing, because every sentence is saved audio." |
| "A visit costs about 4 US cents on CAIMEx, 98% of it speech recognition." | The same file | "On short answers. A real patient says more, so expect more." |
| "Four CAIMEx models through four services, all listed as hosted in Zimbabwe." | The Engine page, from the gateway's catalogue | "That is what the catalogue lists. We have not checked it ourselves." |
| "We logged 24 issues for the CAIMEx team." | `CAIMEX_ISSUES.md` | |
| "80.9% of Zimbabweans spoke Shona in early childhood." | The 2022 census; see `docs/SOURCES.md` | |

Do not quote the 4.0% character error as accuracy. It is a synthetic voice heard back by a model
from the same family. The honest number is the one your team makes on the Voice check page.

## Why it is safe to show, claim by claim

Each of these is a test in `tests/test_visits.py`. They run with no internet: the models are
replaced by fakes that misbehave on purpose.

| Claim | The test |
|---|---|
| The helper only ever says sentences written in advance, whatever the model returns | `test_the_helper_only_ever_says_sentences_written_in_advance` |
| An emergency in the first sentence never waits for a model | `test_an_emergency_in_the_first_sentence_never_waits_for_a_model` |
| With every model down, the visit still finishes and goes ahead of the queue | `test_with_every_model_down_the_visit_still_finishes_and_goes_ahead_of_the_queue` |
| A bare "yes" to the breathing question sounds the alarm | `test_a_bare_yes_to_the_breathing_question_sounds_the_alarm_with_every_model_down` |
| The second opinion alone can raise to urgent but never to emergency | `test_the_second_opinion_alone_can_raise_to_urgent_but_never_to_emergency` |
| No check can lower what the rules found | `test_the_checks_never_lower_what_the_rules_found` |
| A level the nurse set is never overwritten | `test_a_level_the_nurse_set_survives_the_note_arriving` |
| A patient who walks away is not lost | `test_a_patient_who_walks_away_is_not_lost` |
| Old visits and recordings are deleted | `test_old_visits_are_deleted_while_the_server_runs` |

## What it is not

- **Not validated.** No clinician has reviewed the danger signs or the levels.
- **Not tested on patients.** Every patient in the demo is made up, with a synthetic voice.
- **Not a triage system.** The nurse triages. WHO's own FAQ for its triage tool says "Non health
  workers such as security guards should not be used to perform triage" and that a "simple
  screening tool" suits outpatient settings better than the full tool. Mukoti is the screening
  step.
- **Not checked by a native speaker.** Every Shona sentence was written by an AI. They are all in
  `docs/SHONA_TO_CHECK.md`. You are the native speaker: read them before the pitch.
- **Not in Ndebele.** The recogniser could not write it.

## Hard questions

**What if it mishears?** The nurse sees the patient's own words beside the note and can play the
recording. The note has a line for anything that looks misheard. And the rules read both the
Shona and the model's English, so a danger sign has two chances to be caught.

**What if it misses an emergency?** It can. On statements it had never seen, the rules alone
missed 13 of 24; the models caught those. So the design assumes any one check will fail: four vote
and the highest wins. It is a quick check before the nurse, not instead of her. Today the patient
at the back of the bench gets no check at all.

**What if the AI is down?** The rules still run, the fixed questions are still asked in a fixed
order, and the visit goes to the nurse marked urgent, never routine. We tested that today without
meaning to: the gateway returned 504 errors for a batch of notes, and every one of those visits
showed as urgent with the transcript.

**Can it give wrong medical advice?** It has no words for advice. The model chooses a topic; the
sentence spoken is one of 28 written in advance. An independent review of our code found that a
model reply shaped like a question could still carry advice, so we removed the model's words
entirely.

**Does it over-call emergencies?** Yes, somewhat, on purpose. Six of 24 ordinary visits in the
held-out set were pushed ahead. We narrowed one WHO rule that would have made every fever with a
headache an emergency. A clinician should decide where that line sits.

**Where does patient data go?** Each sentence is sent to CAIMEx to be written down and read, by
models the catalogue lists as hosted in Zimbabwe. The saved recordings stay on the clinic's own
machine and are deleted after 24 hours. The demo uses no real patient.

**Whose voice is that?** "Getrude", a voice offered by the CAIMEx voice model. It is synthetic and
labelled so. Confirm with the organisers that the team may use it.

**Why not just use ChatGPT?** It will answer medical questions, and it does not run in the
country. Mukoti is built so that it cannot answer them, and it calls only models the catalogue
lists as hosted here.

**How is this different from a chatbot?** A chatbot writes its own answers. This one cannot. And
its output is not for the patient: it is a queue for a nurse.

**What does it cost?** About 4 cents a visit on CAIMEx at today's list prices, nearly all of it
speech recognition, which is listed at $0.2247 a minute. That price is the lever: we have logged
it as an issue.

**Who pays?** Clinic groups, medical aids and the Ministry. The same engine fits any reception
desk where the first minutes are the same questions.

**Is the danger-sign list yours?** The signs are drawn from four WHO publications, named beside
each sign on the Engine page. The Shona patterns that detect them are ours. Three signs have no
published source and are marked as our own caution: thoughts of self-harm, blood in the stool,
urine, vomit or cough, and a "yes" when asked about bleeding.

**What about people who cannot hear, or will not talk to a machine?** They go to the nurse as they
do today. Mukoti is a second door, not the only one. There is also a typing option.

**Can someone who cannot read use it?** That is who the pictures are for. Every question is spoken
aloud and shown as a picture; the words come third. Be exact about the evidence: an AI reader named
the meaning of all 26 pictures from the pictures alone, half as guesses. No patient has tried them.

**Who drew the pictures?** AI coding agents, to our brief. Three drew a set each, blind readers
compared them, and the winner was redrawn with the others' best ideas. No icon library is used.
The record is `design/README.md`.

**Why Shona only?** And English. The recogniser returned nonsense for Ndebele in our test, so we
left it out rather than fake it. It is issue 18 in our log.

**What did you actually build today?** All of it: the server, five screens, the rules, 133 tests,
two evaluations, and the issue log. The first version this morning let the model write its own
questions and counted costs wrongly; a code review and a billing check this afternoon changed
both.

## What changed during the day, and why

You may be asked how the design got here. These are the decisions that mattered.

1. **The helper speaks only fixed sentences.** First the model wrote the questions and our code
   checked they looked like questions. A review showed advice could hide inside a question. Now
   the model chooses a topic and the sentence is ours.
2. **The browser records WAV.** CAIMEx billed a browser recording at three times its length, and
   not every browser can play that format back to the nurse.
3. **The second opinion is capped.** A small model reading the note may move a visit ahead of the
   queue, but cannot sound the alarm alone.
4. **A missing note means urgent.** The first version left such a visit at routine.
5. **The note has a fallback.** If the reasoning call stalls, the note is written without
   reasoning. Today the gateway stalled often enough to need it.
6. **The helper is called "mubatsiri".** A design judge pointed out that the bot's lines were
   labelled "Mukoti" (nurse) while it told patients "the nurse is coming".
7. **One WHO rule was narrowed.** "Any two of confusion, stiff neck, fever, headache" made an
   ordinary fever with a headache an emergency.
8. **Answers count, not only words.** "Yes" to "are you struggling to breathe?" names no danger
   sign, so the rules now read the question too.

9. **Pictures before words.** The screens were mostly text. A patient who cannot read, and a judge
   at the back of the room, both need to see what is being asked. Each question now has a picture.
10. **The notice of a new emergency no longer takes over the screen.** It appears at the bottom
   with an Open button, so a nurse reading one patient's note is not pulled away from it.

## Before the pitch

**You**
- Read `docs/SHONA_TO_CHECK.md` aloud. Fix anything wrong in `app/prompts.py`, then restart.
- Run the demo once from `docs/DEMO.md`.
- Ask an organiser whether the Getrude voice may be used.

**The team, one job each**
1. **Shona.** Go through the 245 lines in `docs/SHONA_TO_CHECK.md` with you.
2. **Real voices.** Everyone opens `/check`, types five made-up complaints and says them. The
   Engine page then shows a real error rate per speaker. Replace the bracket on slide 9 with it.
3. **Clinical.** Find a nurse for ten minutes. Show her the danger-sign list on the Engine page
   and the note. Write down what she would change. One quoted sentence from her is worth a slide.
4. **Demo.** Rehearse `docs/DEMO.md` twice, including the "if something goes wrong" table.
5. **Pitch.** Put the team's names on the last slide and time the talk.

## Where to look when asked

| Asked about | Open |
|---|---|
| How CAIMEx is used | The Engine page |
| A specific patient | The nurse's queue; "How CAIMEx handled this visit" at the bottom of the note |
| The sources | `docs/SOURCES.md` |
| The numbers | `eval/results.json`, `eval/heldout_results.json`, or the Engine page |
| The pictures | `design/README.md`; the pictures themselves are in `web/art/` |
| What broke | `CAIMEX_ISSUES.md`, or the bottom of the Engine page |
