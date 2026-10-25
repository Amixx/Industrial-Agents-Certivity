# Product video prompt

A 90-second motion-graphics product video for the sudo submission to the Certivity challenge, in four parts:

| Time | Part | What it shows |
| --- | --- | --- |
| 0:00 to 0:37 | Main goal | Requirements from a spec |
| 0:37 to 0:55 | How it works | Which steps a model does, which steps code does, and what each adds to the score |
| 0:55 to 1:07 | What we miss | Where the engine falls short of the expert answer, and why |
| 1:07 to 1:27 | Sub-goal | What changes when a regulation changes |
| 1:27 to 1:30 | Close | The closing line |

The "How it works" part is recorded on the About page (`/about?preview`). Two of the parts need pages that don't exist yet:
- "What we miss" needs the coverage page from `docs/coverage-ui-prompt.md`.
- The sub-goal part needs the pages from `docs/regulation-change-ui-prompt.md`.

Paste everything below the line into the video tool and attach the ten reference frames from `docs/video-refs/`. The brief and storyline come first, then the look, the reference frames, the shot list, and the screen recordings to capture.

---

## Brief

Make a 90-second, 16:9, 1920×1080, 30 fps motion-graphics product launch video for **sudo**, built for the Certivity challenge at the Industrial AI hackathon ("In collaboration with Certivity").

sudo reads a product specification and its exploded view, decides which UN Regulations apply, and writes the requirement list a homologation engineer starts from. Every requirement quotes the regulation and points to its page and paragraph, so a reviewer checks it in seconds instead of searching for it. The demo products are an automotive **rear lamp** and a **front bumper** for an M1 passenger car.

Under the hood, code and models split the work. Code parses all 56 regulations into numbered paragraphs with their pages and owns every citation: no model ever writes a page number. A model picks the regulations that apply (7 of 56 for the front bumper, and the engineer can override). All 3,240 candidate paragraphs are scored: Jev, TypeSafe's decision model, answers five calibrated yes/no questions per paragraph, the language model rates relevance, and code keeps the best. Each kept paragraph becomes standalone obligations, and code checks every number against the source. Last, the model drops rows an expert wouldn't list and merges lists that are one obligation. On the worked example, rules alone score 35 F2, the best single model pass 68 and the full engine 79. A 9-billion-parameter model on a laptop can write the drafts and still score 55.

sudo shows where it falls short. On the worked example, where Certivity published the expert's answer, a coverage page lists every expert requirement sudo did not match and the reason. The engine leans toward recall on purpose: a missed requirement costs the engineer more than an extra one to strike out.

sudo also keeps an assessment current. When a new version of a cited regulation comes out, the engineer uploads it. sudo compares it with the old version paragraph by paragraph and shows which requirements are modified, removed or added, each with a reason and the new paragraph. This step uses no model. It aligns the old and new versions sentence by sentence across the whole document, so a paragraph that was only renumbered (5.1.4.1, for example) is not flagged. It takes about a second, the same input always gives the same result, and on the held-out pair it finds 61 of the 64 changes the expert listed.

The video has to make one idea land: **from regulation PDF to requirement and back, every step is traceable. That includes the steps where it falls short and the ones that follow a change in the regulation.** The audience is a jury of homologation and compliance engineers. They should come away knowing:
- what goes in and what comes out;
- that they can click any requirement and see the exact paragraph it came from;
- that models make the judgement calls and code keeps the citations true;
- that the team measured where the engine misses and says so;
- that a new regulation version shows up as a diff they can review, not a fresh start.

## Storyline (90 s)

### Part one, requirements from a spec (0:00 to 0:37)

