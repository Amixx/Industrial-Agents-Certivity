# Regulation list for a front bumper

The held-out case is a front bumper. This page is the lookup for its regulation list: read the
spec, tick the features it has, and paste the matching `--include` / `--exclude` line. The
lines are checked: each one was run through `brain.pipeline --no-llm` on its variant and the
selected regulations matched the table.

Spec variants are in `data/synthetic/bumper-*/spec.md`. The scope texts behind every decision
come from the corpus (`brain.select_regs.documents`).

## Lookup table

Every bumper gets the base set. Each feature adds regulations to it.

| Spec feature | Regulations in | Regulations out | Rule |
|---|---|---|---|
| Any front bumper of an M1 car (base) | R42, R127, R26, GTR 9 | R94, R137, R32, R131, R157, R171, R114, R43, R79 | R42 approves the front protective device; R127 tests the bumper with the legform; R26 covers the external surface, bumpers (6.5), grilles (6.3), plate brackets (6.15); GTR 9 see below. The rest are whole-vehicle or other-system regulations |
| Lamps of any kind | + R48 | | Installation regulation whenever a lamp is installed on the vehicle, as in the lamp gold |
| Front fog lamp, cornering lamp | + R149 | R19, R37, R128 | R149 replaces R19; light sources are never cited |
| Position lamp, direction indicator, daytime running lamp | + R148 | R6, R7, R37, R128 | R148 replaces R6, R7 and R87 |
| Electronics: LED, sensors, radar, camera, actuators, harness | + R10 | R155, R156 | EMC for any electrical/electronic sub-assembly. Cyber security and software updates are approvals of the vehicle maker's management system |
| Radar used for emergency braking | + R152 | R131, R157, R171 | R152 is the AEBS regulation for M1/N1; R131 is for M2, M3, N2, N3 only. Marginal: see below |
| Towing eye, registration plate bracket | nothing new | | R26 already covers both (towing devices in 2.7.5, plate brackets in 6.15.1). Towing devices (EU 1005/2010) and plate space (EU 1003/2010) are not in the index |
| Ultrasonic parking sensors | nothing beyond R10 | R152 | Parking aid is not emergency braking. Reversing motion detection (R158) is not in the index |

## Paste-ready lines

Each line forces every regulation in or out explicitly. Excluding a regulation the selector
did not pick is a no-op, so the long `--exclude` tail costs nothing and guards the LLM path.
Each line was run with `brain.pipeline --no-llm` on its variant and selected exactly the
regulations listed.

`bumper-plain`: GTR 9, R127, R42, R26

```
--include "UN R42" "UN R127" "UN R26" "UN GTR 9" --exclude "UN R10" "UN R48" "UN R148" "UN R149" "UN R152" "UN R94" "UN R137" "UN R32" "UN R131" "UN R157" "UN R171" "UN R114" "UN R128" "UN R37" "UN R19" "UN R6" "UN R7" "UN R155" "UN R156" "UN R161" "UN R162" "UN R163" "UN R43" "UN R79"
```

`bumper-tow-plate`: GTR 9, R127, R42, R26

```
--include "UN R42" "UN R127" "UN R26" "UN GTR 9" --exclude "UN R10" "UN R48" "UN R148" "UN R149" "UN R152" "UN R94" "UN R137" "UN R32" "UN R131" "UN R157" "UN R171" "UN R114" "UN R128" "UN R37" "UN R19" "UN R6" "UN R7" "UN R155" "UN R156" "UN R161" "UN R162" "UN R163" "UN R43" "UN R79"
```

`bumper-parking-sensors`: base + R10

```
--include "UN R42" "UN R127" "UN R26" "UN GTR 9" "UN R10" --exclude "UN R48" "UN R148" "UN R149" "UN R152" "UN R94" "UN R137" "UN R32" "UN R131" "UN R157" "UN R171" "UN R114" "UN R128" "UN R37" "UN R19" "UN R6" "UN R7" "UN R155" "UN R156" "UN R161" "UN R162" "UN R163" "UN R43" "UN R79"
```

`bumper-radar`: base + R10, R152

```
--include "UN R42" "UN R127" "UN R26" "UN GTR 9" "UN R10" "UN R152" --exclude "UN R48" "UN R148" "UN R149" "UN R94" "UN R137" "UN R32" "UN R131" "UN R157" "UN R171" "UN R114" "UN R128" "UN R37" "UN R19" "UN R6" "UN R7" "UN R155" "UN R156" "UN R161" "UN R162" "UN R163" "UN R43" "UN R79"
```

