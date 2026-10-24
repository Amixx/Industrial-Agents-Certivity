# Requirement-writing framework

**Decision: minimal-edit EARS (Easy Approach to Requirements Syntax), checked against INCOSE
Guide to Writing Requirements v4 rules.**

- The dev gold already follows EARS: of 190 requirements, 122 start "The <system> shall", 22
  "When", 9 "Where", 7 "While", 1 "If … then". The platform judge matches on "scope, condition
  and constraint", which are the three EARS parts.
- How to write each requirement: one obligation per requirement; the subject comes from the
  heading path; the condition goes first with When/While/Where/If; numbers, units, references
  and passive voice stay verbatim; keep only "shall" and "shall not" (a "may" with no
  constraint appears once in the gold).
- Checks: definite article, no pronouns, no added vague terms; every number in the requirement
  must appear in the source (`brain/verify.py:faithful`).

Experiment to confirm it on the dev case: (A) verbatim sentences, (B) minimal-edit EARS, (C) full
EARS + INCOSE rewrite. The best requirement-level F2 wins.

Alternatives on file:

| Candidate | Use if / where |
|---|---|
| Verbatim "shall" extraction | Fallback if rewriting costs matches |
| Full EARS + INCOSE (active voice) | If the jury values requirement quality over matching the gold |
| ISO/IEC/IEEE 29148:2018 | Conformance claim in the pitch |
| Rupp / IREB boilerplate (MASTER) | Drop-in for IREB-trained (German) customers |
| Deontic / legal norm models (obligation, prohibition, permission) | Internal record; the modality filter |
| Planguage (Scale / Meter / Must) | UI display of measurable limits |
| Gherkin (Given / When / Then) | The optional `test_case` field |
| ReqIF | Export to DOORS / Polarion |

Sources: Mavin et al., EARS (RE'09); INCOSE GtWR v4 (2023); INCOSE IS2024 poster on LLM rewrites
dropping preconditions; MoDRE 2026 (few-shot prompting is best for template-based requirements).
