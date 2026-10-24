# Complex strategies: status

Updated: 24 Oct 23:29 CEST (system clock, `date`) by master (Cursor).
Task: brain/docs/todo/08-complex.md. Branch: big-swings. Setup done: yes (07 setup commit "swing master: setup"; this ledger created at 23:29).
Lanes A to G are finished. Do not edit their files except to read them. Do not edit `out/experiments/STATUS.md`.

## Budget

Approved by the owner: not asked yet.
Asked at 23:29: J $1, K $1, I $1, H $6, L $5. Which may spend?
Hard ceiling stays $70 for the whole event, of which the swings spent $14.92.
Until the owner answers, every lane's approved spend is **$0**. Do not make paid API calls. Unpaid steps may run. `claude -p` is not logged in.

## Lanes

| Lane | State | Last update | Current step | Spend so far | Lane file |
|---|---|---|---|---|---|
| J skip classes on votes7 | running | 23:29 | not started; agent launched at $0 | $0 | out/experiments/J.md |
| K same filter on votes4 | running | 23:29 | not started; agent launched at $0 | $0 | out/experiments/K.md |
| I table split into votes7 | running | 23:29 | not started; agent launched at $0 | $0 | out/experiments/I.md |
| H vote of three new runs | running | 23:29 | not started; dry-run only until spend is approved | $0 | out/experiments/H.md |
| L Sonnet 0.85 plus filter | running | 23:29 | not started; filter design on the existing file until spend is approved | $0 | out/experiments/L.md |

## Upload queue

No platform upload unless the owner says a slot is free. A lane may name one file. The master queues it only if its local F2 beats 0.702 by more than about 5 matches. `out/rear-lamp-swing-A-votes7.json` (351 rows, local 156 matched, F2 0.702) remains the first upload when a slot opens.

| Order | File | Lane | Question it answers | Predicted matched / F2 | Uploaded at | Platform matched / F2 |
|---|---|---|---|---|---|---|
| 1 | `out/rear-lamp-swing-A-votes7.json` (351 rows) | A | Does a vote of 14 runs beat every single run on the platform? | 157 / 0.707 (local 156 / 0.702) | | |

## Log

- 23:29 Ledger created. Budget not approved. Asked the owner: J $1, K $1, I $1, H $6, L $5. Started lanes J, K, I, H, L at $0. Paid API calls are forbidden until this file shows an approved amount. Order of value: J, K, I, H, L. Engine freeze for task 06 is 02:00. A result after about 01:30 is a recommendation, not a code change.
