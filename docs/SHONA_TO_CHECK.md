# Shona to check

Every Shona sentence in Mukoti, with the English it is meant to say. All of it was written by an AI
assistant. A native speaker should read each line aloud and mark anything wrong, stiff or unclear.
Made by `tools/shona_sheet.py`; edit the sentences in the files named, then run it again.

## What the helper says: fixed lines

In `app/prompts.py`.

| Shona | Meant to say | OK? |
|---|---|---|
| Mhoroi, welcome kuClinic. Ndiri helper yaNurse, handisi doctor. Ndichakubvunzai maQuestions mashoma kuti nurse akurumidze kukubatsirai. Chii chakuunzai nhasi? | Hello, welcome to the clinic. I am the nurse's helper, not a doctor. I will ask you a few short questions so the nurse can help you sooner. What brings you here today? |  |
| Sorry, handina kunzwa zvakanaka. Please dzokororai. | Please say that again, I did not hear you well. |  |
| Thank you. Ndaudza nurse zvamataura. Please garai mumirire, nurse achakudaidzai. | Thank you. I have passed this to the nurse. Please take a seat, the nurse will call you. |  |
| Thank you. Ndiri kudaidza nurse izvozvi. Please garai pano, nurse ari kuuya. | Thank you. I am calling the nurse now. Please stay here, the nurse is coming. |  |

## What the helper says to a patient at home (online visits)

In `app/prompts.py`.

| Shona | Meant to say | OK? |
|---|---|---|
| Mhoroi. Ndiri helper yeClinic, handisi doctor. Ndichakubvunzai maQuestions mashoma kuti nurse akurumidze kukubatsirai. Chii chiri kukunetsai nhasi? | Hello. I am the clinic's helper, not a doctor. I will ask you a few short questions so the nurse can help you sooner. What is troubling you today? |  |
| Thank you. Ndaudza nurse zvamataura. Clinic ichakufonerai munguva pfupi. | Thank you. I have passed this to the nurse. The clinic will call you back soon. |  |
| Izvi zvingangova emergency. Fonerai ambulance pa 994, kana kuti endai kuClinic kana kuHospital iri pedyo izvozvi. | This may be an emergency. Call an ambulance on 994, or go to the nearest clinic or hospital now. |  |

## The status page a patient at home comes back to

In `app/prompts.py`.

| Shona | Meant to say | OK? |
|---|---|---|
| MaAnswers enyu ari kuna nurse. Clinic ichakufonerai pa {p}. | Your answers are with the nurse. The clinic will call you on {p}. |  |
| Nurse ane case yenyu. Doctor achasarudza zvinotevera. | The nurse has your case. A doctor will decide what happens next. |  |
| Please uyai kuHospital. Uyai neReference {n}. | Please come to the hospital. Bring your reference {n}. |  |
| Doctor aona case yenyu. Hamudi mushonga parizvino. Kana mukanzwa worse, uyai kuHospital. | The doctor has looked at your case. You do not need medicine now. If you feel worse, come to the hospital. |  |
| Doctor akunyorerai prescription. Iratidzei kuPharmacy ipi neipi kuti mutenge mushonga wenyu. | The doctor has written you a prescription. Show it at any pharmacy to buy your medicine. |  |

## First aid for a patient at home with a danger sign (NOT YET REVIEWED BY A CLINICIAN)

In `app/prompts.py`.

