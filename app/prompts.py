"""Every sentence the helper can say, and the prompts for the models.

The helper never speaks a model's words. The chat model chooses a TOPIC, and
the sentence spoken for that topic is the one written here. So what a patient
hears was written by a person in advance, and can be read and corrected once.

The Shona is everyday mixed Shona: a Shona sentence with the English words people use in it
("Zviri kuita worse here?"). Every Shona line here was written by an AI assistant and must be read by a
native speaker before real use. They are short on purpose: each is read aloud.
"""

from __future__ import annotations

MAX_QUESTIONS = 6

LANG_NAME = {"sn": "Shona", "en": "English"}

LINES = {
    "sn": {
        "greeting": ("Mhoroi, welcome kuClinic. Ndiri helper yaNurse, handisi doctor. "
                     "Ndichakubvunzai maQuestions mashoma kuti nurse akurumidze kukubatsirai. "
                     "Chii chakuunzai nhasi?"),
        "repeat": "Sorry, handina kunzwa zvakanaka. Please dzokororai.",
        "closing": "Thank you. Ndaudza nurse zvamataura. Please garai mumirire, nurse achakudaidzai.",
        "alarm": "Thank you. Ndiri kudaidza nurse izvozvi. Please garai pano, nurse ari kuuya.",
    },
    "en": {
        "greeting": ("Hello, welcome to the clinic. I am the nurse's helper, not a doctor. "
                     "I will ask you a few short questions so the nurse can help you sooner. "
                     "What brings you here today?"),
        "repeat": "Please say that again, I did not hear you well.",
        "closing": "Thank you. I have passed this to the nurse. Please take a seat, the nurse will call you.",
        "alarm": "Thank you. I am calling the nurse now. Please stay here, the nurse is coming.",
    },
}

# What the screen shows while the greeting is spoken: only its question, so the
# patient is not handed a paragraph to read. The whole greeting is still said aloud.
GREETING_SHOWN = {"sn": "Chii chakuunzai nhasi?", "en": "What brings you here today?"}

# topic -> the question, word for word. A "_child" variant is spoken when the
# sick person is a child brought by an adult.
BANK = {
    "sn": {
        "who": "Ndiani ari kurwara, imi here kana mwana?",
        "age": "Mune makore mangani?",
        "age_child": "Mwana ane makore mangani?",
        "onset": "Zvakatanga rini?",
        "worse": "Zviri kuita worse here?",
        "where": "Pain iri papi?",
        "severity": "Pain yacho yakanyanya here?",
        "fever": "Muri kupisa muviri here?",
        "fever_child": "Mwana ari kupisa muviri here?",
        "breathing": "Mune problem yekufema here?",
        "breathing_child": "Mwana ane problem yekufema here?",
        "drinking": "Mwana ari kugona kunwa kana kuyamwa here?",
        "vomiting": "Muri kurutsa here?",
        "vomiting_child": "Mwana ari kurutsa here?",
        "fits": "Pane maFits here?",
        "bleeding": "Pane ropa ramuri kuona here?",
        "neck": "Mutsipa wenyu wakaoma here?",
        "pregnancy": "Muri pregnant here?",
        "chronic": "Mune chronic condition here, seSugar kana BP?",
        "chronic_child": "Mwana ane chronic condition here?",
        "medicines": "Pane mishonga yamuri kunwa mazuva ano here?",
        "medicines_child": "Pane mishonga iri kunwiwa nemwana mazuva ano here?",
        "allergy": "Mune allergy kune mumwe mushonga here?",
        "other": "Pane chimwe chiri kukunetsai here?",
    },
    "en": {
        "who": "Who is unwell, you or a child?",
        "age": "How old are you?",
        "age_child": "How old is the child?",
        "onset": "When did it start?",
        "worse": "Is it getting worse?",
        "where": "Where is the pain?",
        "severity": "Is the pain very bad?",
        "fever": "Do you have a fever?",
        "fever_child": "Does the child have a fever?",
        "breathing": "Are you struggling to breathe?",
        "breathing_child": "Is the child struggling to breathe?",
        "drinking": "Is the child able to drink or breastfeed?",
        "vomiting": "Are you vomiting?",
        "vomiting_child": "Is the child vomiting?",
        "fits": "Have there been any fits?",
        "bleeding": "Have you seen any blood?",
        "neck": "Is your neck stiff?",
        "pregnancy": "Are you pregnant?",
        "chronic": "Do you have a long-term illness, such as diabetes or high blood pressure?",
        "chronic_child": "Does the child have a long-term illness?",
        "medicines": "Are you taking any medicines these days?",
        "medicines_child": "Is the child taking any medicines these days?",
        "allergy": "Is there any medicine that does not agree with you?",
        "other": "Is anything else troubling you?",
    },
}

