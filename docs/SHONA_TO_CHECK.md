# Shona to check

Every Shona sentence in Mukoti, with the English it is meant to say. All of it was written by an AI
assistant. A native speaker should read each line aloud and mark anything wrong, stiff or unclear.
Made by `tools/shona_sheet.py`; edit the sentences in the files named, then run it again.

## What the helper says: fixed lines

In `app/prompts.py`.

| Shona | Meant to say | OK? |
|---|---|---|
| Mhoroi, mauya kukiriniki. Ndiri mubatsiri wemukoti, handisi chiremba. Ndichakubvunzai mibvunzo mishoma kuti mukoti akurumidze kukubatsirai. Chii chakuunzai nhasi? | Hello, welcome to the clinic. I am the nurse's helper, not a doctor. I will ask you a few short questions so the nurse can help you sooner. What brings you here today? |  |
| Ndapota dzokororai, handina kunzwa zvakanaka. | Please say that again, I did not hear you well. |  |
| Ndatenda. Ndapa mukoti zvamandiudza. Ndapota garai muchimirira, mukoti achakudaidzai. | Thank you. I have passed this to the nurse. Please take a seat, the nurse will call you. |  |
| Ndatenda. Ndiri kudaidza mukoti iye zvino. Ndapota garai pano, mukoti ari kuuya. | Thank you. I am calling the nurse now. Please stay here, the nurse is coming. |  |

## What the helper says: the questions

In `app/prompts.py`.

| Shona | Meant to say | OK? |
|---|---|---|
| Ndiani ari kurwara, imi here kana mwana? | Who is unwell, you or a child? |  |
| Mune makore mangani? | How old are you? |  |
| Mwana ane makore mangani? | How old is the child? |  |
| Zvakatanga rini? | When did it start? |  |
| Zviri kuwedzera here? | Is it getting worse? |  |
| Kurwadza kuri papi? | Where is the pain? |  |
| Kurwadza kwacho kwakanyanya here? | Is the pain very bad? |  |
| Muri kupisa muviri here? | Do you have a fever? |  |
| Mwana ari kupisa muviri here? | Does the child have a fever? |  |
| Muri kunetseka kufema here? | Are you struggling to breathe? |  |
| Mwana ari kunetseka kufema here? | Is the child struggling to breathe? |  |
| Mwana ari kugona kunwa kana kuyamwa here? | Is the child able to drink or breastfeed? |  |
| Muri kurutsa here? | Are you vomiting? |  |
| Mwana ari kurutsa here? | Is the child vomiting? |  |
| Pane pfari here? | Have there been any fits? |  |
| Pane ropa ramuri kuona here? | Have you seen any blood? |  |
| Mutsipa wenyu wakaoma here? | Is your neck stiff? |  |
| Mune pamuviri here? | Are you pregnant? |  |
| Mune chirwere chenguva refu here, seshuga kana BP? | Do you have a long-term illness, such as diabetes or high blood pressure? |  |
| Mwana ane chirwere chenguva refu here? | Does the child have a long-term illness? |  |
| Pane mishonga yamuri kunwa mazuva ano here? | Are you taking any medicines these days? |  |
| Pane mishonga iri kunwiwa nemwana mazuva ano here? | Is the child taking any medicines these days? |  |
| Pane mushonga usingawirirani nemi here? | Is there any medicine that does not agree with you? |  |
| Pane chimwe chiri kukunetsai here? | Is anything else troubling you? |  |

## Calling a ticket in the waiting room (the number is put in)

In `app/prompts.py`.

| Shona | Meant to say | OK? |
|---|---|---|
| Nhamba gumi nemana, ndapota endai kuna mukoti. | Ticket 14, please go to the nurse. |  |
| Nhamba gumi nemana, ndapota endai kuna chiremba. | Ticket 14, please go to the doctor. |  |
| Nhamba gumi nemana, ndapota endai kunotora mishonga. | Ticket 14, please go to the pharmacy. |  |