1. **Opening (0:00 to 0:04).** A clean, white-to-light-gray studio sweep, lit softly from above like a product photo. A rear lamp sits in the middle on an invisible surface with a soft contact shadow. Its LEDs switch on, red, and it slowly turns. The wordmark "sudo" fades in, with "In collaboration with Certivity" under it as a small mono label.
2. **The problem (0:04 to 0:08).** Regulation PDFs fan out across the studio like a deck of cards: UN R48, R148, R150, R10 and dozens more. A counter ticks to 56. Headline: "56 UN Regulations. One rear lamp." The pages recede into depth, out of focus.
3. **Input to pipeline (0:08 to 0:15).** Chapter tag "01 The engine". A floating app screen: the spec and the exploded-view image drop into "Start an assessment". The pipeline progress runs step by step: Product profile, Regulation selection, Paragraph scan, Requirement extraction, Assessment ready. Counters for Parts, Regulations, Paragraphs and Requirements roll up as each step finishes. Cut to a close crop of the seven-stage engine table from the About page, rows sliding in one after another.
4. **The exploded view (0:15 to 0:23).** Chapter tag "02 Point at a part". The 3D rear lamp sits assembled, then explodes along its axis into its parts: outer lens, retro-reflector, seal, reflector, LED modules on PCB, housing, fasteners. The cursor glides over the parts; each one lights up in turn. It stops on **LED modules on PCB**. The hover card pops: the part number, its name, and three teal numerals for regulations, requirements and paragraphs, with the regulation list underneath. A one-second cut shows the same view on the **front bumper**, its fascia, grill, radar, camera, sensors, absorber and stiffener sliding apart, to show it works on any product. Back on the lamp, click.
5. **The breakdown graph (0:23 to 0:31).** Chapter tag "03 From regulation to requirement". The view morphs into the process graph with its four numbered columns: 1 Spec, 2 Product profile, 3 Regulations, 4 Paragraphs.
   - Everything the LED part touches stays lit; the rest dims.
   - Edges draw left to right: from the spec, to the product profile facets, to the regulations that were kept, to the paragraph groups.
   - Regulations that were ruled out sit dimmed, each with its exclusion reason.
   - The camera pushes along the lit path and ends on one paragraph group, which narrows into its list of requirements in the right-hand panel.
6. **The cited paragraph (0:31 to 0:37).** Chapter tag "04 Traceability". The cursor clicks one requirement and the PDF drawer slides in from the right.
   - The drawer header shows the requirement id, regulation and version, page and paragraph, in mono.
   - The regulation page renders, the rest of the page dims, and the cited paragraph is highlighted with a teal outline.
   - The camera pushes in until the paragraph fills the frame next to the requirement, so the viewer can see that one came from the other.
   - The cursor steps to the next requirement ("2 of N") and the highlight jumps to a new paragraph.

### Part two, how it works (0:37 to 0:55)

7. **Code owns the citations (0:37 to 0:43).** Chapter tag "05 How it works". The About page's "How it works" diagram floats in, paused, and steps forward one stage at a time.
   - Step 02, Parse: 56 regulation PDFs collapse into stacks of numbered paragraphs, each with its page.
   - Step 04, Regulation pick: the model keeps 7 of 56 regulations for the front bumper; the rest dim. A small "Override" tag shows the engineer can change it.
8. **Models judge, code checks (0:43 to 0:49).** The diagram steps on.
   - Step 06, Paragraph screening: citations flicker past as a counter rolls to 3,240 candidate paragraphs. Three small flow cards: "Jev, five yes/no questions", "Language model, relevance", "Code keeps the best".
   - Steps 08 and 09: a kept paragraph splits into standalone obligations, and a "Verify" tick lands on each number checked against the source.
   - Steps 10 to 12: rows an expert wouldn't list drop out, a list merges into one obligation, and the final JSON row settles.
9. **Cost against quality (0:49 to 0:55).** Cut to the "Cost against quality" chart. The Pareto line draws itself, and the dots label in order: rules alone 35, best single model pass 68, full engine 79. A fourth dot, a 9B model on a laptop, reads 55. Caption: "Most of the gain comes from the engine around the model."

### Part three, what we miss (0:55 to 1:07)