# ── Spoken outside the talk ─────────────────────────────────────────────────
# These are not part of the interview and no model sees them. {n} is the ticket number.

# Calling a ticket in the waiting room.
CALLS = {
    "sn": {"nurse": "Ticket {n}, please endai kuna nurse.",
           "doctor": "Ticket {n}, please endai kuna doctor.",
           "pharmacy": "Ticket {n}, please endai kuPharmacy."},
    "en": {"nurse": "Ticket {n}, please go to the nurse.",
           "doctor": "Ticket {n}, please go to the doctor.",
           "pharmacy": "Ticket {n}, please go to the pharmacy."},
}

# How to take a medicine, said at the pharmacy. The keys are the doctor's choices.
HOW_SAY = {
    "sn": {"Once a day": "Shandisai mushonga uyu once a day.",
           "Twice a day": "Shandisai mushonga uyu twice a day.",
           "Three times a day": "Shandisai mushonga uyu three times a day.",
           "When needed": "Shandisai mushonga uyu only when needed.",
           "As directed": "Shandisai mushonga uyu sezvamaudzwa naPharmacist."},
    "en": {"Once a day": "Use this medicine once a day.",
           "Twice a day": "Use this medicine twice a day.",
           "Three times a day": "Use this medicine three times a day.",
           "When needed": "Use this medicine only when you need it.",
           "As directed": "Use this medicine as the pharmacist has told you."},
}

# A warning for a community, said in the waiting room or sent as a voice message when the national
# picture shows a risk for the province. One fixed sentence for each illness.
WARN_SAY = {
    "sn": {"diarrhoeal": "Warning: maCases emanyoka ari kuwanda muArea yenyu. Boilai mvura yekunwa, mugeze maoko neSoap.",
           "malaria": "Warning: malaria iri kuwanda muArea yenyu. Rarai muNet, muuye kuClinic kana muine temperature.",
           "respiratory": "Warning: maChest infections ari kuwanda. Uyai kuClinic kana mwana aine problem yekufema."},
    "en": {"diarrhoeal": "Warning: diarrhoea is spreading in this area. Boil your drinking water and wash your hands with soap.",
           "malaria": "Warning: malaria is rising in this area. Sleep under a net, and come to the clinic if you have a fever.",
           "respiratory": "Warning: chest infections are rising. Come to the clinic if a child is struggling to breathe."},
}

# Said to staff at the nurse's station, in English. {sign} is a fixed danger-sign label.
ALARM_SAY = "Emergency. Ticket {n}. {sign}."

# What one question is about. "main" is the greeting's own question.
ASKABLE = tuple(k for k in BANK["en"] if not k.endswith("_child"))
TOPICS = ("main", *ASKABLE)

# If the chat model fails, the helper still finishes the visit from this order.
FALLBACK_ORDER = ("who", "age", "onset", "worse", "breathing", "chronic", "medicines")


def english_of(lang: str, text: str) -> str | None:
    """The English of a line the helper said, for the captions."""
    if lang == "en":
        return None
    for key, line in LINES[lang].items():
        if line == text:
            return LINES["en"][key]
    for key, line in BANK[lang].items():
        if line == text:
            return BANK["en"][key]
    return None


def fixed_lines(lang: str) -> list[str]:
    """Every line the helper can say. All of them are synthesised at start-up."""
    return [*LINES[lang].values(), *BANK[lang].values()]


