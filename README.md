<img src="web/icon.svg" width="64" height="64" alt="">

# Mukoti

The first person every patient talks to at the clinic, in Shona or English.

A patient speaks. Mukoti asks up to six short questions aloud, then gives the nurse a note in
English and a queue with the most urgent patient at the top. Every model it calls is listed by the
CAIMEx gateway as hosted in Zimbabwe.

Mukoti does not diagnose and does not advise treatment. It is a quick check at reception; the
nurse decides. "Mukoti" is Shona for nurse: the product is the nurse's helper, and calls itself
"mubatsiri" (helper) when it speaks. Built for the Econet AI hackathon, 25 November 2026.

## Run it

```bash
echo 'CAIMEX_API_KEY=sk-or-...' > .env     # never commit this file
./run.sh                                    # or: uv run uvicorn app.server:app --port 8000
```

| Screen | Address | Who it is for |
|---|---|---|
| Welcome | http://127.0.0.1:8000/welcome | Anyone new: what Mukoti is, and a link to every screen |
| Demo | http://127.0.0.1:8000/demo | A room: the patient and the nurse side by side |
| Patient | http://127.0.0.1:8000 | The patient, on a phone or tablet at the door |
| Nurse's queue | http://127.0.0.1:8000/nurse | The nurse |
| Engine | http://127.0.0.1:8000/engine | Judges: how CAIMEx is used, with live numbers |
| Voice check | http://127.0.0.1:8000/check | The team: test the recogniser on real voices |

Start it two minutes before a demo: at start-up it speaks every fixed sentence once and saves it.
The demo itself is scripted in `docs/DEMO.md`.

A microphone only works on `127.0.0.1` or over HTTPS, so a phone on the same Wi-Fi cannot use the
patient screen from a plain `http://` address.

## A picture for every question

Every question the helper asks comes with a picture: a body with a ring for "where does it hurt",
a clock running back for "when did it start", lungs for breathing. The patient hears the question,
sees the picture and reads the words, in that order of importance, so someone who cannot read is
not left out. A trail of small pictures shows how far the talk has got. The nurse's queue uses the
same pictures, so she sees what a visit is about before she reads a word.

There are 26, in `web/art/`: drawn for Mukoti, animated, coloured from six variables so they follow
the light and dark looks, and still when the phone asks for less motion. Three AI coding agents
each drew a set from one brief; blind readers chose between them; the winner was redrawn with the
others' best ideas. A fresh AI reader then named the intended meaning of 26 of 26 from the pictures
alone, half of them as guesses. No patient has seen them yet. The record is `design/README.md`.

## Not asking twice

On real test visits the helper asked "Who is unwell, you or a child?" after "my chest hurts", and
went on questioning a patient who had said everything in the first message and was answering
"I said my leg is broken". Three things now prevent that (`app/visits.py`, `app/prompts.py`):

- **The chat model lists what is already answered** on every turn (`"answered"`), reading every
  patient message, and is told to ask as few questions as it can. Nothing on that list is asked,
  by the model or by the fixed order.
- **The patient's own words are read without the model too**, so the fixed order also skips
  what was said when the model does not answer: "I", "my" or "my child" answers who is sick; an
  age, a time ("since yesterday") or "getting worse" answers those.
- **A patient who repeats themselves is not asked again.** If a message is much the same as an
  earlier one, or says "I said" or "I want to see the nurse", the helper thanks them and hands
  over. A bare "yes" or "no" twice is not counted as a repeat.

Measured: replaying four of those real openings (typed), the broken-leg patient was handed over
after 2 turns instead of 5, and "who is unwell" was not asked in any of them. On the 30 sample
patients the average barely moved (4.1 turns to 4.0), because each sample line answers one
question at a time, so the samples do not show the gain. No count of saved questions on real
patients exists yet.

## The patient's details, without a name

