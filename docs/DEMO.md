# The demo, step by step

About three minutes. One laptop on the projector, showing one page: http://127.0.0.1:8000/demo
(the patient on the left, the nurse on the right). Speak to the room, not to the screen.

## Fifteen minutes before

1. In a terminal: `./run.sh`. Leave it open. Wait two minutes: it is saying every fixed sentence
   once and saving it.
2. Open http://127.0.0.1:8000/demo in Chrome. Choose **Large** or **Largest** at the top, whichever
   the back row can read.
3. On the right, press **Clear the queue**, then **Load the sample patients**. Six patients appear
   within a minute, most urgent first. Do this late, so their waiting times are short.
4. Run one sample patient right through, on the left, to check the sound: **Ona murwere
   wemuenzaniso**, then the first one. Then **Murwere anotevera**.
5. Click once anywhere on the right-hand side. The alarm sound only works after a click.
6. Turn the laptop's volume up. Close other tabs.

If the room has no reliable internet, say so before you start. Mukoti needs CAIMEx for every
sentence.

## The three minutes

**1. The problem (20 seconds, nothing on screen moves).**

> "A clinic. One nurse, a full bench. She sees people in the order they arrived, not the order
> they need. WHO's own guide says someone at reception should check every person as they arrive.
> In a clinic with two nurses, nobody is free to. So we built that person."

**2. The emergency (40 seconds).** Left side: **Ona murwere wemuenzaniso**, then *A mother whose
baby cannot breathe*.

Say while it plays: "This is a made-up patient with a synthetic voice. Everything else is real:
the recogniser is hearing her, in Shona, now."

The helper greets her, she says one sentence, and the right-hand side chimes: the baby is in the
queue as an emergency, and a notice at the bottom says so. Press **Open** on the notice.

> "One sentence. No model was even asked. Fixed rules, written from WHO's danger signs, read her
> words and called the nurse."

Point at the ticket on the left: calm, a number, "the nurse is coming". Point at the right: the
red mark, the picture of what is wrong, her words in Shona and English, and the play button beside
them that plays her own voice.

**3. The quiet danger (50 seconds).** Left: **Murwere anotevera**, then *A child with diarrhoea who
has stopped drinking*.

> "This one sounds ordinary. Diarrhoea since yesterday."

Let the questions run. Point at the picture as each question is asked: "She hears it, and she
sees it. She does not have to read." On the third answer the alarm goes.

> "It asked the right question. The mother said the child can no longer drink, and that is a WHO
> danger sign. Every sentence you heard the helper say was written in advance. The AI only chooses
> which one to ask. It cannot diagnose, and it cannot give advice, because it has no words for it."

**4. The ordinary visit (20 seconds).** Click *A woman collecting her blood pressure tablets* on the
right (it is already in the queue).

> "And most people are this. Three questions, a routine note, back of the queue. The nurse reads
> four lines instead of asking six questions."

**5. How CAIMEx is used (40 seconds).** Top right: **Engine**.

> "Four CAIMEx models, four services, all listed as hosted in Zimbabwe: hear, choose, speak, write
> the note, and a second opinion. The dashed boxes are our own code with no AI in them."

Press **Play again** at the top: the dot travels through the five steps one sentence takes.

Scroll to the last visit's table: "Every call, how long it took, what it cost. About four cents
a visit, nearly all of it speech recognition."

Scroll to "What broke": "And rule six. Twenty-four issues logged for the CAIMEx team. One of them:
a browser recording is billed at three times its length."

**6. The close (20 seconds).**

> "It is not validated and we say so on every screen. We tried it on sixty patient statements it
> had never seen: every emergency was caught. The rules alone caught eleven of twenty-four, which
> is why there are four checks and a nurse in charge. Mukoti: the first person every patient talks
> to, in their own language."

## If something goes wrong

| What happens | What to do |
|---|---|
| A sample patient stops with "Pane chakanganisika" | Press **Edza zvakare** (Try again). The gateway dropped one call. |
| No sound | Click the page once, check the volume, start the patient again. |
| The note says "could not be written" | Say it: "The model that writes the note timed out, so Mukoti put this patient ahead of the queue instead of guessing. That is the design." |
| Everything is slow | The first calls after a start are slow. Run one patient before the judges arrive. |
| The gateway is down | Open the queue you loaded earlier and walk through a finished visit. Do not pretend it is live. |
| A judge wants to speak to it | Left side, **Startai kutaura**. It listens by itself and stops when they stop. In a loud room, tap the red button to end their turn. They can choose English. |

## If a judge speaks to it themselves

It will be the best moment of the demo or the worst. Before they start, say: "It has only been
tested on a few real voices, so let us see." If it mishears, show the nurse's side: the recording
is there, and the note has a line "may have been misheard". That is the answer to the mistake.

## Things not to say

- "It triages patients." The nurse triages. Mukoti does a quick check and orders the queue.
- "It is accurate" or any percentage without "on made-up patients".
- "It is safe." Say what it does when it is unsure: it raises the level and hands over.
- Anything about real patients having used it. None has.
