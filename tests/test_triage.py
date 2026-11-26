"""The danger-sign rules. Shona examples were written by an AI assistant."""

import pytest

from app import triage


def keys(text, lang="sn"):
    return {r.key for r in triage.scan(text, lang)}


def level(text, lang="sn"):
    return triage.highest([r.level for r in triage.scan(text, lang)])


@pytest.mark.parametrize("text,key", [
    ("Mwana wangu ari kutadza kufema", "breathing"),
    ("Handisi kufema zvakanaka", "breathing"),
    ("Ari kunetseka kufema kubva nezuro", "breathing"),
    ("Mwana haasi kumuka", "unconscious"),
    ("mwana ane pfari", "convulsions"),
    ("Mwana ari kugwinha", "convulsions"),
    ("Mwana abatwa nepfari kaviri husiku", "convulsions"),
    ("Ropa riri kubuda rakawanda uye harisi kumira", "bleeding"),
    ("Mwana ane mavhiki matatu haasi kuyamwa", "cannot_drink"),
    ("Mwana haasi kunwa, ari kurutsa zvese", "cannot_drink"),
    ("Mwana haachagoni kuyamwa", "cannot_drink"),
    ("uye hachagoni kunwa mvura", "cannot_drink"),          # as the recogniser wrote it
    ("Mwana ari kutadza kunwa mvura", "cannot_drink"),
    ("Arumwa nenyoka pagumbo", "poison"),
    ("Mwana anwa parafini", "poison"),
    ("Ndiri kubuda ropa rakawanda", "bleeding"),
    ("Ndine pamuviri uye ndiri kubuda ropa", "pregnancy_bleeding"),
    ("Ndiri kufunga kuzviuraya", "self_harm"),
    ("Ndine musoro, ndiri kupisa muviri, uye mutsipa wangu wakaoma", "stiff_neck_fever"),
])
def test_emergency_signs_in_shona(text, key):
    assert key in keys(text)
    assert level(text) == "emergency"


@pytest.mark.parametrize("text,key", [
    ("Chipfuva chiri kurwadza zvakanyanya", "chest_pain"),
    ("Ndiri kurwadziwa muchipfuva", "chest_pain"),
    ("Mutsipa wangu wakaoma", "stiff_neck"),
    ("Akabva afenda mangwanani", "fainted"),
    ("Mbuya vangu vafenda kumba", "fainted"),
    ("Mwana wangu ane mavhiki matatu ane dzihwa", "young_baby"),
    ("Mwana ane manyoka ane ropa", "blood"),
    ("Ndakaita tsaona nezuro", "injury"),
    ("Mwana atsva nemvura inopisa paruoko", "injury"),
    ("Nezuro ndakosora ropa", "blood"),
])
def test_urgent_signs_in_shona(text, key):
    assert key in keys(text)
    assert level(text) == "urgent"


@pytest.mark.parametrize("text", [
    "Ndine musoro uri kurwadza kubva nezuro, ndiri kukosora",
    "Ndiri kufema zvakanaka",
    "Ndine manyoka kubva nezuro",
    "Handina chirwere chenguva refu. Handisi kunwa mushonga.",
    "Haasi kunwa mushonga",
    "Kwete, haasi kunetseka kufema",
    "Handisi kunetseka kufema",
    "Haana kufenda",
    "Haana pfari",
    "Ndine pamuviri. Hapana ropa randiri kuona.",
    "Handina pamuviri. Ndine musoro.",
    "Ndine chipfuva nedzihwa. Musoro uri kurwadza.",          # chipfuva here is a chesty cough
    "Musoro uri kurwadza zvakanyanya. Ndaona ropa shoma pamhino.",
    "Mwana ari kunwa zvakanaka uye ari kufema zvakanaka",
    "Ndauya kuzobaiwa jekiseni rekuronga mhuri",
    "Ropa rekumwedzi chete, harina kuwanda",
    "Ndine dzihwa nechipfuva kwemazuva matatu",
    "Ndave nemavhiki matatu ndichikosora",
    "Mwana ane makore matatu ane dzihwa",
])
def test_no_false_alarm_in_shona(text):
    assert triage.scan(text) == []