The team asked for name, age, weight and height to be ready before the nurse sees the patient.
Three other agents were asked for a design (Codex, Antigravity, Cursor); this is what they agreed on.

- **No new spoken question.** Each one costs speech recognition and a turn of the six.
- **Age** is already asked. `app/details.py` reads the number out of the answer with fixed Shona
  and English number tables, with no model. It is shown as "said by the patient, confirm".
  "Mwedzi mitatu" stays three months and never becomes three years. Outside the age question a
  number counts only when the words say someone has that age, so "three days ago" is not an age.
- **Blood pressure** is keyed as upper over lower (120/80). A slip such as 80/120 or 400/80 is
  refused. A reading of 180 upper or 120 lower and above, or under 90 upper, is kept with a
  warning to measure again and tell the nurse. Those limits are the commonly used ones; no
  clinician has reviewed them, and the warning does not change the level.
- **Weight, height and sex** are never taken from speech. Staff key them in on `/vitals` against
  the ticket number, and they show as "measured". Outside 1 to 250 kg or 45 to 220 cm a value is
  refused. A child keyed above 40 kg is kept with a warning to weigh again.
- **No name is kept.** The ticket number links the visit to the clinic's own register.
- The details sit beside the note. They cannot change the level, and no model is sent them.
  Both are tests. An emergency ticket cannot be opened on the vitals page: it goes straight to the nurse.

Screenshots: `docs/screens/4_details_*.png`.

**Not done.** No nurse or aide has used the vitals page, and no time saving has been measured.
The Shona number words were written by an AI assistant and need a native speaker. The nurse page
has no control yet to correct a misheard age (the server accepts one). A low weight for a
child's age is not flagged: that needs the WHO weight-for-age tables.

## From the door to the pharmacy

The team asked for the whole path, not only intake. Each step has its own screen, and the ticket
number carries the patient between them.

| Step | Screen | What happens |
|---|---|---|
| Helper | `/` | The patient speaks; the helper asks its fixed questions (the CAIMEx models) |
| Vitals | `/vitals` | An aide keys in weight, height, blood pressure and sex, and may take a photo |
| Nurse | `/nurse` | Reads the note and the four checks, sets the level, marks the patient seen |
| Doctor | `/doctor` | Sees the note and the vitals; types the diagnosis and the prescription |
| Pharmacy | `/pharmacy` | Dispenses what was prescribed; anything else needs the supervisor |

- **The doctor decides.** On request a CAIMEx model lists what to rule out; the doctor types
  or accepts the diagnosis and writes the prescription. The model never suggests a medicine.
  The evaluation of the intake models is unchanged.
- **Only what was prescribed leaves the shelf.** A medicine not on the prescription, more than
  was prescribed, or a second supply is refused without the supervisor's PIN and a reason.
- **Use by diagnosis.** Each dispensing carries the doctor's diagnosis, so the stock list shows
  what each medicine is mostly going to.

**Not done.** Every member of staff shares one login, so the screens are not separated by
role. There is no patient record across visits: a visit is deleted after 24 hours. There are no
laboratory, ward, billing or referral modules. No doctor, nurse or pharmacist has used this, and
the list of quick-pick diagnoses and medicines is a made-up starter list.

## Speech beyond the talk

The voice and the recogniser are used in four more places (`app/voice.py`, `tests/test_voice.py`):

- **The waiting-room board** (`/board`) shows and says "Ticket 14, please go to the doctor", in
  the patient's language first, then the other. A patient is called automatically when the
  nurse marks them seen and when the doctor sends a prescription; the nurse can also call one.
- **How to take a medicine** is said to the patient at the pharmacy, in Shona or English: one
  of five sentences written in advance, chosen by the doctor's "how taken".
- **A new emergency is said aloud** at the nurse's station after the chime, with the ticket and
  the danger sign.
- **The doctor can dictate the diagnosis.** The text appears in the box to be checked; nothing
  is saved until the doctor sends it.

