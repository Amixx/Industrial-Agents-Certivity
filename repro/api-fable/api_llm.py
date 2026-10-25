"""Route claude_cli.complete_json through the Anthropic API (brain.llm._anthropic) with a fixed model.
    python api_llm.py <model> <effort> <script.py> [args...]"""
import json, runpy, sys
from brain import llm, claude_cli
llm.PRICES['claude-fable-5-1'] = (10.00, 50.00, 0.25)
MODEL, EFFORT, script = sys.argv[1], sys.argv[2], sys.argv[3]
def closed(schema):
    # The API's structured output needs additionalProperties: false on every object.
    if isinstance(schema, dict):
        schema = {k: closed(v) for k, v in schema.items()}
        if schema.get('type') == 'object':
            schema.setdefault('additionalProperties', False)
    elif isinstance(schema, list):
        schema = [closed(v) for v in schema]
    return schema
def complete_json(system, prompt, schema, model=None, effort=None, on_usage=None):
    return llm._anthropic(MODEL, system, prompt, closed(schema), effort or EFFORT, 32000)
claude_cli.complete_json = complete_json
sys.argv = [script, *sys.argv[4:]]
try:
    runpy.run_path(script, run_name='__main__')
finally:
    print('api usage', json.dumps(llm.usage()), file=sys.stderr)
