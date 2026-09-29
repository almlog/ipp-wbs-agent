"""FastAPI proxy server for ipp_wbs_agent frontend.

Serves the chat web UI and executes the agent directly in-process or over A2A.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import re
import sys
from pathlib import Path
from typing import Any, Dict, List

from dotenv import load_dotenv
load_dotenv()

# Ensure agent directory is in sys.path
agent_root = Path(__file__).resolve().parent.parent
if str(agent_root) not in sys.path:
    sys.path.insert(0, str(agent_root))

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from agent import root_agent
from google.adk.runners import InMemoryRunner
from google.genai import types

logger = logging.getLogger("ipp_wbs_agent.frontend")
if not logger.handlers:
    logging.basicConfig(level=logging.INFO)

app = FastAPI(title="WBS＆スケジュール管理Bot")

# In-memory sessions: user_id -> session_id
_runner: InMemoryRunner | None = None
_sessions: Dict[str, str] = {}
_session_locks: Dict[str, asyncio.Lock] = {}

_TAG_RE = re.compile(r"<a2ui-json>([\s\S]*?)</a2ui-json>", re.IGNORECASE)


def get_runner() -> InMemoryRunner:
    global _runner
    if _runner is None:
        _runner = InMemoryRunner(agent=root_agent, app_name="ipp_wbs_agent")
    return _runner


def get_user_lock(user_id: str) -> asyncio.Lock:
    if user_id not in _session_locks:
        _session_locks[user_id] = asyncio.Lock()
    return _session_locks[user_id]


def _parse_event_text(text: str) -> List[Dict[str, Any]]:
    """Parse text output, separating prose and structured A2UI JSON components."""
    parts: List[Dict[str, Any]] = []
    matches = list(_TAG_RE.finditer(text))
    if matches:
        prose = _TAG_RE.sub("", text).strip()
        if prose:
            parts.append({"kind": "text", "text": prose})
        for match in matches:
            raw_json = match.group(1).strip()
            try:
                data = json.loads(raw_json)
                if isinstance(data, list):
                    for item in data:
                        parts.append({"kind": "a2ui", "data": item})
                elif isinstance(data, dict):
                    parts.append({"kind": "a2ui", "data": data})
            except Exception:
                parts.append({"kind": "text", "text": raw_json})
    else:
        if text.strip():
            parts.append({"kind": "text", "text": text.strip()})
    return parts


@app.get("/health")
async def health():
    return {"status": "ok", "agent": "ipp_wbs_agent"}


@app.post("/chat")
async def chat(req: Request):
    try:
        body = await req.json()
    except Exception:
        body = {}

    message = body.get("message", "").strip()
    user_id = body.get("user_id") or "web-user"

    if not message:
        return JSONResponse({"parts": [{"kind": "text", "text": "メッセージを入力してください。"}]})

    runner = get_runner()
    lock = get_user_lock(user_id)

    async with lock:
        session_id = _sessions.get(user_id)
        if not session_id:
            session = await runner.session_service.create_session(
                app_name="ipp_wbs_agent", user_id=user_id
            )
            session_id = session.id
            _sessions[user_id] = session_id

        content = types.Content(
            role="user",
            parts=[types.Part.from_text(text=message)],
        )

        parts: List[Dict[str, Any]] = []
        async for event in runner.run_async(
            user_id=user_id,
            session_id=session_id,
            new_message=content,
        ):
            if event.author == "user":
                continue
            event_content = getattr(event, "content", None)
            if not event_content:
                continue

            for part in getattr(event_content, "parts", []) or []:
                txt = getattr(part, "text", None)
                if txt:
                    parts.extend(_parse_event_text(txt))

        if not parts:
            parts = [{"kind": "text", "text": "(応答が生成されませんでした。)"}]

        return JSONResponse({"parts": parts})


# Mount static assets
static_dir = Path(__file__).resolve().parent / "static"
app.mount("/", StaticFiles(directory=str(static_dir), html=True), name="static")


if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