Everything said to a patient is a fixed sentence with only the ticket number put in. The Shona
voice read the digits "14" as "one four", so ticket numbers are written out in Shona words
("gumi nemana"). Those number words and the nine new Shona sentences were written by an AI
assistant and have not been read by a native speaker. None of the four has been tried in a
waiting room, and the board, the instructions, the alarm and dictation have only been tested
with the models replaced by fakes, not yet heard through a speaker.

## CAIMEx across the whole system

The team asked for less fixed logic and more of CAIMEx. The chat model now does six more jobs
(`app/ai.py`, `tests/test_ai.py`), all through the same gateway:

| Where | What the model does | Measured on 2026-11-26 |
|---|---|---|
| Forecast and Zimbabwe | Writes the morning briefing from the computed numbers, explains one warning, and drafts the alert | 5 to 30 s each |
| Pharmacy | Reads the shelf together with the outbreak watch and ranks what to order first | about 8 s, about $0.0007 |
| Doctor | On request, lists what to rule out, what not to miss and what to ask or examine, from the note, the vitals and what is rising in the patient's area | about 12 s with reasoning |
| Each visit | Sorts the visit into a symptom group for the tally | 0.3 to 2 s |

Those timings are single runs on the made-up tally, not averages.

What stays fixed, and why:

- **The danger-sign rules stay** as one of the four checks. They answer when the gateway does
  not, and on the held-out set the rules and the models each caught what the other missed.
- **Arithmetic stays arithmetic.** Forecasts, risk scores and days of stock left are computed
  by our own code. A first version let the chat model estimate next week's cases; both agents
  asked to review it said to stop, and it now only explains numbers it is given.
- **The model never names a medicine or a dose**, never fills in the prescription, never
  changes an urgency level, and nothing it writes is spoken to a patient. On the doctor's page
  its suggestion reaches the diagnosis box only when the doctor presses "Use", and the record
  notes that the wording came from the model.

**Not done, and what did not work.** None of these four jobs has been evaluated: there is no
set of real outbreaks, stock-outs or diagnoses to score them against, so nothing here supports
a claim of accuracy. A language model reading counts is not a validated epidemic forecaster.
With reasoning switched on, a large table of counts ran for two minutes and the gateway answered
504, so the briefing runs without reasoning. The decision model was tried as a second score for each
flagged area and gave a clear rise only 36 to 40%, so it was left out. General chat models are
used, not a medical one: the catalogue no longer lists `medgemma-27b-it`.

## Prediction: today, next week, and the country

Asked for by the team: predict before patients arrive, use evidence beyond one clinic, and show
it on a map of Zimbabwe (`app/prediction.py`, `app/national.py`, `web/outbreaks.html`,
`web/national.html`, `tests/test_prediction.py`).

**Who does what.** Our own arithmetic computes every number. CAIMEx puts the numbers into words,
explains a warning, drafts the alert and reads the briefing aloud. A sentence from the model that
holds a number we did not compute is not shown (`ai.numbers_ok`).

**This clinic** (the Forecast page):

- **Today, before the doors open:** expected arrivals for each symptom group, with a likely
  range and the usual, from the clinic's own last twelve weeks and its weekday pattern.
- **Where an illness is rising:** each ward and symptom group is compared with its own usual,
  learnt from days 15 to 70 ago so that a rise already under way does not become "the usual".
- **Next seven days:** a forecast with the middle 80% as its range, drawn on each card.
- **Go back in time:** a slider replays the last 21 days using only what was known each day.
- **The shelf:** how many days of a medicine are left at the usual use, and if the rise goes as
  forecast. The units per extra patient is a planning figure staff can move, not a treatment rule.

**The country** (the Zimbabwe page): a risk score from 0 to 100 for each province and three
illnesses, with every point shown and labelled by where it came from.

