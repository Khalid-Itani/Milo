#!/usr/bin/env bash
# Runs the SPEC §6 demo prompts against a running backend. Needs ANTHROPIC_API_KEY in backend/.env.
set -euo pipefail
API=${API:-http://localhost:8000}

chat() {
  echo "> $1"
  curl -sf -XPOST "$API/chat" -H 'content-type: application/json' \
    -d "$(python3 -c 'import json,sys; print(json.dumps({"message": sys.argv[1]}))' "$1")" \
    | python3 -c 'import json,sys; r=json.load(sys.stdin); print("coach:", r["reply"]); [print("  card:", c["type"]) for c in r["cards"]]'
  echo
}

chat "I train 4 days a week and want a 100 kg bench by December. Build me a plan."
chat "Lunch was a chicken burrito bowl with guac"
chat "What should I eat for dinner?"
chat "Set a goal: reach 72 kg by January 31"
chat "Just did bench press 75 kg for 8"

echo "workouts: $(curl -sf "$API/workouts" | python3 -c 'import json,sys; print(len(json.load(sys.stdin)))')"
echo "kcal left: $(curl -sf "$API/today" | python3 -c 'import json,sys; print(json.load(sys.stdin)["kcal"]["left"])')"