## How to take a medicine, said at the pharmacy

In `app/prompts.py`.

| Shona | Meant to say | OK? |
|---|---|---|
| Shandisai mushonga uyu kamwe chete pazuva. | Use this medicine once a day. |  |
| Shandisai mushonga uyu kaviri pazuva. | Use this medicine twice a day. |  |
| Shandisai mushonga uyu katatu pazuva. | Use this medicine three times a day. |  |
| Shandisai mushonga uyu kana zvichidikanwa chete. | Use this medicine only when you need it. |  |
| Shandisai mushonga uyu sezvamaudzwa nemupi wemishonga. | Use this medicine as the pharmacist has told you. |  |

## A warning for a community, when the national picture shows a risk

In `app/prompts.py`.

| Shona | Meant to say | OK? |
|---|---|---|
| Yambiro: chirwere chemanyoka chiri kuwanda munharaunda. Birisai mvura yokunwa, mugeze maoko nesipo. | Warning: diarrhoea is spreading in this area. Boil your drinking water and wash your hands with soap. |  |
| Yambiro: marariya iri kuwanda munharaunda. Rarai pasi pemambure, uyai kukiriniki kana muchipisa muviri. | Warning: malaria is rising in this area. Sleep under a net, and come to the clinic if you have a fever. |  |
| Yambiro: zvirwere zvechipfuva zviri kuwanda. Uyai kukiriniki kana mwana achinetseka kufema. | Warning: chest infections are rising. Come to the clinic if a child is struggling to breathe. |  |

## Ticket numbers in words

In `app/voice.py`.

| Shona | Meant to say | OK? |
|---|---|---|
| poshi | 1 |  |
| piri | 2 |  |
| tatu | 3 |  |
| ina | 4 |  |
| shanu | 5 |  |
| tanhatu | 6 |  |
| nomwe | 7 |  |
| sere | 8 |  |
| pfumbamwe | 9 |  |
| gumi | 10 |  |
| gumi nerimwe | 11 |  |
| gumi nemaviri | 12 |  |
| gumi nemashanu | 15 |  |
| makumi maviri | 20 |  |
| makumi maviri nerimwe | 21 |  |
| makumi matatu | 30 |  |
| makumi mana nemashanu | 45 |  |
| makumi mapfumbamwe nemapfumbamwe | 99 |  |
| zana | 100 |  |
| zana nerimwe | 101 |  |
| zana negumi | 110 |  |
| zana nemakumi maviri nemashanu | 125 |  |

## The patient's screen

In `web/index.html`.