| Shona | Meant to say | OK? |
|---|---|---|
| Mugarisei akatwasuka. Musamurega achirara pasi akatambarara. | Sit them upright. Do not let them lie flat. |  |
| Sunungurai mbatya dzakasungirira mumuchengete akadzikama. | Loosen tight clothing and keep them calm. |  |
| Murarisei nerutivi, kure nezvinhu zvakaoma. | Lay them on their side, away from anything hard. |  |
| Musaisa chinhu mumuromo make uye musamubata nesimba. | Do not put anything in their mouth and do not hold them down. |  |
| Murarisei nerutivi kuti akwanise kufema. | Lay them on their side so they can breathe. |  |
| Musamupa chikafu kana kunwa. Garai naye. | Do not give food or drink. Stay with them. |  |
| Dzvanyai pachironda nemachira akachena, murambe muchidzvanya. | Press firmly on the wound with a clean cloth and keep pressing. |  |
| Kana zvichikwanisika, simudzai pari kubuda ropa. | If you can, raise the bleeding part. |  |
| Rarai nerutivi rwekuruboshwe muzorore. | Lie down on your left side and rest. |  |
| Endai nemumwe munhu kana zvichikwanisika. | Bring someone with you if you can. |  |
| Musamurutsisa. | Do not make them vomit. |  |
| Kana iri snake bite, musazungunusa gumbo kana ruoko rwakarumwa. Musacheka kana kusveta pakarumwa. | For a snake bite, keep the bitten limb still. Do not cut or suck the bite. |  |
| Endai nechigaba kana packet yazvo. | Bring the container or packet with you. |  |
| Garai naye. Musamusiya ari ega. | Stay with them. Do not leave them alone. |  |
| Bvisai zvinhu zvaangashandisa kuzvikuvadza. | Remove anything they could use to hurt themselves. |  |
| Mupei ORS kana mvura yakachena zvishoma zvishoma, kazhinji, muri munzira. | Give small sips of oral rehydration solution (ORS) or clean water, often, while you travel. |  |
| Kana muchiyamwisa, rambai muchiyamwisa. | If you breastfeed, keep breastfeeding. |  |
| Mudziyisei mwana. | Keep the child warm. |  |
| Murarisei pasi mumutonhodze. | Keep them lying down and cool. |  |
| Musamirira kuti fever idzike musati maenda. | Do not wait for the fever to go down before you go. |  |
| Garai nemurwere mumuchengete akadzikama. | Stay with the patient and keep them calm. |  |
| Musamupa chikafu kana mushonga kunze kwekunge health worker akuudzai. | Do not give food or medicine unless a health worker tells you to. |  |
| Nurse ane case yenyu uye achakufonerai pa {p}. | The nurse has your case and will call you on {p}. |  |

## What the helper says: the questions

In `app/prompts.py`.

| Shona | Meant to say | OK? |
|---|---|---|
| Ndiani ari kurwara, imi here kana mwana? | Who is unwell, you or a child? |  |
| Mune makore mangani? | How old are you? |  |
| Mwana ane makore mangani? | How old is the child? |  |
| Zvakatanga rini? | When did it start? |  |
| Zviri kuita worse here? | Is it getting worse? |  |
| Pain iri papi? | Where is the pain? |  |
| Pain yacho yakanyanya here? | Is the pain very bad? |  |
| Muri kupisa muviri here? | Do you have a fever? |  |
| Mwana ari kupisa muviri here? | Does the child have a fever? |  |
| Mune problem yekufema here? | Are you struggling to breathe? |  |
| Mwana ane problem yekufema here? | Is the child struggling to breathe? |  |
| Mwana ari kugona kunwa kana kuyamwa here? | Is the child able to drink or breastfeed? |  |
| Muri kurutsa here? | Are you vomiting? |  |
| Mwana ari kurutsa here? | Is the child vomiting? |  |
| Pane maFits here? | Have there been any fits? |  |
| Pane ropa ramuri kuona here? | Have you seen any blood? |  |
| Mutsipa wenyu wakaoma here? | Is your neck stiff? |  |
| Muri pregnant here? | Are you pregnant? |  |
| Mune chronic condition here, seSugar kana BP? | Do you have a long-term illness, such as diabetes or high blood pressure? |  |
| Mwana ane chronic condition here? | Does the child have a long-term illness? |  |
| Pane mishonga yamuri kunwa mazuva ano here? | Are you taking any medicines these days? |  |
| Pane mishonga iri kunwiwa nemwana mazuva ano here? | Is the child taking any medicines these days? |  |
| Mune allergy kune mumwe mushonga here? | Is there any medicine that does not agree with you? |  |
| Pane chimwe chiri kukunetsai here? | Is anything else troubling you? |  |

## Calling a ticket in the waiting room (the number is put in)

In `app/prompts.py`.