10. **The score, said plainly (0:55 to 0:58).** Chapter tag "06 What we miss". The coverage page floats in. Two large numerals sit side by side: "167 of 190" expert requirements matched, and F2 "0.794". The label underneath reads "Worked example, scored by the challenge platform". A thin bar shows the share matched and the share missed.
11. **Every miss, with its reason (0:58 to 1:03).** The camera crops in on the list of missed expert requirements. They are grouped by reason, each group with a count:
   - "Paragraph ranked below the cut": the row shows the paragraph's score next to the cut, for example 0.12 against 0.15.
   - "Expert splits it finer": one expert row per table row or list item, where sudo wrote one requirement for the paragraph.
   - "Same paragraph, different wording": the matcher did not pair them.

   The cursor opens one miss. It shows the expert's text, its paragraph, and sudo's nearest requirement on that paragraph beside it. Nothing is hidden or rounded off.
12. **Why it leans toward recall (1:03 to 1:07).** A second card slides in: "Rows the expert did not list: 125". The note under it reads: "We keep them. A missed requirement costs more than an extra one to strike out." Below it is a short list of regulations left out on purpose, each with a one-line reason: UN R7, R23 and R3, which UN R148 and R150 replaced. Caption: "Where it misses, and why."

### Part four, when a regulation changes (1:07 to 1:27)

13. **A new version lands (1:07 to 1:12).** A short title card in the light studio: "Regulations change. Your requirements follow." Then chapter tag "07 When a regulation changes".
    - This part runs on the **front bumper** assessment, because its update touches paragraphs the assessment cites.
    - On the floating Updates screen, the table of cited regulations shows UN R48 at 9.3.0, with 9.4.0 available.
    - A PDF named "UN R48 9.4.0" drops onto the upload zone.
    - The steps tick through fast: Identify regulation, Parse both versions, Align paragraphs, Map requirements, Done.
    - A mono caption: "9.3.0 to 9.4.0, compared in about a second".
14. **The regulation diff (1:12 to 1:17).** Chapter tag "08 What changed". The run page reads like a pull request: changed paragraphs on the left rail with +/− counts, and diff hunks in the main column.
    - The camera pushes into one hunk header on a paragraph the bumper cites, then into a word-level edit: the old words struck through, the new ones highlighted in mint.
    - The rail skips unchanged and renumbered paragraphs. Only real wording changes are shown.
    - A number card floats in: "61 of 64 expert changes found", label "Held-out pair, sentence-level alignment, no model".
15. **What it does to the requirements (1:17 to 1:23).** Chapter tag "09 What it means for you".
    - The view scrolls to the requirement impact band. Modified, removed and added rows fall into place, each tagged and counted, with the word diff on a modified requirement.
    - Cut to the graph in diff mode. The R48 node flips from "9.3.0" to "9.4.0", changed paragraph groups light up in mint while the rest dim, and new edges draw to the requirements they touch.
    - The cursor clicks one new paragraph, and the PDF drawer opens on the new version with that paragraph highlighted.
16. **Apply (1:23 to 1:27).** The cursor clicks "Apply update". The button turns into "Applied", the requirement counter rolls to its new value, and the R48 version on the assessment reads 9.4.0.

### Close (1:27 to 1:30)

17. **Close (1:27 to 1:30).** An empty light studio. Headline: "Every requirement points to its *paragraph*.", with "paragraph" in italic in the accent colour. Under it are the sudo wordmark and "In collaboration with Certivity".

## Look and feel

Use the BMW Product Intelligence trailer as the reference for staging, camera, cards and pacing. Don't copy its colour, its brand, or its blue background.

**Background: a clean photo studio, the whole way through.**
- Every shot, title cards included, sits on a seamless white-to-light-gray sweep (`#ffffff` at the top to about `#e9ebeb` at the floor), lit by a soft overhead key light that falls off gently toward the edges.
- Floating screens and cards cast a soft, realistic contact shadow onto the floor plane, as in a product photo.
- No coloured blobs, no blue or teal washes, no bokeh, no speed lines, no gradients in hue. The only colour in the frame comes from the app screens and the accent.
- There are no dark title cards. The sweep stays the same from the first frame to the last, so the video reads as one continuous studio.

