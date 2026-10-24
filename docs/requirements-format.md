# Requirement format

What one requirement in our output should look like, both its JSON and its sentence, and where that comes from.

## Two layers

1. **The file format is fixed** by Certivity's schema (`schemas/submission_main.schema.json`) and checked by `tools/validate.py`. Each requirement has:
   - `id`
   - `text`, at most 2,000 characters
   - `source`:
     - `regulation`: must be in `regulations/index.json`
     - `version`: the **base** version label
     - `page`: the PDF page
     - `paragraph`: optional, but always send it, because it rescues a page that's off by one
   - `test_case`: optional and not scored.
2. **The sentence style is ours to choose.** The scorer matches by meaning ("same scope, condition and constraint"), so the style only matters insofar as it keeps the meaning identical to the golden requirement. The golden set is the best evidence of what Certivity's experts consider a good requirement.

## What the organisers said (meeting transcript)

- "Each of the requirements have an ID, a text which is the text of the original form… and a source… version… page and paragraph." In other words, the text stays close to the regulation's own wording.
- "There are these frameworks which impose how the language should be written… shall… active voice, not passive voice… there are various frameworks." So requirement-writing frameworks exist and they care about them, but they named none.
- "All these units… you can just pick one… What is important is the citation." Units are a free choice; the citation is what matters.
- **The transcript doesn't record the remark about a US format.** It may be in the part of the audio the transcript garbled. See the open question below.

## What the golden set actually does (`cases/dev-rear-lamp/expected.json`, 190 requirements)

| Property | Count | Meaning for us |
|---|---|---|
| Uses "shall" | 189 / 190 | "shall" is the only modal. Never "must" (0) or "should" (0). |
| "shall not" | 24 | Prohibitions stay as prohibitions. |
| Starts with "The …" | 122 | Explicit subject: the lamp, the device, the vehicle, the light emitted. |
| Starts with a condition (When/If/Where/While/In the case) | 40 | Conditions go first, as in EARS. |
| Keeps references ("paragraph X", "Annex N") | 40 / 20 | Cross-references are **kept, not resolved**. |
| Carries a value with a unit (mm, cd, °, V, km/h, %) | 45 | Units are kept as in the source, which is SI. |
| Passive "shall be …ed" | 55 | Passive is **not** rewritten to active. They stay faithful to the source. |
| Length | median 213 characters, p90 382, max 881 | One obligation, but long obligations stay whole. |

**The three rewrite moves** the golden set makes on the regulation text (R48 examples):

1. **Give an explicit subject.** "Red light emitted by a lamp fitted on the rear … shall not be visible from the front" becomes "The vehicle shall not emit red light from a lamp fitted on the rear … that is visible from the front of the vehicle."
2. **Add context the section implies.** Under "6.10 Rear position lamp", "that point on the apparent surface…" becomes "…the apparent surface … **of the rear position lamp**…".
3. **Fold exceptions into the sentence.** "This condition shall not apply to the optional rear lamps" becomes "…, except that this condition shall not apply to the optional rear lamps."

Everything else stays near-verbatim, including the passive voice, references and units.

## Requirement-writing frameworks, for reference

- **EARS** (Easy Approach to Requirements Syntax, from Rolls-Royce in the UK, widely used in European aerospace and automotive). Templates:
  - Ubiquitous: "The <system> shall <response>."
  - Event: "When <trigger>, the <system> shall <response>."
  - State: "While <state>, the <system> shall <response>."
  - Unwanted behaviour: "If <condition>, then the <system> shall <response>."
  - Optional feature: "Where <feature>, the <system> shall <response>."
  - The golden set only partly fits EARS; see "Which format is it?" below.
- **ISO/IEC/IEEE 29148**, the international standard for requirements: singular, unambiguous, verifiable, with "shall" for binding requirements.
- **INCOSE Guide to Writing Requirements**: rules such as one thought per requirement, active voice, no vague terms, explicit units.
- **US conventions:** MIL-STD-961 and the NASA systems-engineering handbook use a shall/will/should hierarchy. Here "will" states a fact or intent, not an obligation; in UN regulations "shall" is the only binding word.

## Recommendation

- **Text:** one obligation per requirement, ISO verbal forms ("shall", "shall not", and "may" only for permissions), explicit subject, and the condition where the source puts it. Close to the source otherwise; turn tables into sentences. Keep passive voice, references and SI units as in the source. Don't paraphrase into "nicer" engineering language, because it risks drifting from the golden meaning.
- **Internally**, extract a structure first and render the sentence from it:
  - `subject`, `condition`, `modal` (shall / shall not), `constraint`, `value`, `unit`, `exceptions`, `references[]`
  - It makes the output consistent, lets the UI highlight values, and gives us `test_case` almost for free ("Measure X under condition Y; pass if ≤ value unit").
- **Always** fill in `paragraph` and cite the base version.

## Which format is it?

**Not strict EARS.** All 190 golden requirements, sorted by EARS pattern:

| Pattern | Count |
|---|---|
| Ubiquitous ("The X shall …") | 95 |
| Condition first: "When" (event) | 22 |
| Condition first: "While" (state) | 7 |
| Condition first: "If" (unwanted) | 1 |
| Condition first: "Where", "In the case of" or "For" (scope) | 27 |
| **Condition at the end** (", if …", ", except …", ", provided that …") | **30** |
| Other ("There shall be…", "In normal use there shall be no…", "… may be installed…") | 8 |

- Strict EARS always puts the condition first and always uses the system as the subject. The golden set keeps the condition wherever the regulation had it, and its subjects are often properties ("The intensity of the light…", "The markings…").
- It isn't verbatim either. The median similarity between a golden requirement and its closest source sentence is 0.68, and only 31 of 190 score 0.9 or higher.
- The biggest rewrites:
  - **Tables turned into sentences.** G-0029 spells out the minimum light-reflection values for Class IA and IB red retro-reflectors, which the source gives as a table.
  - **Exceptions merged** into the sentence.
  - **Subjects added** where the source sentence has none.

**What it does follow is the ISO/IEC verbal-form convention** (ISO/IEC Directives Part 2, also used by UNECE):

| Form | Meaning | In the golden set |
|---|---|---|
| shall / shall not | a requirement | 189 / 190 |
| should | a recommendation | 0 |
| may | a permission | 22, mostly inside obligations ("…may be installed…") |
| can | a possibility | 5 |
| must | (not used) | 0 |

**The US convention to avoid:** US federal plain-language guidelines tell drafters to write "must" for obligations and to avoid "shall". The European and international style is "shall" for a binding requirement, which the UN regulations themselves use: R48 has 625 "shall" and 0 "must". So our text uses "shall", never "must", and doesn't rewrite into US plain-language style.

**Summary of the format:** one obligation per requirement in ISO verbal forms, with an explicit subject, and the wording, units and references close to the source. EARS is a useful *internal* structure for the condition, subject and response, but it isn't a template to force onto the output.