| Shona | Meant to say | OK? |
|---|---|---|
| Ticket fourteen, please endai kuna nurse. | Ticket 14, please go to the nurse. |  |
| Ticket fourteen, please endai kuna doctor. | Ticket 14, please go to the doctor. |  |
| Ticket fourteen, please endai kuPharmacy. | Ticket 14, please go to the pharmacy. |  |

## How to take a medicine, said at the pharmacy

In `app/prompts.py`.

| Shona | Meant to say | OK? |
|---|---|---|
| Shandisai mushonga uyu once a day. | Use this medicine once a day. |  |
| Shandisai mushonga uyu twice a day. | Use this medicine twice a day. |  |
| Shandisai mushonga uyu three times a day. | Use this medicine three times a day. |  |
| Shandisai mushonga uyu only when needed. | Use this medicine only when you need it. |  |
| Shandisai mushonga uyu sezvamaudzwa naPharmacist. | Use this medicine as the pharmacist has told you. |  |

## A warning for a community, when the national picture shows a risk

In `app/prompts.py`.

| Shona | Meant to say | OK? |
|---|---|---|
| Warning: maCases emanyoka ari kuwanda muArea yenyu. Boilai mvura yekunwa, mugeze maoko neSoap. | Warning: diarrhoea is spreading in this area. Boil your drinking water and wash your hands with soap. |  |
| Warning: malaria iri kuwanda muArea yenyu. Rarai muNet, muuye kuClinic kana muine temperature. | Warning: malaria is rising in this area. Sleep under a net, and come to the clinic if you have a fever. |  |
| Warning: maChest infections ari kuwanda. Uyai kuClinic kana mwana aine problem yekufema. | Warning: chest infections are rising. Come to the clinic if a child is struggling to breathe. |  |

## Ticket numbers in words

In `app/voice.py`.

| Shona | Meant to say | OK? |
|---|---|---|
| one | 1 |  |
| two | 2 |  |
| three | 3 |  |
| four | 4 |  |
| five | 5 |  |
| six | 6 |  |
| seven | 7 |  |
| eight | 8 |  |
| nine | 9 |  |
| ten | 10 |  |
| eleven | 11 |  |
| twelve | 12 |  |
| fifteen | 15 |  |
| twenty | 20 |  |
| twenty one | 21 |  |
| thirty | 30 |  |
| forty five | 45 |  |
| ninety nine | 99 |  |
| one hundred | 100 |  |
| one hundred and one | 101 |  |
| one hundred and ten | 110 |  |
| one hundred and twenty five | 125 |  |

## The patient's screen

In `web/index.html`.

