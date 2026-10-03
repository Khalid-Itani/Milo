"""Chat loop: history + today context -> Claude with tools -> execute tool_use blocks -> repeat until end_turn."""
import json
import logging
import os

import anthropic
from sqlmodel import Session, select

from agent.prompt import SYSTEM_PROMPT
from agent.tools import TOOLS, execute
from app.models import ChatMessage, Goal, User
from app.today import build_today

log = logging.getLogger("fitcoach.coach")
MAX_ITERATIONS = 6
_client = None


def create_message(**kwargs):
    """Single seam for the API call; tests monkeypatch this."""
    global _client
    _client = _client or anthropic.Anthropic()
    return _client.beta.messages.create(
        model=os.getenv("COACH_MODEL", "claude-opus-5-5"),
        max_tokens=16000,
        output_config={"effort": "low"},  # chat replies are short; raise for better plans
        betas=["server-side-fallback-2026-07-01"],
        fallbacks="default",  # retry on another model if a safety classifier declines
        **kwargs,
    )


def context_block(s: Session) -> str:
    u = s.get(User, 1)
    goals = s.exec(select(Goal).where(Goal.status == "active")).all()
    ctx = {
        "today": build_today(s),
        "profile": u.model_dump(),
        "active_goals": [g.model_dump(mode="json") for g in goals],
    }
    return "Current context (JSON):\n" + json.dumps(ctx, default=str)


def history(s: Session) -> list[dict]:
    rows = s.exec(select(ChatMessage).order_by(ChatMessage.id.desc()).limit(20)).all()[::-1]
    msgs = [{"role": r.role, "content": r.content} for r in rows if r.content]
    while msgs and msgs[0]["role"] != "user":  # API conversations start with a user turn
        msgs.pop(0)
    return msgs


def run(s: Session, message: str) -> dict:
    s.add(ChatMessage(role="user", content=message))
    s.commit()

    messages, cards, reply = history(s), [], ""
    system = SYSTEM_PROMPT + "\n\n" + context_block(s)
    try:
        for _ in range(MAX_ITERATIONS):
            resp = create_message(system=system, tools=TOOLS, messages=messages)
            text = "".join(b.text for b in resp.content if b.type == "text").strip()
            reply = text or reply
            if resp.stop_reason != "tool_use":
                break
            messages.append({"role": "assistant", "content": resp.content})
            results = []
            for b in resp.content:
                if b.type != "tool_use":
                    continue
                try:
                    data, card = execute(s, b.name, b.input)
                    if card:
                        cards.append(card)
                    results.append({"type": "tool_result", "tool_use_id": b.id, "content": json.dumps(data, default=str)})
                except Exception as e:
                    s.rollback()
                    log.warning("tool %s failed: %s", b.name, e)
                    results.append({"type": "tool_result", "tool_use_id": b.id, "content": str(e), "is_error": True})
            messages.append({"role": "user", "content": results})
    except (anthropic.AuthenticationError, TypeError):  # SDK raises TypeError when no credentials are configured
        log.exception("coach auth failed")
        reply = "Coach is offline: set ANTHROPIC_API_KEY in backend/.env."
    except anthropic.APIError as e:
        log.exception("coach call failed")
        reply = f"Coach hit an error ({type(e).__name__}). Try again in a moment."

    reply = reply or ("Done." if cards else "Sorry, I couldn't come up with a reply.")
    s.add(ChatMessage(role="assistant", content=reply, cards=cards))
    s.commit()
    return {"reply": reply, "cards": cards}
