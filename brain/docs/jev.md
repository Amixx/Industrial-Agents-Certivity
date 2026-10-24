# Jev (TypeSafe) on the judgement steps

A spike on 2026-10-24 comparing TypeSafe's Jev (`jev-1.14.0`) with Claude Opus 5.5 on three judgements the
engine makes. Jev answers typed yes/no questions ("Nouls") with calibrated probabilities. It is billed only for
input tokens, at $0.042 per million. The whole spike cost $0.45 of TypeSafe credit: 381 requests, 10.7M input
tokens. Opus ran through `claude -p` on the subscription.

How it was set up:

- The product profile goes in `state`.
- Each item to judge goes in its own question, together with its context.
- Code combines the answers (a truth table or a logistic fit). Jev never makes the keep/drop decision itself.

## Results

| Step | Jev | Opus | Jev cost and speed |
|---|---|---|---|
| Paragraph applicability, AUC (dev / a03 / a06) | 0.959 / 0.966 / 0.964 | 0.972 / 0.986 / 0.969 | $0.14 and 11 s per case (2,915 paragraphs, 117 calls) |
| Paragraph applicability, best F2 | 0.66 / 0.58 / 0.66 | 0.75 / 0.68 / 0.70 | |
| Regulation applicability, 13 cases, F2 at 0.7 | 0.965 | 1.000 | $0.002 and 2 s per case |
| Rewrite fidelity, AUC | 0.996 | 0.983 | $0.001 for 120 checks |

For reference, the current decision model scores AUC 0.841 on dev paragraphs, qwen3.5:9b 0.836 and gpt-5.5
0.975.

### 1. Paragraph applicability (the relevance step)

The items are the `decide.dataset` paragraphs of R10, R148, R150 and R48: 2,915 per case, with gold being the
paragraphs the expert cited. Each paragraph goes into its question with its label, heading path and parent
clause. Five Nouls per paragraph (the wording is under "Questions" below):

- technical requirement;
- about one of the product's own functions;
- about a function the product doesn't have;
- installation;
- EMC.

How they compare:

- **Jev:** a logistic regression over the Noul answers, fit on dev out of fold and applied unchanged to
  the synthetic cases.
- **Opus:** ran the pipeline's own relevance prompt on 300 paragraphs per case. That sample is every gold
  paragraph plus random others, reweighted so precision is fair. The Jev scores in the table are on the same
  300-paragraph samples.

What stood out:

- The single strongest Nouls are "technical requirement" (AUC 0.86) and "own function" (0.84 to 0.93).
  "Other function" is a strong negative (0.09 to 0.21).
- Jev plus the decision model reaches AUC 0.961 on dev.
- As a pre-filter, Jev's top 30% holds 98% / 100% / 99% of gold, and its top 20% holds 95 to 96%.
- Opus on a full case would take about 117 calls and 0.9M input tokens.

### 2. Regulation applicability from scope cards

The cards are the title plus the obligation base's best scope sentence, for all 56 regulations, run over the 13
labelled cases (40 gold regulation picks, all rear lamps). Three Nouls per card: device scope, installation,
and vehicle effect. Two rules are in code:

- EMC applies when the regulation's role is EMC and the product has electronics.
- A regulation is dropped when the consolidated regulation that supersedes it also applies.

What happened:

- Both rank every gold regulation first (AUC 1.000).
- Opus at 0.7 picks exactly the 40 gold regulations, with one call per case of about 13k input tokens.
- Jev at 0.7 picks 42, with one miss. The light-source regulations R128 and R37 are its remaining trap.

### 3. Rewrite fidelity

The items are 60 real rewrites from `out/dev-llm.json` (requirement text against its quote), plus 30 copies
with a number changed and 30 with "shall" and "shall not" swapped. One Noul: does the source support the
requirement.