| Evidence | Source | Real? |
|---|---|---|
| Rainfall and temperature, last 8 weeks and next 7 days | Open-Meteo, at each province's centre point | Real, refreshed every six hours |
| Province boundaries | geoBoundaries (ZIMSTAT and OCHA ROSEA), simplified | Real |
| Water points reported broken or unsafe | none found | Made up |
| Cases reported by clinics, and outbreaks already reported | none used | Made up |
| How established malaria is in each province | our reading of general knowledge | Our estimate |

A clinic sees its own province's warnings on its Forecast page (`MUKOTI_PROVINCE`, default
Manicaland), and the fixed Shona warning for a community can be played.

**How well the clinic forecaster does** (`tools/evaluate_prediction.py`,
`eval/prediction_results.json`). No real patient data may be used and we know of no open
ward-level series for Zimbabwe, so it is scored on simulated clinics with outbreaks planted at
known days. Settings were chosen on 12 clinics and scored on 30 others.

| On the 30 unseen clinics | This forecaster | A simple weekly count |
|---|---|---|
| Planted outbreaks flagged within 14 days | 203 of 235 | 207 of 235 |
| Days from start to flag, middle case | 8 | 8 |
| False alarms a ward a year | 3.72 | 5.57 |

| Forecast of next week's cases | Average error, cases a week |
|---|---|
| This forecast | 1.721 |
| "Same as last week" | 2.171 |
| "The usual" | 1.786 |

89% of weeks fell inside the stated range; during outbreaks only 64% did.

**Read this with care.**

- The forecaster is not faster than a weekly count and catches slightly fewer outbreaks. Its
  gain is about a third fewer false alarms, a forecast that beats "same as last week", and a range.
- The simulator was written by the same hand as the forecaster. This shows the arithmetic
  behaves; it is not validation on real outbreaks.
- During a real rise the range is too narrow about a third of the time.
- The national score has not been evaluated at all. Its weights are ours, not fitted to data
  and not reviewed by an epidemiologist. It ranks provinces; it is not a probability.
- Real weather is mixed with made-up water and case numbers on one map. Each is labelled, but a
  screenshot of the map alone could mislead: the red province is red because of made-up cases.
- The nine wards and their map are made up. Weather is taken at one point per province.
- "Confirmed" in a ward means the clinic doctor's diagnosis of that kind of illness, not a
  laboratory result.
- Nothing is sent anywhere. The drafted text message and note are for a person to check and send.

## Revenue and pharmacy controls

Asked for by the team: stop a medicine or a fee waiver being claimed twice, and see a stock-out
coming. Built with no model in it (`app/pharmacy.py`, `web/pharmacy.html`, `tests/test_pharmacy.py`).

- **A photo on the ticket.** On `/vitals` staff can take one photo with the tablet's camera. It
  is stored beside the recordings and deleted with the visit. When a medicine is dispensed, the
  pharmacy page shows that ticket's photo beside the photos of everyone else given the same
  medicine, and asks "is this the same person?". A person compares the faces. Nothing in Mukoti
  matches faces, and there is no fingerprint reader.
- **Two people for the risky steps.** A fee waiver, a second supply of a medicine on one ticket,
  and any change to a stock count are refused without the supervisor's PIN and a reason. Each is
  listed under "Signed by the supervisor today". Eight wrong PINs lock approvals for five minutes.
- **When each medicine runs out.** Days left = stock on the shelf ÷ average use a day over the
  last 14 days. A medicine is flagged "order soon" under four weeks and "order now" under two.
- One supply is 1 to 200 units and never more than the shelf holds.

**What this is not.** The stock history a new installation starts with is made up and marked so
on the page. Use is counted by medicine dispensed, not by diagnosis, because Mukoti does not
diagnose. The fee is a status (not paid, paid, waived) with no amounts and no link to a till.
The supervisor's PIN defaults to 2468 for a demo: set `MUKOTI_SUPERVISOR_PIN`. The supervisor
and the nurse share one login, so the PIN is the only thing that separates them. A photo of a
real patient is personal data: use teammates or no photo in a demonstration, and real use needs
the patient's consent and the clinic's approval. Nobody at a pharmacy has used this.