`bumper-fog-lamps`: base + R10, R48, R149

```
--include "UN R42" "UN R127" "UN R26" "UN GTR 9" "UN R10" "UN R48" "UN R149" --exclude "UN R148" "UN R152" "UN R94" "UN R137" "UN R32" "UN R131" "UN R157" "UN R171" "UN R114" "UN R128" "UN R37" "UN R19" "UN R6" "UN R7" "UN R155" "UN R156" "UN R161" "UN R162" "UN R163" "UN R43" "UN R79"
```

`bumper-position-indicators`: base + R10, R48, R148

```
--include "UN R42" "UN R127" "UN R26" "UN GTR 9" "UN R10" "UN R48" "UN R148" --exclude "UN R149" "UN R152" "UN R94" "UN R137" "UN R32" "UN R131" "UN R157" "UN R171" "UN R114" "UN R128" "UN R37" "UN R19" "UN R6" "UN R7" "UN R155" "UN R156" "UN R161" "UN R162" "UN R163" "UN R43" "UN R79"
```

`bumper-sensors-fog`: base + R10, R48, R148, R149

```
--include "UN R42" "UN R127" "UN R26" "UN GTR 9" "UN R10" "UN R48" "UN R148" "UN R149" --exclude "UN R152" "UN R94" "UN R137" "UN R32" "UN R131" "UN R157" "UN R171" "UN R114" "UN R128" "UN R37" "UN R19" "UN R6" "UN R7" "UN R155" "UN R156" "UN R161" "UN R162" "UN R163" "UN R43" "UN R79"
```

`bumper-full`: base + R10, R48, R148, R149, R152

```
--include "UN R42" "UN R127" "UN R26" "UN GTR 9" "UN R10" "UN R48" "UN R148" "UN R149" "UN R152" --exclude "UN R94" "UN R137" "UN R32" "UN R131" "UN R157" "UN R171" "UN R114" "UN R128" "UN R37" "UN R19" "UN R6" "UN R7" "UN R155" "UN R156" "UN R161" "UN R162" "UN R163" "UN R43" "UN R79"
```
For a lamp without electronics (a halogen fog lamp, no harness named), move `"UN R10"` from
`--include` to `--exclude`. For a radar that only serves adaptive cruise control or blind-spot
detection, move `"UN R152"` to `--exclude`.

## Decisions per regulation

In:
- **R42** Front and rear protective devices. Scope: M1 vehicles, behaviour of the front and rear protective devices in a low-speed collision. The bumper is that device.
- **R127** Pedestrian safety. Scope: M1 and N1. The bumper decides the lower and upper legform results; the 02 series is mandatory for new approvals since 31 December 2017 (11.2).
- **R26** External projections of M1 vehicles. Defines "bumper" and "bumper cover" (2.11, 2.12) and has its own bumper section (6.5), grilles (6.3), air intake flaps (6.12) and plate brackets (6.15). Its scope excludes only indirect-vision devices and the ball of towing devices.
- **GTR 9** Pedestrian safety, global text. Applies to the frontal surfaces of category 1-1 vehicles over 500 kg. Marginal; see the next section.
- **R48** Installation of lighting and light-signalling devices, M, N and O. In whenever the bumper carries a lamp.
- **R149** Road illumination devices: front fog lamps, cornering lamps, headlamps. Combines R19, R98, R112, R113, R119, R123.
- **R148** Light-signalling devices: position lamps, direction indicators, daytime running lamps. Combines R4, R6, R7, R23, R38, R50, R77, R87, R91.
- **R10** EMC. Applies to vehicles and to components and separate technical units fitted to them; any electronics in the bumper is an ESA.
- **R152** AEBS for M1 and N1, only when the spec says the radar serves emergency braking.

Out:
- **R19, R6, R7** legacy regulations replaced by R149 and R148; the lamp gold never cites the legacy ones.
- **R37, R128** light sources; not cited in the lamp gold even for an LED lamp.
- **R94, R137** frontal collision and restraint systems: occupant protection in a full-vehicle crash test. The bumper beam contributes, but the regulation approves the vehicle's restraint system.
- **R32** rear-end collision: the rear of the vehicle.
- **R131** AEBS for M2, M3, N2, N3: wrong vehicle category for M1.
- **R157, R171** ALKS and DCAS: driver-assist systems of the whole vehicle, not the bumper's sensors.
- **R155, R156** cyber security and software updates: management systems of the vehicle maker.
- **R114** airbag modules for replacement airbag systems: aftermarket airbags. It matched only through "wiring harness" (see "Selector" below).
- **R43, R79, R161, R162, R163** glazing, steering, anti-theft, immobilisers, alarms: other systems.