| | AUC | Real rewrites passed | Wrong number caught | Flipped negation caught |
|---|---|---|---|---|
| Jev at 0.5 | 0.996 | 0.80 | 1.00 | 1.00 |
| Jev at 0.3 | | 0.90 | 1.00 | 0.97 |
| Opus (yes/no) | 0.983 | 0.97 | 1.00 | 1.00 |
| Number and negation rule (`kb.enrich.fidelity`) | 0.925 | 0.95 | 1.00 | 0.80 |

Most real rewrites that Jev rejects add context from the heading or parent clause ("the stop lamp", "for M1 and
N1"), which the quote alone doesn't show.

## Where Jev fits

1. **Relevance:**
   - Without an LLM: add the Noul answers to the decision model's features. AUC goes from 0.84 to 0.96 for
     $0.14 a case.
   - With an LLM: Jev pre-filters, and the strong model reads only the top 30%. That's about 3.3 times fewer
     strong-model reads for at most 2% of recall.
   - Jev alone doesn't replace Opus here: its best F2 is 0.07 to 0.12 lower.
2. **Regulation selection:** keep the one Opus call per case. Jev is the path when no LLM is used.
3. **Fidelity:** gate LLM rewrites in `verify.py` with Jev at 0.3. Give it the source together with its
   heading path and parent clause.

Caveats:

- Every labelled case is a rear lamp, and the logistic weights were fit on dev.
- The Opus relevance figures come from 300-paragraph samples.
- Neither the questions nor the prompts were tuned.

## Questions

Paragraph applicability. The product profile is in `state`, and each question ends with the paragraph as JSON
(regulation, label, heading path, parent clause, the first 1,500 characters of text). Each Noul is listed as
its question, then what yes means, then what no means.

- **technical**
  - Question: does this paragraph state a technical requirement: construction, performance, colour,
    dimensions, position, markings, or a limit the device or vehicle must meet in a test?
  - Yes: a minimum luminous intensity, a required colour, a mounting height, or a marking the device must
    carry.
  - No: a definition, scope statement, administrative step, or test equipment or laboratory set-up that
    sets no limit.
- **own_function**
  - Question: is this paragraph about one of the lamps, devices or functions that `product` has?
  - Yes: it concerns one listed in `product.functions` or `product.parts`.
  - No: it concerns a different one, or none in particular.
- **other_function**
  - Question: is this paragraph specifically about a lamp, device or function that `product` does not have?
  - Yes: for example a headlamp requirement for a product without one.
  - No: it concerns the product's own functions, or applies to every device the regulation covers.
- **installation**
  - Question: is this paragraph about how a device is installed on the vehicle rather than about the device
    itself?
  - Yes: the number of lamps, mounting position, geometric visibility, or electrical connection on the
    vehicle.
  - No: requirements on the device as a component.
- **electronics**
  - Question: is this paragraph about electromagnetic compatibility of electrical or electronic equipment?
  - Yes: emissions or immunity of a vehicle or an electronic sub-assembly.
  - No: optical, mechanical or administrative matters.

Regulation applicability. The card (regulation, title, scope) is in each question.

- **device_scope:** does the regulation approve or set requirements for devices of the same kind as `product`?
- **installation:** does the regulation set requirements for how devices like `product` are installed on a
  vehicle?
- **vehicle_effect:** does the regulation test or limit a vehicle property that `product` directly
  determines? For example, a bumper in a pedestrian impact test.

Fidelity. The question carries the source and the requirement, and asks whether the source supports the
requirement.

- Yes: every number, limit, condition and negation in the requirement is stated in the source; the wording may
  differ.
- No: the requirement changes a number, flips a negation, drops or adds a condition, or states something the
  source does not say.

The request is `POST https://api.typesafe.ai/v1/systemone` with `{"model": "jev-1.14.0", "state": {...},
"questions": {"<id>": {"type": "noul", "instructions": "...", "criteria": {"true": "...", "false": "..."}}}}`.
Keep each request under 64k tokens: 25 paragraphs with five Nouls each comes to about 31k.