## What happens to one sentence

1. The browser records the patient as WAV and stops by itself when they stop talking.
2. `languages-lab-stt-large-1.3` writes down the Shona or English (`/v1/audio/transcriptions`).
3. **Mukoti's own code** reads the sentence against fixed danger-sign rules (`app/triage.py`). An
   emergency ends the questions at once and alerts the nurse. A bare "yes" to "are you struggling
   to breathe?" counts too.
4. `deepseek-v4-flash` chooses which question comes next, and writes the sentence in English so
   the rules can read it a second time (`/v1/chat/completions`).
5. **Mukoti's own code** speaks the fixed sentence for that topic (`app/prompts.py`). The model's
   own words are never spoken, so the helper cannot give advice or a diagnosis.
6. `languages-lab-tts-large-1.3`, voice Getrude, made that sentence once at start-up
   (`/v1/audio/speech`).

When the talk ends, `deepseek-v4-flash` (with reasoning) writes the nurse's note, and `d3-nano`
gives a second opinion with a score for each level (`/v1/decisions`).

## The four checks

| Check | What it is | What it can do |
|---|---|---|
| Danger-sign rules | Fixed patterns, no AI, on the patient's own words, their English and their yes/no answers | Raise to urgent or emergency |
| Interview model | The chat model, during the talk | Sound the alarm |
| Note model | The chat model with reasoning, after the talk | Give any level |
| Second opinion | A smaller, different model reading the finished note | Raise routine to urgent, never more |

The level shown is the highest any check gives. If the note cannot be written, the visit is shown
as urgent, never routine. Only the nurse can lower a level, and her choice is recorded as hers.

## How well it works

All of this was measured on 25 November 2026. None of it is a clinical test.

**On statements it was never written against** (`eval/heldout.json`, `tools/heldout.py`). A
separate AI agent, not allowed to see the rules or prompts, wrote 60 things patients say at
reception. Each was given to Mukoti as a patient's only sentence, once, before any rule was
changed because of it.

| | The four checks together | The fixed rules alone |
|---|---|---|
| Emergencies given the emergency level | 24 of 24 | 11 of 24 |
| Urgent cases put ahead of the queue | 12 of 12 | 5 of 12 |
| Ordinary visits left as routine | 18 of 24 | 21 of 24 |

The rules were then extended using what they missed, so they can no longer be scored on this set.

**On our own 30 sample patients** (`samples/patients.json`, `tools/evaluate.py --spoken`), each
line spoken in a synthetic voice and then recognised:

| | Result |
|---|---|
| Visits completed | 30 of 30 |
| Patients given a lower level than they should have had | 0 |
| Emergencies given the emergency level | 11 of 11, 10 of them on the first sentence |
| Ordinary visits left as routine | 10 of 11 |
| Character error, synthetic voice heard back | 3.6% |
| From the end of the patient's sentence to the helper answering | about 2.5 s (1.4 s on 25 November) |
| Cost of a visit at list prices | $0.04, 98% of it speech recognition |

Rerun on 2026-11-26 after the helper was taught not to ask what the patient has already said
(see the next section). The levels did not change. The reply was slower: choosing the question
took 1.4 s against 0.7 s, partly because the prompt is longer and partly because the gateway was
slower that day (the unchanged note call also took twice as long). The held-out set was not rerun
through the pipeline after this change.

Read these with care:

- Both sets were written by AI, not collected from patients, and no clinician set the levels.
- The sample patients and the rules were written together, so that table only shows the pipeline
  holds together.
- Synthetic voices are easier to recognise than a person in a waiting room. Real voices are
  measured on the Voice check page, against a sentence the speaker typed.