@pytest.mark.parametrize("text,key", [
    ("My baby is struggling to breathe", "breathing"),
    ("She cannot breathe properly", "breathing"),
    ("He had a seizure this morning", "convulsions"),
    ("She will not wake up", "unconscious"),
    ("I have a stiff neck and a fever", "stiff_neck_fever"),
    ("The child is not drinking and vomits everything", "cannot_drink"),
    ("I am six months pregnant and I am bleeding", "pregnancy_bleeding"),
    ("He swallowed rat poison", "poison"),
    ("I have chest pain since last night", "chest_pain"),
    ("I want to die", "self_harm"),
])
def test_signs_in_english(text, key):
    assert key in keys(text, "en")


@pytest.mark.parametrize("text", [
    "I have a headache and a cough for two days",
    "No difficulty breathing. Not pregnant.",
    "She is breathing well and drinking well",
    "He denies chest pain",
    "No fits, no fainting, no blood in the stool",
    "I am not taking any medicine",
])
def test_no_false_alarm_in_english(text):
    assert triage.scan(text, "en") == []


def test_shona_text_is_also_checked_in_english():
    # Patients mix the two languages.
    assert "breathing" in keys("Mwana wangu ane difficulty breathing")


def test_second_opinion_only_counts_when_sure():
    assert triage.second_opinion_level({"0": 0.02, "1": 0.3, "2": 0.68}, 0.6) == "emergency"
    assert triage.second_opinion_level({"0": 0.2, "1": 0.5, "2": 0.3}, 0.6) == "urgent"
    assert triage.second_opinion_level({"0": 0.5, "1": 0.4, "2": 0.1}, 0.6) == "routine"
    assert triage.second_opinion_level({"x": "y"}, 0.6) == "routine"
    assert triage.second_opinion_level({"0": "bad"}, 0.6) is None


def test_combine_takes_the_highest_and_says_who_raised_it():
    C = triage.Check
    out = triage.combine([C("Rules", "emergency"), C("Note", "routine"), C("Second", None)])
    assert out["level"] == "emergency" and out["raised_by"] == ["Rules"] and not out["agreed"]
    out = triage.combine([C("Rules", "routine"), C("Note", "routine")])
    assert out["level"] == "routine" and out["agreed"] and out["raised_by"] == []
    # Nothing could assess the visit: it goes ahead of the queue.
    assert triage.combine([C("Rules", None)])["level"] == "urgent"


# Sentences an independent review found slipping past the first version of the rules.
@pytest.mark.parametrize("text,lang,key", [
    ("Mwana haamuke", "sn", "unconscious"),
    ("Mwana haasi kugona kufema", "sn", "breathing"),
    ("Handisi kugona kufema", "sn", "breathing"),
    ("Mwana haasi kugona kunwa", "sn", "cannot_drink"),
    ("Handina simba ndiri kutadza kufema", "sn", "breathing"),
    ("Mwana haasi kudya ari kugwinha", "sn", "convulsions"),
    ("Nyoka yakandiruma", "sn", "poison"),
    ("Ropa harisi kuda kumira", "sn", "bleeding"),
    ("He cannot be woken", "en", "unconscious"),
    ("We could not wake him", "en", "unconscious"),
    ("I couldn't wake my baby this morning", "en", "unconscious"),
    ("He has not stopped convulsing since this morning", "en", "convulsions"),
    ("She can't stop vomiting blood", "en", "bleeding"),
    ("He isn't breathing", "en", "breathing"),
    ("The bleeding will not stop", "en", "bleeding"),
])
def test_emergencies_found_by_review(text, lang, key):
    assert key in keys(text, lang)
    assert level(text, lang) == "emergency"


