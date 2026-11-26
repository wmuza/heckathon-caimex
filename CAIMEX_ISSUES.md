# CAIMEx issues log

Rule 6 of the hackathon: log every technical issue so CAIMEx can be improved. Everything below was
hit while building Mukoti on 2026-11-25, against `https://api.caimex.ai/v1`, from a Mac on the
venue network. Times are wall-clock for one request. Add new entries at the bottom.

| # | Area | What happened | How we worked round it |
|---|---|---|---|
| 1 | Network | Opening a new connection took 8 to 15 s (TCP connect 2 to 4 s, TLS 6 to 8 s), so every one-off `curl` looked very slow. On a reused connection the same calls took 1 to 2 s. `notebooks.futurezim.com` showed the same TLS delay. May be the venue network, not the gateway. | One long-lived HTTP client, three connections kept warm with a request every 20 s. |
| 2 | Chat, `deepseek-v4-flash` | `reasoning_effort: "none"` does not stop reasoning. Each short answer still used 240 to 450 reasoning tokens and took 4 to 8 s. `"minimal"`, `reasoning: {"enabled": false}`, `reasoning: {"effort": "none"}` and `thinking: {"type": "disabled"}` made no difference either. | `enable_thinking: false` (sent with `chat_template_kwargs: {"enable_thinking": false}`) works: 1.3 s, no reasoning tokens. Not in the docs. |
| 3 | Chat, `deepseek-v4-flash` | With `max_tokens: 300`, hidden reasoning used the whole budget: `finish_reason: "length"` and empty or cut-off `content`. With reasoning set to "none" the caller cannot see why. | Higher `max_tokens`, and item 2. |
| 4 | Chat, `glm-5.3-flash` | Same as 3: empty `content`, 300 of 300 tokens used, with or without `reasoning_effort: "none"`. It answered at `max_tokens: 1500` (565 tokens for a 30-token answer). | Not relied on for live turns. |
| 5 | Chat, `hy4-fp8` | Used all 1200 tokens in 11 s and returned empty `content`. | Not used. |
| 6 | Speech to text, `stt` | A 12-second MP3 failed after 92 s with `{"detail": "The provider could not complete this request. Please try again in a moment."}`. | Used `languages-lab-stt-large-1.3`. |
| 7 | Speech to text, `auto-stt` | No answer within 60 s on the same clip. | As 6. |
| 8 | Speech to text, `gpt-4o-transcribe`, `gpt-4o-mini-transcribe` | HTTP 502 after 33 to 37 s with the same generic "provider could not complete" text. Chat calls to OpenAI models in the same workspace failed at once with a clear message ("disabled by an admin"), so the audio path seems to hide the real reason and wait a long time before saying so. | Not used. |
| 9 | Catalogue | `voxtral-small-transcribe-3` is listed under `kind=stt`, but the API answers "is not a transcription model; use voxtral-mini-latest". | Not used. |
| 10 | Catalogue | `GET /v1/models` lists models this workspace cannot call (`gemini-3.8-flash`, `gpt-5.6-luna`: "disabled by an admin"; `gemini-3.8-flash-lite`: "not in this workspace's model access tier") with `locked: null`, so a client cannot tell in advance what it may use. | Tried each model by hand. |
| 11 | Catalogue | The self-hosted speech and chat models have an empty `description` and no list of languages. Nothing says which recogniser or voice supports Shona; we found out by trying. | Trial and error. |
| 12 | Live transcription socket | `/v1/audio/transcriptions/live` (`window_seconds=3`): we streamed a 12-second clip, then sent `{"type": "end"}`. Only the first window came back ("Mangwanani chiremba. Ndine musoro uri kurwa.") and the socket then dropped with no close frame. The docs say `end` flushes first. Tested once. | Used the REST endpoint. |
| 13 | Live speech socket | `/v1/audio/speech/live`: after two `audio` frames the socket dropped with no close frame, and no `segment_done` or `session_ended` arrived. Tested once, on a cold connection. | Used the REST endpoint. |
| 14 | Text to speech, `languages-lab-tts-large-1.3` | Time for one short sentence varied from 1.5 s to 5.7 s on a warm connection. | Fixed lines are synthesised once and cached on disk. |
| 15 | Billing, speech to text | A WebM/Opus clip (what Chrome's recorder produces) is billed about three times its real length. The same 12.3-second sentence cost $0.15 as WebM and $0.03 to $0.05 as MP3, WAV or Ogg, read from `GET /v1/key` before and after one call each. At the list price of $0.2247 a minute, 12.3 s should be $0.046. A browser recording has no duration in its header, so the length seems to be guessed from the file size. | The browser now records 16 kHz WAV itself (`web/rec.js`). |
| 16 | Billing, speech calls | `/v1/audio/transcriptions` and `/v1/audio/speech` return no `x-caimex-cost-usd` header and no `usage` in the body, although chat and decisions do. An app cannot tell what a speech call cost; the docs point to `GET /v1/generation/{id}`, but speech calls return no id either. | Cost worked out from the catalogue price and the clip length, and labelled as such. |
| 17 | Catalogue, pricing | The self-hosted recogniser is listed at $0.2247 a minute ($13.48 an hour). In Mukoti it is 98% of the cost of a visit (about 4 US cents on our test patients); the chat, voice and decision calls together are about a tenth of a cent. Worth a look if local speech apps are meant to be affordable. | Trailing silence is trimmed before upload, which saves about a second a turn. |
| 18 | Speech to text, Ndebele | `languages-lab-stt-large-1.3` with `language=nd` returned garbled text for a clear synthetic Ndebele sentence, in all five voices ("Ngilekhanda elibuhlungu" came back as "ngile kanda elibulungu"). Nothing in the catalogue says which languages it supports. | Mukoti offers Shona and English only. |
| 19 | Translation, `madlad400-3b-mt` | Shona to English changed the meaning of a medical sentence: "Mwana wangu ane mwedzi misere ari kutadza kufema" (my eight-month-old cannot breathe) became "My six-month-old son is trying to breathe". | Not used. The chat model translates. |
| 20 | Decisions, `d3-nano` | Fast (0.15 s) and gives real probabilities, but it reads Shona poorly: "pregnant and bleeding" in Shona scored routine. On the same facts in English it scored emergency. | It is only ever given the English note, and it can raise a visit to urgent but never sound the alarm alone. |
| 21 | Text to speech | With `stream` unset, the first byte arrives at the same moment as the last (1.75 s of 1.78 s), so nothing is gained by streaming this model. | Every fixed line is synthesised once at start-up. |
| 22 | Chat under load, `deepseek-v4-flash` with reasoning | When sixty note-writing calls (reasoning on, up to 4,000 tokens) were sent at once, every one failed with `504 Gateway Time-out` (an HTML page, not JSON). Sent three at a time a few minutes later, 14 of 60 still failed: `504`, `502 "The model is temporarily unavailable"`, or no answer in 90 s. The same call alone answers in 3 to 9 s. | The note is tried with reasoning for 40 s, then once without (about 2.5 s). If both fail the visit is shown as urgent, never routine. |
| 23 | Chat, `deepseek-v4-flash` without reasoning | Asked to put "the patient's last message" into English, it sometimes translated an earlier message instead (the age answer came back as the opening complaint). | The last message is repeated at the end of the system prompt. |
| 24 | Errors | A gateway timeout returns an HTML error page with status 504, while other errors are JSON. A client that parses every error body as JSON breaks. | Error bodies are read as text. |

## What worked well

- `languages-lab-stt-large-1.3` transcribed a 12-second Shona clip word for word in 1.2 to 2 s, and
  accepts the browser's WebM/Opus recording directly.
- `languages-lab-tts-large-1.3` speaks natural Shona; `GET /v1/audio/voices` lists its voices.
- `response_format: {"type": "json_object"}` returned clean JSON every time on `deepseek-v4-flash`.
- The `x-caimex-cost-usd` header on chat calls made cost easy to track: a question costs about $0.0003.
- `/v1/decisions` with `d3-nano` answers in about 0.15 s with a probability for every option.
- `GET /v1/models` reports `hosting_country`, so the app can show that every model it uses runs in Zimbabwe.
- `GET /v1/key` reports the key's running spend, which is how issue 15 was found.