Other checks: `uv run pytest` (256 tests: the rules, and each safety claim with the models
replaced by fakes), `uv run python tools/contrast.py` (every colour pair),
`uv run python tools/e2e.py http://127.0.0.1:8000 out "$PWD/tests/fixtures/shona_sentence.wav"` (a real browser with a fake
microphone), `uv run python tools/shots.py http://127.0.0.1:8000 out` (every screen).

## Responsible use

- **No personal data.** Demonstrate with the sample patients, which are made up and labelled so.
  Do not record real patients with this prototype.
- **Recordings** are kept so the nurse can check a line that looks misheard. They are deleted
  after 24 hours (`MUKOTI_KEEP_HOURS`), and the nurse can delete a visit at once.
- **The nurse's queue** can be put behind a PIN: set `MUKOTI_NURSE_PIN`. Without one, anyone who
  can reach the port can read and change the queue, so keep the server on `127.0.0.1`.
- **Synthetic voices.** Getrude and the sample patients' voices come from the gateway's voice
  model and are labelled synthetic wherever they are heard.

## Not done

- No clinician has reviewed the danger-sign list. Mukoti also departs from the WHO tool in one
  place, described in `docs/SOURCES.md`; that is the first thing to review.
- No patient has seen the pictures. They were read correctly by AI readers, which is not the same.
- No native speaker has checked the Shona. Every sentence is listed in `docs/SHONA_TO_CHECK.md`.
- Ndebele: the recogniser returned garbled text for it, so Mukoti offers Shona and English only.
- Visits are kept in a local file (`data/`). There is no sign-in beyond the optional PIN.
- The triage tool the rules draw on is licensed for non-commercial use. See `docs/SOURCES.md`.

## Where things are

| | |
|---|---|
| `app/` | The server: `visits.py` (the talk and the checks), `triage.py` (the rules), `prompts.py` (every sentence the helper can say), `gateway.py` (every CAIMEx call) |
| `web/` | The five screens. No build step, no framework |
| `web/art/` | The 29 pictures, one SVG each |
| `app/pharmacy.py`, `web/doctor.html`, `web/pharmacy.html` | The doctor's diagnosis and prescription, dispensing by ticket, the stock forecast, fee status and the supervisor's approvals |
| `app/prediction.py`, `app/surveillance.py`, `web/outbreaks.html` | The clinic forecaster, the nameless tally it reads, and the Forecast page |
| `app/national.py`, `web/national.html`, `web/zw_provinces.json`, `samples/weather_snapshot.json` | The national risk score, the Zimbabwe map, its boundaries and a dated copy of the weather |
| `tools/evaluate_prediction.py`, `eval/prediction_results.json` | The simulator that scores the forecaster, and its results |
| `web/help.js` | The Help steps on each staff screen |
| `app/details.py`, `web/vitals.html` | Age read from speech by fixed tables; weight, height and sex typed by staff against the ticket |
| `design/` | How the pictures were chosen: the brief, the three entries, the blind check |
| `docs/screens/` | Screenshots of the three stages of the look |
| `samples/patients.json` | The 30 made-up patients |
| `eval/` | The held-out set and the results of both evaluations |
| `docs/BRIEF.md` | What to know before presenting, and answers to hard questions |
| `docs/DEMO.md` | The demo, step by step |
| `docs/SOURCES.md` | Every source, with what was actually read |
| `docs/SHONA_TO_CHECK.md` | Every Shona sentence, for a native speaker |
| `CAIMEX_ISSUES.md` | The 24 issues we hit, for the CAIMEx team |

## Credits

Figtree typeface, SIL Open Font License 1.1 (`web/fonts/Figtree-OFL.txt`). Danger signs drawn from
WHO, ICRC and MSF publications listed in `docs/SOURCES.md`. The pictures and the mark were drawn
for Mukoti by an AI coding agent (Codex), with ideas from sets drawn by two others (Antigravity and
Cursor); no icon library or outside artwork is used. Built with Claude Code.