| Shona | Meant to say | OK? |
|---|---|---|
| Helper yaNurse. Taurai, mubatsirwe fast | The nurse's helper. Speak, and be helped sooner |  |
| Welcome kuClinic | Welcome to the clinic |  |
| Ndichakubvunzai maQuestions mashoma chete. MaAnswers enyu anoenda kuna nurse, kuti akubatsirei fast. | I will ask you a few short questions. Your answers go to the nurse, so she can help you sooner. |  |
| Voice renyu rinoRecordwa kuti nurse azoriteerera. RinoDeletwa after 24 hours. | Your voice is recorded so the nurse can listen to it. It is deleted after one day. |  |
| Startai kutaura | Start speaking |  |
| Onai sample patient | Watch a sample patient |  |
| Helper iyi iComputer, haisi doctor. Kana iri emergency, udzai nurse izvozvi. | This helper is a computer, not a doctor. If it is serious, tell the nurse now. |  |
| Sample, voice reComputer | Sample, synthetic voice |  |
| More options | More options |  |
| Helper | Helper |  |
| Ticket yenyu | Your number |  |
| Next patient | Next patient |  |
| Send | Send |  |
| Mic inozviOn nekuzviOff yoga | The microphone opens and closes by itself |  |
| Typai instead yekutaura | Type instead of speaking |  |
| Ratidza English pasi pemaWords | Show English under the words |  |
| Ndapedza, finish | I have finished |  |
| Light | Light |  |
| Dark | Dark |  |
| Follow phone | Match phone |  |
| Staff | Staff |  |
| Sample patients | Sample patients |  |
| Close | Close |  |
| Vanhu ava havasi real, uye maVoice avo ndeeComputer. Helper inovanzwa nekuvapindura chaizvo. | These people are made up and their voices are synthetic. The helper really hears them and really answers. |  |
| Pressai mic mutaure | Tap the microphone to speak |  |
| Okay, taurai, ndiri kuteerera | Speak now, I am listening |  |
| Ndiri kurecorder zvamataura… | Writing down what you said… |  |
| One moment, ndiri kufunga… | Thinking… |  |
| Helper iri kutaura, please teererai | The helper is speaking, listen |  |
| Typai answer yenyu | Type your answer |  |
| Mic haisi kuworker. Typai answer yenyu. | The microphone is not working. Type your answer. |  |
| Pane error yaitika. Tryai futi. | Something went wrong. Please try again. |  |
| Imi | You |  |
| Sample patient | Sample patient |  |
| Patient ari kutaura… | The patient is speaking… |  |
| Typai pano | Type here |  |
| Done | Finished |  |
| Nurse ari kuuya | The nurse is coming |  |
| Tryai futi | Try again |  |
| Thank you. Garai mumirire, nurse achakudaidzai. | Thank you. Please take a seat, the nurse will call you. |  |
| Thank you. Nurse adaidzwa izvozvi. Please garai pano. | Thank you. The nurse has been called. Please stay here. |  |
| Number yenyu yefoni | Your phone number |  |
| Nurse chete ndiye anoona number iyi, kuti akufonerei. InoDeletwa after 24 hours. | Only the clinic's nurse sees this number, to call you back. It is deleted after one day. |  |
| Helper yeClinic | The clinic's helper |  |
| Reference yenyu | Your reference |  |
| Ndichakubvunzai maQuestions mashoma chete. MaAnswers enyu anoenda kuna nurse, uye clinic ichakufonerai. | I will ask you a few short questions. Your answers go to the nurse, and the clinic will call you back. |  |
| Helper iyi iComputer, haisi doctor. Kana iri emergency, fonerai {n} izvozvi. | This helper is a computer, not a doctor. If it is serious, call {n} now. |  |
| Thank you. Clinic ichakufonerai pa {p} munguva pfupi. | Thank you. The clinic will call you on {p} soon. |  |
| Emergency | This may be an emergency |  |
| Fonerai ambulance pa {n}, kana kuti endai kuClinic kana kuHospital iri pedyo izvozvi. | Call an ambulance on {n}, or go to the nearest clinic or hospital now. |  |
| Fonerai {n} | Call {n} |  |
| Pamuri kuenda: | While you get help: |  |
| Ziva kuti case yenyu yasvika papi | Check your progress |  |
| Onai visit yenyu yekupedzisira | Check my last visit |  |
| Onai sample e-prescription | See a sample e-prescription |  |
| Chengetai link iyi. Muchada maDigits matatu ekupedzisira enumber yenyu yefoni. | Keep this link. You will need the last 3 digits of your phone number. |  |

## The status page's own words

In `web/status.html`.

| Shona | Meant to say | OK? |
|---|---|---|
| Ziva kuti case yenyu yasvika papi | Check your progress |  |
| Typai maDigits matatu ekupedzisira enumber yenyu yefoni | Type the last 3 digits of your phone number |  |
| Ratidza | Show |  |
| Reference yenyu | Your reference |  |
| Emergency | This may be an emergency |  |
| Peji iyi inozvichinja yoga. | This page updates by itself. |  |
| Kana muchiri kunzwa zvakaipa, fonerai ambulance pa {n}, kana kuti endai kuClinic kana kuHospital iri pedyo izvozvi. | If you still feel very unwell, call an ambulance on {n}, or go to the nearest clinic or hospital now. |  |
| Fonerai {n} | Call {n} |  |
| Typai maDigits matatu. | Type 3 digits. |  |
| Pane error yaitika. Tryai futi. | Something went wrong. Please try again. |  |
| E-prescription | E-prescription |  |
| Reference {n} | Reference {n} |  |
| Downloadai prescription (PDF) | Download prescription (PDF) |  |
| Sample, haisi patient chaiye | Sample, not a real patient |  |
| Sample: maDigits ndi 567. | Sample: the digits are 567. |  |
| Iratidzei kuPharmacy ipi neipi. Pharmacist achatarisa kuti iri kushanda. | Show this at any pharmacy. The pharmacist will check it is valid. |  |