| Shona | Meant to say | OK? |
|---|---|---|
| Mubatsiri wemukoti. Taurai, mukurumidze kubatsirwa | The nurse's helper. Speak, and be helped sooner |  |
| Mauya kukiriniki | Welcome to the clinic |  |
| Ndichakubvunzai mibvunzo mishoma. Mhinduro dzenyu dzinopiwa mukoti kuti akubatsirei nekukurumidza. | I will ask you a few short questions. Your answers go to the nurse, so she can help you sooner. |  |
| Izwi renyu rinorekodhwa kuti mukoti azorinzwa, rozodzimwa mushure mezuva rimwe chete. | Your voice is recorded so the nurse can listen to it. It is deleted after one day. |  |
| Ndinobvuma, tanga kutaura | I agree, start talking |  |
| Ona murwere wemuenzaniso | Watch a sample patient |  |
| Mubatsiri uyu ikombiyuta, haasi chiremba. Kana zvakaoma, udzai mukoti iye zvino. | This helper is a computer, not a doctor. If it is serious, tell the nurse now. |  |
| Muenzaniso, izwi rekombiyuta | Sample, synthetic voice |  |
| Zvimwe | More options |  |
| Mubatsiri | Helper |  |
| Nhamba yenyu | Your number |  |
| Murwere anotevera | Next patient |  |
| Tumira | Send |  |
| Maikorofoni inozvivhura nekuzvivhara yoga | The microphone opens and closes by itself |  |
| Nyora panzvimbo pekutaura | Type instead of speaking |  |
| Ratidza Chirungu pasi pemashoko | Show English under the words |  |
| Ndapedza | I have finished |  |
| Chiedza | Light |  |
| Rima | Dark |  |
| Sefoni | Match phone |  |
| Vashandi | Staff |  |
| Varwere vemuenzaniso | Sample patients |  |
| Vhara | Close |  |
| Vanhu ava havasi chaivo uye mazwi avo nderekombiyuta. Mubatsiri anovanzwa nekuvapindura chaizvo. | These people are made up and their voices are synthetic. The helper really hears them and really answers. |  |
| Dzvanyai maikorofoni mutaure | Tap the microphone to speak |  |
| Taurai iye zvino, ndiri kuteerera | Speak now, I am listening |  |
| Ndiri kunyora zvamataura… | Writing down what you said… |  |
| Ndiri kufunga… | Thinking… |  |
| Mubatsiri ari kutaura, teererai | The helper is speaking, listen |  |
| Nyorai mhinduro yenyu | Type your answer |  |
| Maikorofoni haisi kushanda. Nyorai mhinduro yenyu. | The microphone is not working. Type your answer. |  |
| Pane chakanganisika. Edzai zvakare. | Something went wrong. Please try again. |  |
| Imi | You |  |
| Murwere wemuenzaniso | Sample patient |  |
| Murwere ari kutaura… | The patient is speaking… |  |
| Nyorai pano | Type here |  |
| Zvapera | Finished |  |
| Mukoti ari kuuya | The nurse is coming |  |
| Edza zvakare | Try again |  |
| Ndatenda. Garai muchimirira, mukoti achakudaidzai. | Thank you. Please take a seat, the nurse will call you. |  |
| Ndatenda. Mukoti adaidzwa iye zvino. Ndapota garai pano. | Thank you. The nurse has been called. Please stay here. |  |

## Sample patients: answers every Shona patient shares

In `samples/patients.json`.

| Shona | Meant to say | OK? |
|---|---|---|
| Ndini ndiri kurwara. | It is me. |  |
| Ndine makore makumi matatu. | I am thirty years old. |  |
| Zvakatanga nezuro. | It started yesterday. |  |
| Kwete, zvakangofanana. | No, it is about the same. |  |
| Zviri pakati nepakati. | It is not too bad. |  |
| Kwete, ndiri kufema zvakanaka. | No, I am breathing well. |  |
| Hongu, ari kunwa zvakanaka. | Yes, drinking well. |  |
| Kwete, hapana ropa. | No, there is no blood. |  |
| Kwete, handina pamuviri. | No, I am not pregnant. |  |
| Kwete, handina chirwere chenguva refu. | No, I have no long-term illness. |  |
| Kwete, handisi kunwa mishonga. | No, I am not taking any medicines. |  |
| Kwete, hapana. | No, none. |  |
| Kwete. | No. |  |
| Ndiri kurwara. | I am not feeling well. |  |
| Ipapo pandakuudzai. | Where I told you. |  |
| Kwete, handisi kupisa muviri. | No, I do not have a fever. |  |
| Kwete, handisi kurutsa. | No, I am not vomiting. |  |
| Kwete, hapana pfari. | No, no fits. |  |
| Kwete, mutsipa hauna kuoma. | No, my neck is not stiff. |  |

## Sample patients: their own lines

In `samples/patients.json`.

