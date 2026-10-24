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
  - The golden set fits EARS well: "shall" throughout, explicit subject, conditions first.
- **ISO/IEC/IEEE 29148**, the international standard for requirements: singular, unambiguous, verifiable, with "shall" for binding requirements.
- **INCOSE Guide to Writing Requirements**: rules such as one thought per requirement, active voice, no vague terms, explicit units.
- **US conventions:** MIL-STD-961 and the NASA systems-engineering handbook use a shall/will/should hierarchy. Here "will" states a fact or intent, not an obligation; in UN regulations "shall" is the only binding word.

## Recommendation

- **Text:** one obligation per requirement, "shall", explicit subject, conditions first (EARS-shaped), near-verbatim otherwise. Keep passive voice, references and SI units as in the source. Don't paraphrase into "nicer" engineering language, because it risks drifting from the golden meaning.
- **Internally**, extract a structure first and render the sentence from it:
  - `subject`, `condition`, `modal` (shall / shall not), `constraint`, `value`, `unit`, `exceptions`, `references[]`
  - It makes the output consistent, lets the UI highlight values, and gives us `test_case` almost for free ("Measure X under condition Y; pass if ≤ value unit").
- **Always** fill in `paragraph` and cite the base version.

## Open question

**Which "US format" did Certivity mean?** Three readings, each with a different consequence:

1. **Units:** US customary vs SI. UN regulations are SI, so keep the source units. This is the transcript's units remark.
2. **Regulatory system:** US FMVSS vs UN ECE regulations. We may only cite UN regulations from the index anyway.
3. **Requirement-writing convention:** a US style (MIL-STD-961, shall/will/should) vs the international or European one (ISO 29148, EARS).

Settle it with Certivity, or from the meeting audio, before tuning the text style. Reading 3 is the only one that would change our sentences.