## Sample patients: answers every Shona patient shares

In `samples/patients.json`.

| Shona | Meant to say | OK? |
|---|---|---|
| Ndini patient. | It is me. |  |
| Ndine thirty years. | I am thirty years old. |  |
| Zvakastarta yesterday. | It started yesterday. |  |
| Kwete, zviri just the same. | No, it is about the same. |  |
| Zviri moderate, hazvina kunyanya. | It is not too bad. |  |
| Kwete, ndiri kufema normal. | No, I am breathing well. |  |
| Hongu, ari kunwa normal. | Yes, drinking well. |  |
| Kwete, hapana blood. | No, there is no blood. |  |
| Kwete, handisi pregnant. | No, I am not pregnant. |  |
| Kwete, handina chronic condition. | No, I have no long-term illness. |  |
| Kwete, handisi kunwa maPills. | No, I am not taking any medicines. |  |
| Kwete, handina allergy. | No, none. |  |
| Kwete, that's all. | No. |  |
| Handisi kufeeler mushe. | I am not feeling well. |  |
| Pa area yandakuudzai iyoyo. | Where I told you. |  |
| Kwete, handina temperature. | No, I do not have a fever. |  |
| Kwete, handisi kuvomita. | No, I am not vomiting. |  |
| Kwete, hapana maFits. | No, no fits. |  |
| Kwete, neck haisi stiff. | No, my neck is not stiff. |  |

## Sample patients: their own lines

In `samples/patients.json`.