From the reference, keep:
- **Floating screens.** Real app screen recordings sit on a single sheet with a 1px light-gray border and a soft, large, low-opacity shadow. They are tilted a few degrees in 3D perspective and drift slowly, a 2 to 4 percent scale or rotation over the shot. The camera never sits still. (`01-floating-screen.jpg`)
- **Chapter tags.** A small white card in the top-left corner, with a mono number and a short rule ("01 ——") above the chapter name in sentence case. (`01-floating-screen.jpg`, `06-title-card.jpg`)
- **Detail crops.** After each wide screen, cut to an enlarged crop of the same UI, such as a counter row, a hover card or a PDF paragraph. It floats as its own card, then the camera pulls back out. (`02-detail-crop-numerals.jpg`, `04-panel-crop.jpg`, `08-number-card.jpg`)
- **Caption cards.** One short caption card per scene, bottom-left, overlapping the screen edge: a sentence-case line in a clean sans, with a mono uppercase sub-label under it. (`03-caption-card-on-screen.jpg`, `09-caption-over-screen.jpg`)
- **Flow cards.** Steps of a trace as separate cards joined by a thin line that draws from one to the next. (`07-flow-cards.jpg`)
- **Cursor.** A clean macOS pointer with smooth eased paths and a slight press-in on click, followed by a small dark name tag ("Troy, homologation"). Clicks ripple once, subtly. (`05-cursor-name-tag.jpg`, `10-action-card-cursor.jpg`)
- **Title cards.** Two lines of large sentence-case type, centred, with one word in the accent colour and a mono label row under it. (`06-title-card.jpg`)
- **Pacing.** Calm and confident. One idea per shot, 2 to 4 seconds each, ease-in-out on every move, no whip pans or bounces.

Brand, from the app:
- **Studio colours.** Ink `#02312f` for headlines and text. The accent word and numerals in the studio are teal `#0b7a70`, because the bright teal is too light on white.
- **Colours inside the app screens.** They keep the app's own palette: dark ink `#031e1c`, teal `#27dac2` for numerals, mint `#79f2de` for selection and hover.
- **Type.** Instrument Serif for headlines, with one italic word in the accent colour. Hanken Grotesk for body text and captions. JetBrains Mono in small uppercase for labels, ids, regulation numbers and page references.
- **The app itself.** Record it in dark mode: dark ink screens floating in a white studio, as the reference does with its screens. The app is a strict grid with 1px rules and 3px corners. Show it as it is. Shadows belong to the frame around the screens, never inside them.

Copy rules:
- Sentence case everywhere. No exclamation marks, no emoji, no sparkle icons, no "AI" badges.
- No em dashes or middle dots as separators in on-screen text.
- Avoid "seamless", "effortless", "powerful", "unlock", "leverage", "elevate", "robust", "cutting-edge".
- No three-word taglines like "Fast. Accurate. Compliant."
- In the "What we miss" part, state the numbers flatly. No apology, no spin, no "only".

Sound: a restrained, modern electronic bed at about 100 BPM with a soft pulse. It builds slightly into the exploded view, drops to a sparser pattern for "What we miss", picks up again for the regulation change and resolves on the close. Light UI sounds on clicks and the explode. Cut on the beat. No voice-over (optional lines are below if you want one).

## Reference frames

Ten stills from the BMW trailer are in `docs/video-refs/`; attach them. Copy their layout, card style, crop and type scale. Ignore their pale blue wash: our background is the neutral white-to-gray studio described above.

| File | Take from it | Use it for |
| --- | --- | --- |
| `01-floating-screen.jpg` | A full app screen tilted in perspective, fading into the floor, with the chapter tag top-left | Every wide app shot (scenes 3, 4, 5, 7, 10, 11) |
| `02-detail-crop-numerals.jpg` | A row of large numerals cropped out of the app as a floating card | Pipeline counters (3), coverage numerals (7), diff summary (11) |
| `03-caption-card-on-screen.jpg` | A screen filling the frame, with a caption card overlapping its bottom-left corner | Exploded view (4), Updates screen (10) |
| `04-panel-crop.jpg` | One panel of the UI lifted out and floating, slightly tilted, on its own | Hover card (4), missed-requirement list (8), requirement impact band (12) |
| `05-cursor-name-tag.jpg` | A cursor with a dark name tag over a form, the crop tight on the action | Every click: part click (4), requirement click (6), opening a miss (8) |
| `06-title-card.jpg` | A two-line centred headline, one coloured word, a mono label row with rules | "56 UN Regulations" (2), "Regulations change" (10), close (14) |
| `07-flow-cards.jpg` | Separate cards joined by a drawn line, with a caption card underneath | The trace in the graph (5), the expert text beside sudo's nearest requirement (8) |
| `08-number-card.jpg` | One large numeral with a short ranked list and a thin share bar below | "167 of 190" with its matched and missed bar (7), "125 rows" (9) |
| `09-caption-over-screen.jpg` | A caption card over a dense screen, the screen slightly out of focus behind it | PDF drawer (6), diff hunks (11) |
| `10-action-card-cursor.jpg` | A single action card with the primary button and the cursor about to click | "Apply update" (13) |

