# The 0.724 upload, rebuildable

`zsh repro/run.sh` rebuilds `rear-lamp-kb-section-cut2-mark-verbatim.json` (platform 156 / 0.724, uploaded 25 Oct 01:10) row for row from cached answers, and stops on any live LLM or Jev call.

- Code: this branch is `kb-stack` at `1d8b22e` plus the uncommitted harness of the `-select` worktree (claude -p routing, rewrite prompt) as it stood on 25 Oct 01:28.
- Chain: pipeline with Jev at relative cut 0.20 and the requirement filter off, recording p_keep (`j20f-all.json`, 448 rows) → `section_stage.py`: p_keep × √p_section ≥ 0.3535 plus the pointer, umbrella and approval-mark rules (317 rows) → `verbatim.py --all`: each row's text replaced by its quote where the quote is that row's alone.
- Inputs kept here: `llm-cache.tgz` (claude -p and Jev answers), `kb.sqlite.gz`, `p_section.json` (one Opus call per section), the intermediate files and the uploaded file.
- Needs `brain/data/corpus` linked to a checkout's corpus.