## GTR 9 against R127

Recommendation: keep GTR 9 in. It needs a sign-off from the team's regulatory reviewer.

- Under the 1958 Agreement the approval basis is R127, which transposes GTR 9 with the same legform limits. An EU-centred expert would cite R127 alone, and the silver labels mark GTR 9 as not cited (unsure).
- Against that, the index holds exactly one GTR, and it is this one. It was added on purpose, either as the answer or as a decoy, and the two cannot be told apart from the data.
- The costs are lopsided. GTR 9 duplicates R127's rows, so a wrong GTR 9 costs about 0.04 requirement F2 at about 350 rows. A missed GTR 9 loses all its gold rows, about 0.07 or more because recall counts four times. Including it pays off above about a 0.35 chance that the gold cites it.
- Opus put that chance at 0.35. The selector and the LLM review both pick it. Our own estimate is 0.3 to 0.4.

## Second opinion

One call to Opus 5.5 through `claude -p` (subscription, no API key) with the scope texts of 27
candidates and all eight variant specs. Its answer agrees with the table on every variant. Its
probabilities: GTR 9 0.35 (marginal include), R152 for a radar that serves AEBS 0.40 (marginal
include), R171 for a radar 0.15, R155/R156 0.15 to 0.20. It named regulations outside the
index: EU 1003/2010 (plate space), EU 1005/2010 (towing devices), the Radio Equipment Directive
for a 77 GHz radar, and R46 only if the camera were an indirect-vision device. None of these
are in the corpus, so none can be cited.

## Selector against the table

`uv run python -m brain.pipeline data/synthetic/<variant> --no-llm`, after the rule change below:

| Variant | Deterministic picks | Differs from the table |
|---|---|---|
| `bumper-plain` | GTR 9, R127, R42, R26 | no |
| `bumper-tow-plate` | GTR 9, R127, R42, R26 | no |
| `bumper-parking-sensors` | GTR 9, R10, R127, R42, R26 | no |
| `bumper-radar` | GTR 9, R10, R127, R42 | misses R26 and R152 |
| `bumper-fog-lamps` | GTR 9, R10, R149, R127, R48, R42, R26 | no |
| `bumper-position-indicators` | GTR 9, R10, R127, R48, R148, R42, R26 | no |
| `bumper-sensors-fog` | R10, R48, GTR 9, R149, R127, R148, R42, R26 | no |
| `bumper-full` | GTR 9, R10, R48, R149, R127, R148, R42, R26 | misses R152 |

The review gate covers both differences, which is why every line forces the base set in:

- R42 (0.49) and R26 (0.46) sit just above the 0.40 cut. R42 depends on the spec saying "front
  protective device"; R26 on a part named exactly "bumper cover". The radar spec says "bumper
  cover with radar-transparent zone", and R26 drops out.
- R152 never scores: its scope talks about collisions and an on-board system, not radar or
  bumpers. Whether it applies is a judgement on the spec's wording, which a lexical score
  cannot make.

### Rule change in `brain/select_regs.py`

Two terms were pulling in regulations that had nothing to do with the product. With the
cached LLM profiles of the two original bumper specs, the deterministic selector picked R152,
R157 and R171 on "passenger car" alone, and R114 on "wiring harness" alone. The deterministic
profile of `bumper-full` also picked R114.

- The vehicle category ("M1", "passenger car") is no longer a product term. `_categories_ok`
  already checks it against the scope; as a term it matched every whole-vehicle regulation for
  M1.
- A term made only of electrical words ("wiring harness", "PCB", the vocabulary `profile.py`
  uses to detect electronics) no longer counts as a product term. It is evidence for EMC,
  which the EMC rule adds anyway.

After the change, the deterministic picks on the cached LLM profiles equal the LLM review's
picks on both original specs: plain GTR 9, R127, R26, R42; sensors and fog GTR 9, R10, R127,
R148, R149, R26, R42, R48.

## Notes for task 06

- `pipeline.review` forces a regulation in but keeps its lexical probability, so a forced
  R152 or R26 enters the decision model with `reg_prob` 0.00. Both still got rows on the radar
  variant (87 for R152, 25 for R26), but fewer than a selected regulation of the same size
  would. Setting the probability of a forced include to at least the selection threshold would
  fix it.
- On the deterministic path GTR 9 brings about 255 rows and R127 about 185. If the reviewer
  drops GTR 9, add `"UN GTR 9"` to `--exclude` and remove it from `--include`.
