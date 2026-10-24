"""Write the hand-checked region manifest used by the 2.5D parts viewer."""

import json
from pathlib import Path

REGIONS = {
    "caseId": "dev-rear-lamp",
    "image": "/parts3d/dev-rear-lamp/exploded_view.png",
    "coordinateSystem": "normalized image coordinates, origin top-left",
    "extraction": {
        "mode": "vision-llm-stub + human review",
        "automatic": "A vision model identifies each callout-labelled component and returns a polygon.",
        "manual": "These five polygons were hand-checked against the supplied drawing for the spike.",
        "schema": {"id": "string", "name": "string", "polygon": "[[x, y], ...] with x/y in 0..1", "keywords": "string[]"},
    },
    "parts": [
        {"id": "rear-position-lamp", "name": "Rear position lamp", "shortName": "Position lamp", "accent": "#27dac2", "depth": 0, "polygon": [[0.16, 0.22], [0.39, 0.20], [0.40, 0.43], [0.17, 0.46]], "keywords": ["rear position", "position lamp"]},
        {"id": "stop-lamp", "name": "Stop lamp", "shortName": "Stop lamp", "accent": "#ff9d67", "depth": 1, "polygon": [[0.39, 0.22], [0.62, 0.20], [0.63, 0.42], [0.39, 0.43]], "keywords": ["stop lamp", "braking"]},
        {"id": "reversing-lamp", "name": "Reversing lamp", "shortName": "Reversing lamp", "accent": "#a7b8ff", "depth": 2, "polygon": [[0.61, 0.22], [0.84, 0.20], [0.86, 0.42], [0.63, 0.44]], "keywords": ["reversing lamp", "reverse gear"]},
        {"id": "outer-lens", "name": "Outer lens", "shortName": "Outer lens", "accent": "#ffe07a", "depth": 3, "polygon": [[0.13, 0.56], [0.88, 0.55], [0.91, 0.83], [0.12, 0.84]], "keywords": ["outer lens", "lens", "light transmission", "colour"]},
        {"id": "retro-reflector", "name": "Retro-reflector", "shortName": "Retro-reflector", "accent": "#c693ff", "depth": 4, "polygon": [[0.69, 0.29], [0.84, 0.28], [0.86, 0.40], [0.70, 0.42]], "keywords": ["retro-reflector", "retroreflective", "reflective"]},
    ],
}

out = Path(__file__).parents[2] / "frontend/static/parts3d/dev-rear-lamp/regions.json"
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(REGIONS, indent=2) + "\n")
print(out)
