List the requirements from UN Regulations that the product described in spec.md (exploded view: exploded_view.png) must meet for type approval, as a regulatory expert would.

The regulations are in regulations/. INDEX.md lists them; each .txt file is one regulation's base version, one paragraph per line, prefixed with its PDF page and paragraph label.

Write one engineering obligation per requirement, stated so that it stands alone (its scope, condition and constraint), and cite the paragraph it comes from. Recall counts four times as much as precision.

Write the result as JSON to submission.json. If it gets long, write several files named submission-<part>.json instead; they are merged. Format:
{"team_id": "team-06", "case_id": "dev-rear-lamp", "requirements": [{"id": "R-001", "text": "The rear lamp shall ...", "source": {"regulation": "UN R48", "version": "9.3.0", "page": 6, "paragraph": "6.2"}}]}