## Shot list

| Time | Scene | On screen | Caption | Reference |
| --- | --- | --- | --- | --- |
| 0:00 to 0:04 | Opening | Rear lamp in a white studio, LEDs switch on red, slow turn. Wordmark "sudo", label "In collaboration with Certivity". | none | none |
| 0:04 to 0:08 | Problem | Regulation PDF covers fan out, counter to 56, pages recede out of focus. | "56 UN Regulations. One rear lamp." | 06 |
| 0:08 to 0:12 | 01 The engine | Floating "Start an assessment" screen, spec and exploded view drop in, pipeline steps tick through, counters roll. | "A spec goes in" / SPEC AND EXPLODED VIEW | 01, 02 |
| 0:12 to 0:15 | 01 The engine, crop | Seven-stage table: Product profile, Regulation pick, Paragraph screening, Relevance ranking, Obligation drafts, Expert-likeness cut, Consolidation. | "Seven stages, each one checkable" / PROFILE TO CONSOLIDATION | 04 |
| 0:15 to 0:19 | 02 Point at a part | 3D lamp assembled, then explodes into seven parts. A one-second cut to the front bumper exploding into its parts. | "Every part of the product" / REAR LAMP, FRONT BUMPER | 03 |
| 0:19 to 0:23 | 02 Point at a part, crop | Cursor hovers parts, stops on LED modules on PCB, hover card with regulations, requirements and paragraphs. Click. | "Point at a part" / LED MODULES ON PCB | 04, 05 |
| 0:23 to 0:27 | 03 Regulation to requirement | Process graph, four columns, the LED part's path lit, the rest dimmed, edges drawing left to right. | "From regulation to requirement" / SPEC, PROFILE, REGULATIONS, PARAGRAPHS | 01, 07 |
| 0:27 to 0:31 | 03 Regulation to requirement, crop | Push along the lit path to a paragraph group; the right panel lists its requirements with regulation, version, page and paragraph. | "Excluded regulations keep their reason" | 04 |
| 0:31 to 0:35 | 04 Traceability | Click a requirement, PDF drawer slides in, cited paragraph highlighted, rest of page dimmed. | "Read the paragraph it has to meet" / R148 00, P. 23, § 5.4.1 | 05, 09 |
| 0:35 to 0:37 | 04 Traceability, crop | Push in on the highlight beside the requirement text, step to "2 of N", highlight jumps. | "Every requirement, cited" | 09 |
| 0:37 to 0:40 | 05 How it works | About page diagram, step 02 Parse: 56 regulations become numbered paragraphs with pages. | "Code owns every citation" / NO MODEL WRITES A PAGE NUMBER | 01 |
| 0:40 to 0:43 | 05 How it works, crop | Step 04 Regulation pick: 7 of 56 kept for the front bumper, the rest dimmed, override tag. | "The model picks, the engineer can override" / 7 OF 56 | 04 |
| 0:43 to 0:46 | 05 How it works | Step 06 Paragraph screening, citations flicker, counter to 3,240, three flow cards. | "Every candidate paragraph scored" / JEV, LANGUAGE MODEL, CODE | 07 |
| 0:46 to 0:49 | 05 How it works, crop | Steps 08 to 12: obligations split out, numbers verified, the final JSON row. | "Models judge, code keeps the citations true" / VERIFY AGAINST THE SOURCE | 04 |
| 0:49 to 0:55 | 05 How it works | Cost against quality chart, Pareto line draws, dots 35, 68, 79 and the laptop model at 55. | "Most of the gain comes from the engine" / F2 ON THE WORKED EXAMPLE | 02, 08 |
| 0:55 to 0:58 | 06 What we miss | Coverage page, "167 of 190" matched and F2 0.794, matched and missed bar. | "Measured against the expert's answer" / WORKED EXAMPLE, PLATFORM SCORE | 01, 08 |
| 0:58 to 1:03 | 06 What we miss, crop | Missed expert requirements grouped by reason with counts; one opened, expert text beside sudo's nearest requirement. | "Every miss, with its reason" / BELOW THE CUT, SPLIT FINER, WORDED DIFFERENTLY | 04, 05, 07 |
| 1:03 to 1:07 | 06 What we miss, crop | "Rows the expert did not list: 125" with the recall note; regulations left out on purpose, each with its reason. | "Where it misses, and why" | 08 |
| 1:07 to 1:09 | Title card | "Regulations change. Your requirements follow." | none | 06 |
| 1:09 to 1:12 | 07 When a regulation changes | Front bumper Updates screen, cited regulations with versions, "UN R48 9.4.0" PDF dropped on the upload zone, steps tick through. | "Upload the new version" / UN R48 9.3.0 TO 9.4.0, ABOUT 1 S | 03 |
| 1:12 to 1:15 | 08 What changed | Run page as a pull request: changed-paragraph rail, diff hunks, summary numerals for amended, new and deleted. | "Only the paragraphs that changed" / RENUMBERING AND FORMATTING LEFT OUT | 01, 02 |
| 1:15 to 1:17 | 08 What changed, crop | One hunk header on a cited paragraph and a word-level edit, struck old words, mint new words. | "§ <cited paragraph>, amended in 9.4.0" | 09 |
| 1:17 to 1:20 | 09 What it means for you | Requirement impact band, modified, removed and added rows with counts and a word diff. | "Each requirement updated, with its reason" | 04 |
| 1:20 to 1:23 | 09 What it means for you, crop | Graph in diff mode, R48 node flips version, changed paragraph groups light mint, PDF drawer opens on the new paragraph. | "Traced through the same graph" | 01, 07 |
| 1:23 to 1:27 | Apply | "Apply update" clicked, "Applied", counter rolls, version reads 9.4.0. | "Review it, then apply it" | 10 |
| 1:27 to 1:30 | Close | "Every requirement points to its *paragraph*." Wordmark and Certivity label. | none | 06 |