| Shona | Meant to say | OK? |
|---|---|---|
| Mwana wangu ane eight months ari kutadza kubreather, uye ane temperature. | (A mother whose baby cannot breathe) opening line |  |
| Mwana wangu. | answer about: who |  |
| Ane eight months. | answer about: age |  |
| Kubva last night. | answer about: onset |  |
| Hongu, zviri kuita worse. | answer about: worse |  |
| Hongu, ari kutadza kubreather. | answer about: breathing |  |
| Hongu, ane temperature. | answer about: fever |  |
| Kwete, hapana maFits. | answer about: fits |  |
| Kwete, haasi kuvomita. | answer about: vomiting |  |
| Mwana wangu ane diarrhoea kubva yesterday. | (A child with diarrhoea who has stopped drinking) opening line |  |
| Mwana wangu. | answer about: who |  |
| Ane one year. | answer about: age |  |
| Kubva yesterday evening. | answer about: onset |  |
| Hongu, zviri kuita worse, ava weak. | answer about: worse |  |
| Hongu, zvakanyanya. | answer about: severity |  |
| Kwete, ari kufema normal. | answer about: breathing |  |
| Kwete, haachagoni kunwa kana kuyamwa, uye ari kuvomita everything yaanodya. | answer about: drinking |  |
| Kwete, hapana blood mustool. | answer about: bleeding |  |
| Haachagoni kunwa kana kuyamwa. | answer about: other |  |
| Kwete, haana temperature. | answer about: fever |  |
| Hongu, ari kuvomita everything yaanodya. | answer about: vomiting |  |
| Kwete, hapana maFits. | answer about: fits |  |
| Ndiri pregnant, seven months, ndatanga kubleeder this morning. | (A pregnant woman who is bleeding) opening line |  |
| Ndine twenty six years. | answer about: age |  |
| This morning. | answer about: onset |  |
| Hongu, bleeding iri kuwedzera. | answer about: worse |  |
| Hongu, ndiri kubleeder. | answer about: bleeding |  |
| Hongu, ndiri pregnant, seven months. | answer about: pregnancy |  |
| Mwana wangu ane three years aita maFits twice last night. | (A child who had fits in the night) opening line |  |
| Mwana wangu. | answer about: who |  |
| Ane three years. | answer about: age |  |
| Last night. | answer about: onset |  |
| Hongu. | answer about: worse |  |
| Hongu, twice last night. | answer about: fits |  |
| Hongu, ane temperature. | answer about: fever |  |
| Husband wangu arumwa nenyoka paleg, tanga tiri kumunda. | (A man bitten by a snake) opening line |  |
| Husband wangu. | answer about: who |  |
| Ane forty years. | answer about: age |  |
| One hour ago. | answer about: onset |  |
| Gogo vangu vaita faint kumba, vazomuka asi vava confused. | (A grandmother who fainted) opening line |  |
| Gogo vangu. | answer about: who |  |
| Vane seventy years. | answer about: age |  |
| This morning. | answer about: onset |  |
| Hongu, vane sugar. | answer about: chronic |  |
| Ndave nemaWeeks ndisingarare, uye ndava nemaThoughts ekuzviuraya. | (A man with thoughts of ending his life) opening line |  |
| Ndine thirty five years. | answer about: age |  |
| Three weeks ago. | answer about: onset |  |
| Hongu. | answer about: worse |  |
| Ndazvicheka neknife paruoko, blood riri kubuda rakawanda uye harisi kumira. | (A deep cut that will not stop bleeding) opening line |  |
| Ndine twenty nine years. | answer about: age |  |
| Twenty minutes ago. | answer about: onset |  |
| Hongu, blood rakawanda. | answer about: bleeding |  |
| Mwana wangu ane three weeks ane temperature, uye haasi kuyamwa. | (A three-week-old baby with fever) opening line |  |
| Mwana wangu. | answer about: who |  |
| Ane three weeks. | answer about: age |  |
| Kubva yesterday. | answer about: onset |  |
| Kwete, haasi kuyamwa. | answer about: drinking |  |
| Hongu. | answer about: worse |  |
| Hongu, ane temperature. | answer about: fever |  |
| Ndine headache yakanyanya, ndine temperature, uye neck yangu iri stiff. | (A man with a bad headache, fever and a stiff neck) opening line |  |
| Ndine twenty four years. | answer about: age |  |
| Kubva last night. | answer about: onset |  |
| Hongu, zviri kuita worse. | answer about: worse |  |
| Hongu, zvakanyanya. | answer about: severity |  |
| Hongu, ndine temperature. | answer about: fever |  |
| Hongu, neck iri stiff. | answer about: neck |  |
| Head neneck. | answer about: where |  |
| Kwete. | answer about: vomiting |  |
| Mwana ane four years ane diarrhoea ine blood kubva yesterday. | (A child with blood in the stool) opening line |  |
| Mwana wangu. | answer about: who |  |
| Ane four years. | answer about: age |  |
| Kubva yesterday. | answer about: onset |  |
| Zviri just the same. | answer about: worse |  |
| Hongu, pane blood mustool. | answer about: bleeding |  |
| Hongu, ari kunwa. | answer about: drinking |  |
| Kwete. | answer about: fever |  |
| Kwete, haasi kuvomita. | answer about: vomiting |  |
| Ndiri pregnant, five months, ndine temperature yakanyanya uye ndiri kuita maChills. | (A pregnant woman with a high fever) opening line |  |
| Ndine twenty two years. | answer about: age |  |
| Two days ago. | answer about: onset |  |
| Hongu. | answer about: worse |  |
| Hongu, five months. | answer about: pregnancy |  |
| Kwete, hapana bleeding. | answer about: bleeding |  |
| Hongu, yakanyanya. | answer about: fever |  |
| Mwana wangu atsva nemvura inopisa paruoko nepachest. | (A child scalded with hot water) opening line |  |
| Mwana wangu. | answer about: who |  |
| Ane two years. | answer about: age |  |
| One hour ago. | answer about: onset |  |
| Hongu, ari kuchema nepain. | answer about: severity |  |
| Paruoko nepachest. | answer about: where |  |
| Ndine stomach pain yakanyanya kubva last night, handisi kugona kumira straight. | (Severe abdominal pain since the night) opening line |  |
| Ndine thirty one years. | answer about: age |  |
| Kubva last night. | answer about: onset |  |
| Hongu, zviri kuita worse. | answer about: worse |  |
| Hongu, zvakanyanya. | answer about: severity |  |
| Mustomach, kuright side. | answer about: where |  |
| Kwete. | answer about: vomiting |  |
| Kwete. | answer about: fever |  |
| Ndave nethree weeks ndichikosora, uye yesterday ndakosora blood. | (Three weeks of cough, now with blood) opening line |  |
| Ndine forty five years. | answer about: age |  |
| Three weeks ago. | answer about: onset |  |
| Hongu. | answer about: worse |  |
| Hongu, ndakosora blood yesterday. | answer about: bleeding |  |
| Ndine headache uye ndiri kukosora. | (A woman with a headache and a cough) opening line |  |
| Ndine thirty two years. | answer about: age |  |
| Two days ago. | answer about: onset |  |
| Kwete, zviri just the same. | answer about: worse |  |
| Front yemusoro. | answer about: where |  |
| Slight temperature chete. | answer about: fever |  |
| Ndauya kuzotora maPills angu eBP, apera. | (A woman collecting her blood pressure tablets) opening line |  |
| Ndine sixty four years. | answer about: age |  |
| MaPills apera yesterday. | answer about: onset |  |
| Hongu, ndine BP. | answer about: chronic |  |
| Hongu, maPills eBP. | answer about: medicines |  |
| Kwete, hapana pain. | answer about: severity |  |
| Mwana wangu ane six years ane rash inoita itch pamaoko kubva last week. | (A child with an itchy rash) opening line |  |
| Mwana wangu. | answer about: who |  |
| Ane six years. | answer about: age |  |
| Last week. | answer about: onset |  |
| Kwete, ari kufema normal. | answer about: breathing |  |
| Hongu, ari kudya nekunwa normal. | answer about: drinking |  |
| Kwete, haana temperature. | answer about: fever |  |
| Pamaoko ese. | answer about: where |  |
| Ndine back pain kubva pandakasimudza saga last week. | (Backache after lifting a sack) opening line |  |
| Ndine forty two years. | answer about: age |  |
| Last week. | answer about: onset |  |
| Lower back. | answer about: where |  |
| Ndauya kuzobaiwa injection yeFamily planning. | (A family planning injection) opening line |  |
| Ndine twenty eight years. | answer about: age |  |
| Hapana problem, ndauya kuinjection chete. | answer about: onset |  |
| Kwete, hapana pain. | answer about: severity |  |
| Ndine toothache, yava netwo days. | (A toothache) opening line |  |
| Ndine thirty four years. | answer about: age |  |
| Two days ago. | answer about: onset |  |
| Zino rekuback. | answer about: where |  |
| Ndauya nemwana kuzobaiwa maInjection ake enine months. | (A baby due for immunisation) opening line |  |
| Mwana wangu, asi haasi sick. | answer about: who |  |
| Ane nine months. | answer about: age |  |
| Haasi sick, ndauya kumaInjection chete. | answer about: onset |  |
| Kwete, ari kufema normal. | answer about: breathing |  |
| Hongu, ari kuyamwa normal. | answer about: drinking |  |
| Kwete, haana temperature. | answer about: fever |  |
| Kwete, haasi kuvomita. | answer about: vomiting |  |
| Ndine flu nechest, zvava nethree days. | (A cold, with every danger sign denied) opening line |  |
| Ndine twenty one years. | answer about: age |  |
| Three days ago. | answer about: onset |  |
| Kwete, handina problem yekufema. | answer about: breathing |  |
| Kwete, hapana blood randiri kuona. | answer about: bleeding |  |
| Kwete, handisi pregnant. | answer about: pregnancy |  |
| Kwete, handina temperature. | answer about: fever |  |
| Kwete, neck haisi stiff. | answer about: neck |  |
| Ndine maPeriod pains, dumbu rinorwadza every month. | (Period pain) opening line |  |
| Ndine seventeen years. | answer about: age |  |
| Every month. | answer about: onset |  |
| Blood remaPeriods chete, harina kuwanda. | answer about: bleeding |  |
| Zviri moderate. | answer about: severity |  |
| Lower stomach. | answer about: where |  |

