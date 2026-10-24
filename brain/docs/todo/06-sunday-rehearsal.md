# 06 Dry-run the whole Sunday path and freeze the configuration

## Prompt

You are joining a hackathon team mid-event (Certivity challenge, Munich). Read
`brain/docs/todo/README.md` first: it has the event, the scores, the rules and the tools. Work
from `brain/`.

**Why this task exists.** On Sunday there are five hours and one chance: the last valid
held-out upload counts. Every step that has not been run end to end before 08:00 is a risk: a
missing remote, a missing key, a model timeout, a regulation with zero rows, a file that fails
validation, an upload made in the wrong order. The runbook is in `README.md` ("Sunday runbook");
this task proves it works and decides the configuration.

**Known gaps (24 Oct, evening).**
- This clone has only the `origin` remote (the team repository). The held-out case arrives in
  Certivity's package repository, so `git pull upstream main` fails until someone adds it:
  `git remote add upstream <package repository URL from the organisers>`. Check every
  machine that may run Sunday.
- `brain/.env` on the main machine holds only `OPENAI_KEY`. Whatever model runs on Sunday needs
  its key there, tested.
- `tools/fetch_regulations.py` must run again after the pull; the held-out case may add PDFs.
- `make check` needs `bun` for the frontend step.

**What to do.**
1. Follow the runbook literally on `data/synthetic/bumper-sensors-fog` as if it were the
   held-out case, on the machine that will run Sunday, and time each step.
   - Deterministic run, validate, check the per-regulation row counts.
   - The regulation review with the `--include` / `--exclude` lines from task 04.
   - One model-backed run with the configuration you propose (cost estimate and approval
     first; a bumper run with Fable 5.1 on every step is about $6, with Opus 5.5 about $2.40,
     about three times that when lamps and sensors bring in R48 and R10).
   - Validate and read 20 random rows against their quotes.
2. Fix what breaks. Wiring fixes in `brain/pipeline.py` are yours; prompt and selection changes
   belong to tasks 02 and 03, so report them there.
3. At 02:00, collect the results of tasks 01 to 05 and write the frozen configuration into the
   runbook: model per step, rewrite prompt version (commit), relevance configuration, the
   regulation review lines, the sub-goal command. Base the choice on dev platform scores and
   the bumper labels, not on dev alone.
4. Decide the end game with the team and write it down: who uploads, in what order, and which
   file is the last upload, both for when the platform shows held-out scores and for when it
   does not. Never end on an experiment.
5. Prepare the fallback: if the model run fails or is late, the deterministic file with the
   reviewed regulation list is the answer, uploaded by 08:30 at the latest.

**Acceptance.**
- A timed log of the full dry run, with every command, in "Results".
- The frozen configuration in `README.md`, with the commit it refers to.
- Every machine that may run Sunday has the remote, the keys, the corpus and the cache tested.

**Deliverables.** The updated runbook, the dry-run log, and any wiring fix with tests.

**Do not.** Change prompts, features or the decision model after 02:00, unless the dry run shows
the path is broken.

## Results

(fill in)