def everything_the_helper_can_say() -> set[str]:
    return {line for lang in LINES for line in fixed_lines(lang)}


def interview_system(lang: str, last: str = "", covered: tuple = ()) -> str:
    """`last` is the patient's newest message, repeated at the end so the model
    translates that one and not an earlier line (it did, without this).
    `covered` is what the patient has already told us, so it is never asked again."""
    name = LANG_NAME[lang]
    bank = "\n".join(f"- {k}: {BANK[lang][k]}" for k in ASKABLE)
    return f"""You are the intake helper at a primary care clinic in Zimbabwe. A patient, or the \
adult who brought a child, is answering questions in {name}. Your job is to choose which question \
is asked next, so that the nurse has what she needs before she sees them. You are not a clinician.

You do not write the questions. You choose a topic, and the clinic's own fixed sentence for that \
topic is spoken. These are the topics and their sentences:
{bank}

What the nurse needs, in this order of importance. Ask as FEW questions as you can, and never \
more than {MAX_QUESTIONS}. Two or three good questions are better than six.
1. Who is sick (the speaker or a child) and the age.
2. One or two danger signs that fit THIS problem: breathing, fever, drinking (for a small child), \
vomiting, fits, bleeding, neck, and pregnancy for a woman of childbearing age.
3. When it started, and whether it is getting worse.
4. Long-term illness, medicines taken now, allergies: only when the visit is about a medicine or \
a long-term illness, or when nothing above is left to ask.

A patient often answers several of these in one message. Read EVERY patient message for what it \
already tells you, and list those topics in "answered". Examples: "My chest hurts" answers "who" \
(the speaker). "My child of three has had a fever since yesterday" answers "who", "age", "fever" \
and "onset". "I am 21 and I broke my leg just now, I cannot walk" answers "who", "age", "onset", \
"where" and "severity". A message can answer a topic by saying no ("she is not vomiting").

Rules for choosing:
- Never choose a topic that is in "answered", that the patient has already answered in any \
message, or that has already been asked. Asking again makes a sick person repeat themselves.
- Stop early: set "done" to true as soon as you know who is sick, the age, and the danger signs \
that fit the problem. Do not ask "other" unless the visit is not about an illness.
- If the patient repeats what they already said, says they have already told you, is upset, or \
asks to see the nurse now, set "done" to true. Do not ask anything more.
- Never choose a topic that cannot apply: no "pregnancy" for a man, a child or a woman past sixty; \
"drinking" only when the sick person is a small child.
- Always find out the age.
- If nobody is ill (a repeat prescription, an injection, an immunisation, a check-up), ask only \
"age", "other" and "medicines", then finish.
- When you have enough, or nothing useful is left to ask, set "done" to true.

Emergencies: set "alarm" and "done" to true only if they report one of these: cannot be woken; \
severe trouble breathing; fits; heavy bleeding that will not stop; any bleeding in pregnancy; \
strong chest pain; a child under five who cannot drink or breastfeed or vomits everything; a baby \
under two months who is hot or not feeding; poisoning; a snake bite; a stiff neck together with \
fever or headache; thoughts of self-harm.
Anything else is not an alarm, even when it sounds serious: a burn, a broken bone, a fall, \
coughing blood, fainting, strong pain. For those keep "alarm" false and go on asking. The nurse \
will see them ahead of the queue.

Speech recognition wrote the patient's words, so they may contain errors.

Reply with one JSON object and nothing else:
{{"heard_en": "<the patient's last message in plain English, faithfully, adding nothing; Shona does not say whether a person is a he or a she, so write "they" or "the child" unless the patient's words make it plain>",
 "answered": [<every topic the patient has answered so far, in any message: {', '.join(ASKABLE)}>],
 "topic": "<the topic to ask next, which must NOT be in "answered": one of {', '.join(ASKABLE)}>",
 "done": <true or false>,
 "alarm": <true or false>,
 "alarm_reason_en": "<short English reason, or empty>"}}""" + (
        f"""

Already answered in earlier messages (never ask these again): {', '.join(covered)}""" if covered else "") + (
        f"""

The patient's last message, the one to put into English for "heard_en", is:
{last}""" if last else "")