| Shona | Meant to say | OK? |
|---|---|---|
| Mwana wangu ane mwedzi misere ari kutadza kufema, uye ari kupisa muviri. | (A mother whose baby cannot breathe) opening line |  |
| Mwana wangu. | answer about: who |  |
| Ane mwedzi misere. | answer about: age |  |
| Kubva husiku hwapfuura. | answer about: onset |  |
| Hongu, zviri kuwedzera. | answer about: worse |  |
| Hongu, ari kutadza kufema. | answer about: breathing |  |
| Hongu, ari kupisa muviri. | answer about: fever |  |
| Kwete, hapana pfari. | answer about: fits |  |
| Kwete, haasi kurutsa. | answer about: vomiting |  |
| Mwana wangu ane manyoka kubva nezuro. | (A child with diarrhoea who has stopped drinking) opening line |  |
| Mwana wangu. | answer about: who |  |
| Ane gore rimwe chete. | answer about: age |  |
| Kubva nezuro manheru. | answer about: onset |  |
| Hongu, zviri kuwedzera, ava kuneta. | answer about: worse |  |
| Hongu, zvakanyanya. | answer about: severity |  |
| Kwete, ari kufema zvakanaka. | answer about: breathing |  |
| Kwete, haachagoni kunwa kana kuyamwa, uye anorutsa zvese zvaanodya. | answer about: drinking |  |
| Kwete, hapana ropa mumanyoka. | answer about: bleeding |  |
| Haachagoni kunwa kana kuyamwa. | answer about: other |  |
| Kwete, haasi kupisa muviri. | answer about: fever |  |
| Hongu, anorutsa zvese zvaanodya. | answer about: vomiting |  |
| Kwete, hapana pfari. | answer about: fits |  |
| Ndine pamuviri pemwedzi minomwe, ndatanga kubuda ropa mangwanani ano. | (A pregnant woman who is bleeding) opening line |  |
| Ndine makore makumi maviri nematanhatu. | answer about: age |  |
| Mangwanani ano. | answer about: onset |  |
| Hongu, riri kuwedzera. | answer about: worse |  |
| Hongu, ropa riri kubuda. | answer about: bleeding |  |
| Hongu, ndine pamuviri pemwedzi minomwe. | answer about: pregnancy |  |
| Mwana wangu ane makore matatu abatwa nepfari kaviri husiku hwapfuura. | (A child who had fits in the night) opening line |  |
| Mwana wangu. | answer about: who |  |
| Ane makore matatu. | answer about: age |  |
| Husiku hwapfuura. | answer about: onset |  |
| Hongu. | answer about: worse |  |
| Hongu, kaviri husiku hwapfuura. | answer about: fits |  |
| Hongu, ari kupisa muviri. | answer about: fever |  |
| Murume wangu arumwa nenyoka pagumbo tiri kumunda. | (A man bitten by a snake) opening line |  |
| Murume wangu. | answer about: who |  |
| Ane makore makumi mana. | answer about: age |  |
| Awa imwe chete yapfuura. | answer about: onset |  |
| Mbuya vangu vafenda kumba, vazomuka asi vava kutaura zvisinganzwisisike. | (A grandmother who fainted) opening line |  |
| Mbuya vangu. | answer about: who |  |
| Vane makore makumi manomwe. | answer about: age |  |
| Mangwanani ano. | answer about: onset |  |
| Hongu, vane shuga. | answer about: chronic |  |
| Ndave nemavhiki ndisingarari, uye ndava kufunga kuzviuraya. | (A man with thoughts of ending his life) opening line |  |
| Ndine makore makumi matatu nemashanu. | answer about: age |  |
| Mavhiki matatu apfuura. | answer about: onset |  |
| Hongu. | answer about: worse |  |
| Ndazvicheka nebanga paruoko, ropa riri kubuda rakawanda uye harisi kumira. | (A deep cut that will not stop bleeding) opening line |  |
| Ndine makore makumi maviri nemapfumbamwe. | answer about: age |  |
| Maminitsi makumi maviri apfuura. | answer about: onset |  |
| Hongu, ropa rakawanda. | answer about: bleeding |  |
| Mwana wangu ane mavhiki matatu ari kupisa muviri uye haasi kuyamwa. | (A three-week-old baby with fever) opening line |  |
| Mwana wangu. | answer about: who |  |
| Ane mavhiki matatu. | answer about: age |  |
| Kubva nezuro. | answer about: onset |  |
| Kwete, haasi kuyamwa. | answer about: drinking |  |
| Hongu. | answer about: worse |  |
| Hongu, ari kupisa muviri. | answer about: fever |  |
| Ndine musoro unorwadza zvakanyanya, ndiri kupisa muviri, uye mutsipa wangu wakaoma. | (A man with a bad headache, fever and a stiff neck) opening line |  |
| Ndine makore makumi maviri nemana. | answer about: age |  |
| Kubva nezuro husiku. | answer about: onset |  |
| Hongu, zviri kuwedzera. | answer about: worse |  |
| Hongu, zvakanyanya. | answer about: severity |  |
| Hongu, ndiri kupisa muviri. | answer about: fever |  |
| Hongu, mutsipa wakaoma. | answer about: neck |  |
| Musoro nemutsipa. | answer about: where |  |
| Kwete. | answer about: vomiting |  |
| Mwana ane makore mana ane manyoka ane ropa kubva nezuro. | (A child with blood in the stool) opening line |  |
| Mwana wangu. | answer about: who |  |
| Ane makore mana. | answer about: age |  |
| Kubva nezuro. | answer about: onset |  |
| Zvakangofanana. | answer about: worse |  |
| Hongu, pane ropa mumanyoka. | answer about: bleeding |  |
| Hongu, ari kunwa. | answer about: drinking |  |
| Kwete. | answer about: fever |  |
| Kwete, haasi kurutsa. | answer about: vomiting |  |
| Ndine pamuviri pemwedzi mishanu, ndiri kupisa muviri zvakanyanya uye ndiri kutonhorwa. | (A pregnant woman with a high fever) opening line |  |
| Ndine makore makumi maviri nemaviri. | answer about: age |  |
| Mazuva maviri apfuura. | answer about: onset |  |
| Hongu. | answer about: worse |  |
| Hongu, pemwedzi mishanu. | answer about: pregnancy |  |
| Kwete, hapana ropa. | answer about: bleeding |  |
| Hongu, zvakanyanya. | answer about: fever |  |
| Mwana wangu atsva nemvura inopisa paruoko nepadumbu. | (A child scalded with hot water) opening line |  |
| Mwana wangu. | answer about: who |  |
| Ane makore maviri. | answer about: age |  |
| Awa imwe chete yapfuura. | answer about: onset |  |
| Hongu, ari kuchema zvakanyanya. | answer about: severity |  |
| Paruoko nepadumbu. | answer about: where |  |
| Ndine dumbu riri kurwadza zvakanyanya kubva husiku, handisi kugona kumira ndakatwasuka. | (Severe abdominal pain since the night) opening line |  |
| Ndine makore makumi matatu nerimwe. | answer about: age |  |
| Kubva husiku hwapfuura. | answer about: onset |  |
| Hongu, zviri kuwedzera. | answer about: worse |  |
| Hongu, zvakanyanya. | answer about: severity |  |
| Mudumbu, kurudyi. | answer about: where |  |
| Kwete. | answer about: vomiting |  |
| Kwete. | answer about: fever |  |
| Ndave nemavhiki matatu ndichikosora, uye nezuro ndakosora ropa. | (Three weeks of cough, now with blood) opening line |  |
| Ndine makore makumi mana nemashanu. | answer about: age |  |
| Mavhiki matatu apfuura. | answer about: onset |  |
| Hongu. | answer about: worse |  |
| Hongu, ndakosora ropa nezuro. | answer about: bleeding |  |
| Ndine musoro uri kurwadza uye ndiri kukosora. | (A woman with a headache and a cough) opening line |  |
| Ndine makore makumi matatu nemaviri. | answer about: age |  |
| Mazuva maviri apfuura. | answer about: onset |  |
| Kwete, zvakangofanana. | answer about: worse |  |
| Musoro. | answer about: where |  |
| Zvishoma chete. | answer about: fever |  |
| Ndauya kuzotora mapiritsi angu eBP, apera. | (A woman collecting her blood pressure tablets) opening line |  |
| Ndine makore makumi matanhatu nemana. | answer about: age |  |
| Mapiritsi apera nezuro. | answer about: onset |  |
| Hongu, ndine BP. | answer about: chronic |  |
| Hongu, mapiritsi eBP. | answer about: medicines |  |
| Kwete, hapana chiri kurwadza. | answer about: severity |  |
| Mwana wangu ane makore matanhatu ane mapundu anovava pamaoko kwevhiki. | (A child with an itchy rash) opening line |  |
| Mwana wangu. | answer about: who |  |
| Ane makore matanhatu. | answer about: age |  |
| Vhiki rapfuura. | answer about: onset |  |
| Kwete, ari kufema zvakanaka. | answer about: breathing |  |
| Hongu, ari kudya nekunwa zvakanaka. | answer about: drinking |  |
| Kwete, haasi kupisa muviri. | answer about: fever |  |
| Pamaoko. | answer about: where |  |
| Ndine musana uri kurwadza kubva pandakasimudza saga svondo rapfuura. | (Backache after lifting a sack) opening line |  |
| Ndine makore makumi mana nemaviri. | answer about: age |  |
| Svondo rapfuura. | answer about: onset |  |
| Musana, nechezasi. | answer about: where |  |
| Ndauya kuzobaiwa jekiseni rekuronga mhuri. | (A family planning injection) opening line |  |
| Ndine makore makumi maviri nemasere. | answer about: age |  |
| Hapana chiri kurwadza. | answer about: onset |  |
| Kwete, hapana chiri kurwadza. | answer about: severity |  |
| Ndine zino riri kurwadza kwemazuva maviri. | (A toothache) opening line |  |
| Ndine makore makumi matatu nemana. | answer about: age |  |
| Mazuva maviri apfuura. | answer about: onset |  |
| Zino rekuseri. | answer about: where |  |
| Ndauya nemwana kuzobaiwa majekiseni ake emwedzi mipfumbamwe. | (A baby due for immunisation) opening line |  |
| Mwana wangu, asi haasi kurwara. | answer about: who |  |
| Ane mwedzi mipfumbamwe. | answer about: age |  |
| Haasi kurwara, majekiseni chete. | answer about: onset |  |
| Kwete, ari kufema zvakanaka. | answer about: breathing |  |
| Hongu, ari kuyamwa zvakanaka. | answer about: drinking |  |
| Kwete, haasi kupisa muviri. | answer about: fever |  |
| Kwete, haasi kurutsa. | answer about: vomiting |  |
| Ndine dzihwa nechipfuva kwemazuva matatu. | (A cold, with every danger sign denied) opening line |  |
| Ndine makore makumi maviri nerimwe. | answer about: age |  |
| Mazuva matatu apfuura. | answer about: onset |  |
| Kwete, handisi kunetseka kufema. | answer about: breathing |  |
| Kwete, hapana ropa randiri kuona. | answer about: bleeding |  |
| Kwete, handina pamuviri. | answer about: pregnancy |  |
| Kwete, handisi kupisa muviri. | answer about: fever |  |
| Kwete, mutsipa hauna kuoma. | answer about: neck |  |
| Ndine dumbu rinorwadza pandinenge ndiri kumwedzi. | (Period pain) opening line |  |
| Ndine makore gumi nemanomwe. | answer about: age |  |
| Mwedzi woga woga. | answer about: onset |  |
| Ropa rekumwedzi chete, harina kuwanda. | answer about: bleeding |  |
| Zviri pakati nepakati. | answer about: severity |  |
| Dumbu rezasi. | answer about: where |  |

