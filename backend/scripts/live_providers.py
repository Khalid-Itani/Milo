"""Opt-in paid/provider smoke checks, separate from offline tests; never print session tokens."""
import argparse
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.config import settings
from app.visualize import mint_session
from agent.coach import create_message
from agent.tools import TOOLS

parser = argparse.ArgumentParser()
parser.add_argument("provider", choices=["claude", "visualize"])
args = parser.parse_args()
try:
    if args.provider == "claude":
        if not settings.anthropic_api_key:
            raise SystemExit("NOT RUN: ANTHROPIC_API_KEY is missing.")
        tools = [t for t in TOOLS if t["name"] == "get_today"]
        messages = [{"role": "user", "content": "Call get_today once for this synthetic connection check."}]
        response = create_message(max_tokens=256, messages=messages, tools=tools,
                                  tool_choice={"type": "tool", "name": "get_today"})
        uses = [b for b in response.content if b.type == "tool_use"]
        assert response.stop_reason == "tool_use" and len(uses) == 1
        assert uses[0].name == "get_today" and uses[0].input == {}
        messages += [{"role": "assistant", "content": [b.model_dump(mode="json", exclude_none=True)
                                                       for b in response.content]},
                     {"role": "user", "content": [{"type": "tool_result", "tool_use_id": uses[0].id,
                         "content": '{"data":{"status":"synthetic_connection_check","kcal":{"eaten":0}}}'}]}]
        final = create_message(max_tokens=256, messages=messages, tools=tools,
                               tool_choice={"type": "none"})
        assert final.stop_reason == "end_turn" and any(b.type == "text" and b.text for b in final.content)
        print("PASS: live configured Claude model accepted the app tool schema, forced call and tool result.")
        print("Two bounded paid Messages calls; synthetic tool data only; no application writes.")
    else:
        if not settings.visualize_secret_key:
            raise SystemExit("NOT RUN: VISUALIZE_SECRET_KEY is missing.")
        result = mint_session()
        print("PASS: fresh Visualize session token validated; token withheld. No physical scan was tested.")
except SystemExit:
    raise
except Exception:
    raise SystemExit("Provider check failed; upstream contents and secrets are withheld.") from None