@pytest.mark.parametrize("text,lang", [
    ("Mutsipa hauna kuoma", "sn"),
    ("Chipfuva hachisi kurwadza", "sn"),
    ("He is not struggling to breathe", "en"),
    ("She has no fits and no fever", "en"),
])
def test_denials_inside_the_phrase(text, lang):
    assert triage.scan(text, lang) == []


@pytest.mark.parametrize("topic,answer,key", [
    ("breathing", "Hongu", "breathing"),
    ("breathing", "Hongu, zvakanyanya", "breathing"),
    ("breathing", "Yes", "breathing"),
    ("fits", "Ehe, kaviri nezuro", "convulsions"),
    ("drinking", "Kwete", "cannot_drink"),
    ("bleeding", "Hongu", "bleeding_yes"),
    ("neck", "Yes, it is", "stiff_neck"),
])
def test_a_bare_yes_or_no_to_a_danger_question_counts(topic, answer, key):
    assert triage.answer_sign(topic, answer).key == key


@pytest.mark.parametrize("topic,answer", [
    ("breathing", "Kwete"), ("breathing", "Hongu, ari kufema zvakanaka"), ("drinking", "Hongu, ari kunwa"),
    ("fits", "Kwete, hapana"), ("age", "Hongu"), ("onset", "Kwete"), (None, "Hongu"),
])
def test_other_answers_raise_nothing(topic, answer):
    assert triage.answer_sign(topic, answer) is None


# Lessons from the held-out set (eval/heldout.json), added after its one clean run.
@pytest.mark.parametrize("text,lang,key", [
    ("kubva nezuro ari kuramba zamu zvachose", "sn", "cannot_drink"),
    ("zvese zvaanodya kana kunwa ari kurutsa", "sn", "cannot_drink"),
    ("haachadaviri kana ndikamudaidza", "sn", "unconscious"),
    ("ropa riri kungoerera, jira rese ratonyorova", "sn", "bleeding"),
    ("ropa riri kungobuda zvakawandisa", "sn", "bleeding"),
    ("ari kukweva mweya nesimba mbabvu dzichipinda mukati", "sn", "breathing"),
    ("muviri wese uchidedera, furo richibuda mumuromo", "sn", "convulsions"),
    ("dai ndangozviuraya zvipere", "sn", "self_harm"),
    ("pfungwa dzinongoti zviri nani ndisisipo", "sn", "self_harm"),
    ("I'm about five months pregnant and I started spotting this morning", "en", "pregnancy_bleeding"),
    ("his nose has been bleeding since four and it's not stopping", "en", "bleeding"),
    ("now he's not answering us", "en", "unconscious"),
    ("I've been thinking of ending it all", "en", "self_harm"),
])
def test_emergencies_found_by_the_held_out_set(text, lang, key):
    assert key in keys(text, lang)


@pytest.mark.parametrize("text,lang", [
    ("Ndauya kuzotora mapiritsi epfari emwana, haasati ambogwinha zvakare", "sn"),
    ("I'm on the tablets for fits. I haven't had a fit in over two years", "en"),
    ("My son had a nosebleed yesterday but it stopped on its own", "en"),
    ("Hapana ropa, hapana kurwadziwa, mwana ari kutamba zvakanaka", "sn"),
])
def test_false_alarms_found_by_the_held_out_set(text, lang):
    assert triage.scan(text, lang) == []


# Patients mix Shona and English in one sentence. The second spelling in some
# pairs is how the recogniser wrote the borrowed word (measured 2026-11-26 on
# synthetic speech). Written by an AI assistant, not checked by a native speaker.
@pytest.mark.parametrize("text,key", [
    ("Mwana wangu ane fever, ari kutadza kubreather zvakanaka", "breathing"),
    ("Mwana wangu ane fivha uye ari kutadza kubhiridha zvakanaka", "breathing"),
    ("Ndine headache yakanyanya, uye neck yangu yakaoma", "stiff_neck_fever"),
    ("Ndine headack yakanyanya uye neki yangu yakaoma", "stiff_neck_fever"),
    ("Ndiri pregnant, ndiri kuona ropa kubva mangwanani", "pregnancy_bleeding"),
    ("Ndine pamuviri, ndiri kubleeda", "pregnancy_bleeding"),
    ("Mwana ari kuvhomita everything", "cannot_drink"),
    ("Mwana ane mafits kubva mangwanani", "convulsions"),
    ("Arumwa nesnake pagumbo", "poison"),
])
def test_emergency_signs_in_mixed_speech(text, key):
    assert key in keys(text)
    assert level(text) == "emergency"