The technical figures (56 regulations, 7 of 56, 3,240 paragraphs, 35, 68, 79, 55, 61 of 64) come from the About page and `out/README.md` (61 of 64 is the v10 held-out upload). The citations (R148 00, p. 23, § 5.4.1 and the R48 hunk paragraph), the scores (167 of 190, F2 0.794, 125 extra rows) and the example cut (0.12 against 0.15) are placeholders from the run log. Replace them with what the recordings show. Every number on screen must be one the app actually produced.

## Optional voice-over (about 230 words)

> A rear lamp has to meet dozens of UN Regulations. Finding the right paragraphs takes days.
> sudo reads the spec and the exploded view, picks the regulations that apply, and screens every paragraph.
> Point at a part, and you see what it has to meet.
> Follow it from the spec, through the regulations, down to each requirement.
> Click one, and the regulation opens on the cited paragraph.
>
> Under the hood, code parses all 56 regulations into numbered paragraphs with their pages. No model ever writes a page number.
> A model keeps the regulations that apply: 7 of 56 for the front bumper, and an engineer can override.
> Then 3,240 candidate paragraphs are scored. Jev, TypeSafe's decision model, answers five yes/no questions per paragraph, our language model rates relevance, and code keeps the best.
> Each kept paragraph becomes obligations, and code checks every number against the source.
> Rules alone score 35. The best single model pass scores 68. The full engine scores 79.
>
> On the worked example, sudo matches 167 of the expert's 190 requirements.
> Every one it misses is listed, with the reason: ranked below the cut, split differently, or worded differently.
> It also writes rows the expert didn't. We keep them, because a missed requirement costs more than an extra one.
>
> It works the same on a front bumper.
>
> Then a regulation changes. Upload the new version.
> sudo aligns the two versions sentence by sentence, with no model. A paragraph that was only renumbered isn't flagged.
> On the held-out pair it finds 61 of the 64 changes the expert listed.
> Each requirement it touches is modified, removed or added, with the reason and the new paragraph.
> Review it in the same graph, then apply it.
>
> Every requirement points to its paragraph.