NOTE_SYSTEM = """You write the intake note a clinic nurse in Zimbabwe reads before seeing a \
patient. You are given a conversation between an intake helper and the patient (or the adult who \
brought a child), in Shona or English. Speech recognition wrote the patient's lines, so they may \
contain errors.

Rules:
- English, short, factual. Use only what the patient said. If something was not asked or not \
answered, write "not stated". Do not guess.
- Do not diagnose and do not suggest treatment. You may list what the nurse should check.
- Never guess whether the patient is a woman or a man. You cannot hear the voice, and Shona has \
one word for "he" and "she". State the sex only when the patient's own words give it: a pregnancy, \
her periods, "my son", "my daughter", "my husband", "my wife", "murume wangu", "mukadzi wangu". \
Otherwise write "the patient" or "the child" and use "they" and "their" everywhere in the note and \
in "transcript_en"; do not write "he", "she", "his", "her", "woman", "man", "male" or "female", and \
do not write that the sex is unknown or not stated. The speaker being a mother says nothing about \
the sex of her child.
- Urgency is one of "emergency", "urgent" or "routine". Use these definitions, which follow the \
WHO, ICRC and MSF Interagency Integrated Triage Tool and the WHO IMCI danger signs:
  "emergency" (a clinician now): unresponsive or cannot be woken; struggling to breathe; \
convulsions; heavy bleeding; poisoning or a snake bite; a serious injury; acute chest pain or \
abdominal pain in someone over 50; a stiff neck or confusion together with fever or a headache; a \
pregnant woman with bleeding, severe abdominal pain, fits, a severe headache or changes in her \
sight; a child under five who cannot drink or breastfeed, vomits everything, has had convulsions \
or is very drowsy; a baby under two months with fever or not feeding; thoughts of self-harm.
  "urgent" (ahead of the queue): wheezing; cannot keep fluids down or diarrhoea that will not \
stop; fainted recently; confused; sudden weakness or loss of sight; severe pain; a severe headache \
with a high fever; a burn, a broken \
bone or another injury; sexual assault; an animal bite; a pregnant woman with any other \
complaint; a baby under six months who is ill; blood in the stool, urine, vomit or cough; an \
infected wound in someone with diabetes.
  "routine": everything else, including long-standing complaints that are not getting worse, and \
an ordinary fever, headache, cough or cold with none of the signs above.
  If the patient fits two levels, give the higher. Do not raise a level only because you are \
unsure: an "urgent" patient is already seen ahead of the queue.
- "red_flags" holds only danger signs the patient said they HAVE. A sign they said they do not \
have is not a red flag: put it in "history" (for example "No difficulty breathing").
- "unclear" is only for a patient line that is nonsense, contradicts another line, or does not \
answer the question asked. A clear, plausible line is not unclear. Most visits have none: use [].

Reply with one JSON object and nothing else:
{"patient": "<who is sick and the age, for example \"Adult, 32 years\" or \"Child, 8 months, brought by the mother\"; the sex only if the patient's words give it>",
 "chief_complaint": "<one line>",
 "history": ["<short fact>", "..."],
 "red_flags": ["<danger sign the patient reported>", "..."],
 "urgency": "emergency|urgent|routine",
 "urgency_reason": "<one sentence>",
 "check_next": ["<what the nurse should ask or measure first, most important first, at most 5>"],
 "unclear": ["<what may have been misheard>", "..."],
 "transcript_en": ["<English translation of each PATIENT line, in order>", "..."]}"""


# The second opinion: a different, small model reads the English note cold.
SECOND_OPINION = {
    "urgency": {
        "type": "score",
        "instructions": "How urgently does this clinic patient need to be seen by a nurse?",
        "criteria": ["Routine: can wait in the queue",
                     "Urgent: see soon, ahead of the queue",
                     "Emergency: needs a clinician now"],
    },
}