@pytest.mark.parametrize("text,key", [
    ("Chest yangu iri kurwadza", "chest_pain"),
    ("Ndiri kunwa mapiritsi eBP neshuga asi nhasi ndine chest pain", "chest_pain"),
    ("Akafainta kubasa", "fainted"),
    ("Neck yangu yakaoma", "stiff_neck"),
])
def test_urgent_signs_in_mixed_speech(text, key):
    assert key in keys(text)


@pytest.mark.parametrize("text", [
    "Handisi pregnant, ndine headache chete",
    "Ndauya kuzotora matablets angu eHigh blood pressure handisi kurwara",
    "Mwana ane fever asi ari kubreather zvakanaka",
    "Neck yangu haina kuoma, ndine headache",
    "Hapana mafits",
])
def test_mixed_speech_that_is_not_a_danger_sign(text):
    assert level(text) == "routine"


# The wording the helper and the sample patients now use: everyday mixed Shona.
@pytest.mark.parametrize("text,key,expect", [
    ("Mwana ane problem yekufema", "breathing", "emergency"),
    ("Ndazvicheka, blood riri kubuda rakawanda uye harisi kumira", "bleeding", "emergency"),
    ("Blood harisi kustopper", "bleeding", "emergency"),
    ("Ndine headache, ndine temperature, uye neck yangu iri stiff", "stiff_neck_fever", "emergency"),
    ("Mwana ari kuvomita everything yaanodya", "cannot_drink", "emergency"),
    ("Ndiri pregnant, ndatanga kubleeder this morning", "pregnancy_bleeding", "emergency"),
    ("Neck yangu iri stiff", "stiff_neck", "urgent"),
    ("Mwana wangu ane three weeks ane temperature", "young_baby", "urgent"),
    ("Mwana ane diarrhoea ine blood kubva yesterday", "blood", "urgent"),
    ("Pane blood mustool", "blood", "urgent"),
    ("Yesterday ndakosora blood", "blood", "urgent"),
])
def test_signs_in_the_helpers_own_mixed_wording(text, key, expect):
    assert key in keys(text)
    assert level(text) == expect


# A Shona denial in front of an English sign is still a denial.
@pytest.mark.parametrize("text", [
    "Kwete, handina problem yekufema",
    "Kwete, neck haisi stiff",
    "Ndiri pregnant, five months. Kwete, hapana bleeding.",
    "Ndiri pregnant. Hapana blood randiri kuona.",
    "Handina chest pain",
    "Hapana blood mustool",
    "Mwana haasi kunwa maPills",
    "Mwana wangu ane six years ane rash kubva last week",
    "Blood remaPeriods chete, harina kuwanda",
])
def test_mixed_denials_are_not_danger_signs(text):
    assert level(text) == "routine"


def test_an_english_sign_after_a_shona_denial_of_something_else_still_counts():
    assert "chest_pain" in keys("Handina simba, ndine chest pain")


@pytest.mark.parametrize("text", [
    "she cannot drink",
    "she can't drink",
    "she can not drink",
    "he won't drink anything",
    "the baby cannot breastfeed",
    "she is unable to drink",
    "she is too weak to suck",
    "My daughter has had diarrhoea since yesterday and now she cannot drink anything",   # ticket 9, word for word
])
def test_a_child_who_cannot_drink_is_an_emergency_in_plain_english(text):
    """The rules must catch this with every model down. They missed "cannot drink" with no "to"."""
    assert "cannot_drink" in keys(text, "en") and level(text, "en") == "emergency"