## Screen recordings to capture

Record the real app in dark mode at 2560×1440 or larger, because the crops need the extra pixels. Hide the browser chrome and keep the cursor visible and moving slowly. Record one clean take per clip, with 2 seconds of stillness before and after.

Part one, on the rear lamp assessment:

1. **Landing page** (`/`): the rear lamp at rest with the lamp on, then the Assembled to Exploded slider dragged all the way.
2. **New assessment** (`/new`): uploading the rear lamp spec PDF and exploded view, then the pipeline progress running to "Assessment ready" with the counters filling.
3. **About page** (`/about`): scroll to "The engine" so the seven stage rows animate in.
4. **Exploded view** (`/a/<id>/exploded`, 3D mode): explode the lamp, hover across three or four parts, rest on "LED modules on PCB" until the hover card shows, then click.
4b. **Front bumper exploded view** (`/a/8f93fc71/exploded`, 3D mode): drag from assembled to exploded once and hover two parts (radar, fascia). Only 2 seconds are used.
5. **Graph** (`/a/<id>/graph?part=<led part id>`): the lit path for that part. Hover one regulation, then click a paragraph group so the right panel lists its requirements.
6. **PDF drawer**: click a requirement so the drawer opens on the highlighted paragraph, then press next twice.
7. **Stills**: the rear lamp spec PDF and the four regulation PDF covers (R48, R148, R150, R10), for the fan-out. For the opening, a clean render of the 3D lamp from the landing page on a transparent background, lamp on.

Part two, on the About page (`/about?preview`). Pause both diagrams and step them with the arrow keys; on autoplay they move every 2.6 seconds:

8a. **How it works**: step through 02 Parse, 04 Regulation pick, 06 Paragraph screening (let the citations flicker), 07, 08, 09 Verify, 10 and 12 (the JSON row).
8b. **The engine table**: click "Language model", then "Rules", so their marks light up.
8c. **Cost against quality**: scroll slowly so the Pareto line draws itself, and hold on the 35, 68, 79 and 55 labels.
8d. **When a regulation changes** diagram: steps 03, 04 (5.1.4.1 renumbered, not flagged) and 07, for part four.

Part three, after the coverage page from `docs/coverage-ui-prompt.md` is built:

8. **Coverage page** (`/a/<id>/coverage`): hold on the numerals, scroll slowly through the reason groups, then open one miss.
9. **Coverage page, extras and exclusions**: scroll to the rows the expert did not list and the excluded regulations.

Part four, on the front bumper assessment (`8f93fc71`). Its UN R48 9.3.0 to 9.4.0 run changes 5 cited paragraphs; the rear lamp's R148 run changes none, so it has nothing to show in the impact band:

10. **Updates start page** (`/a/<id>/updates`): the cited-regulation table. Drag the R48 9.4.0 PDF from `regulations/pdf/UN_R48/latest/` onto the upload zone and let the steps run to the run page.
11. **Run page** (`/a/<id>/updates/<run>`): a slow scroll from the summary numerals through the diff rail and two or three hunks, hovering a hunk's affected requirement ids, then down to the requirement impact band.
12. **Graph diff** (`/a/<id>/graph?update=<run>`): flip the before and after toggle once, then click a new paragraph group and let the PDF drawer open on the highlighted new paragraph.
13. **Apply**: click "Apply update" and hold on "Applied" and the new counts for 2 seconds.
14. **Still**: the R48 9.4.0 PDF cover, for the drop animation.
