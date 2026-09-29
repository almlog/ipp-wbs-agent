"""Unit tests for ipp_wbs_agent and its A2UI callback."""

import sys
from pathlib import Path
from unittest.mock import MagicMock

# Ensure agent directory is in sys.path
agent_dir = Path(__file__).resolve().parent.parent
if str(agent_dir) not in sys.path:
    sys.path.insert(0, str(agent_dir))

from agent import root_agent, get_schedule_and_wbs
from a2ui_utils import a2ui_callback
from google.adk.models.llm_response import LlmResponse
from google.genai import types


def test_root_agent_configuration():
    """Verify that root_agent is properly configured with ADK, tools, and callback."""
    assert root_agent is not None
    assert root_agent.name == "ipp_wbs_agent"
    tool_names = [getattr(t, "__name__", getattr(t, "name", "")) for t in root_agent.tools]
    assert "get_schedule_and_wbs" in tool_names
    assert root_agent.after_model_callback == a2ui_callback


def test_tool_weekly_schedule_query():
    """Verify that get_schedule_and_wbs correctly returns weekly schedule and uncompleted tasks."""
    result = get_schedule_and_wbs(project_name="プロジェクトX", action_type="query")
    assert result["status"] == "success"
    assert result["action"] == "weekly_schedule_and_tasks"
    assert result["project"] == "プロジェクトX"
    assert "weekly_events" in result
    assert len(result["weekly_events"]) >= 3
    assert "uncompleted_tasks" in result
    assert len(result["uncompleted_tasks"]) >= 3
    assert any(t["priority"] == "HIGH" for t in result["uncompleted_tasks"])


def test_tool_reschedule_delayed_task():
    """Verify that get_schedule_and_wbs dynamically recalculates WBS Gantt chart on task delay."""
    result = get_schedule_and_wbs(
        project_name="プロジェクトX",
        target_task="認証基盤実装",
        delay_reason="進捗遅延",
        action_type="reschedule",
    )
    assert result["status"] == "success"
    assert result["action"] == "rescheduled_wbs_gantt"
    assert result["target_task"] == "認証基盤実装"
    assert result["delay_business_days"] > 0
    assert result["critical_path_impact"] is True
    assert "revised_project_completion" in result
    assert "wbs_nodes" in result
    
    # Check that target task is marked as DELAYED and subsequent tasks are SHIFTED
    delayed_node = next((n for n in result["wbs_nodes"] if n["task_name"] == "認証基盤実装"), None)
    assert delayed_node is not None
    assert delayed_node["status"] == "DELAYED"
    
    shifted_nodes = [n for n in result["wbs_nodes"] if n["status"] == "SHIFTED"]
    assert len(shifted_nodes) >= 2


def test_tool_returns_differ_for_different_inputs():
    """Verify that tool outputs dynamically change based on input arguments (not a stub)."""
    res1 = get_schedule_and_wbs(project_name="プロジェクトX", action_type="query")
    res2 = get_schedule_and_wbs(
        project_name="プロジェクトX",
        target_task="認証基盤実装",
        delay_reason="進捗遅延",
        action_type="reschedule",
    )
    assert res1["action"] != res2["action"]
    assert res1 != res2


def test_a2ui_callback_processes_a2ui_surface():
    """Verify that a2ui_callback correctly extracts and formats A2UI JSON payload."""
    mock_context = MagicMock()
    a2ui_text = (
        "プロジェクトの進捗をお知らせします。\n\n"
        '[\n'
        '  {"beginRendering": {"surfaceId": "default", "root": "card1"}},\n'
        '  {"surfaceUpdate": {\n'
        '     "surfaceId": "default",\n'
        '     "components": [\n'
        '       {"id": "card1", "component": {"Card": {"child": "col1"}}},\n'
        '       {"id": "col1", "component": {"Column": {"children": {"explicitList": ["t1", "t2"]}}}},\n'
        '       {"id": "t1", "component": {"Text": {"text": {"literalString": "WBS進捗サマリー"}, "usageHint": "h1"}}},\n'
        '       {"id": "t2", "component": {"Text": {"text": {"literalString": "認証基盤実装が進行中"}, "usageHint": "body"}}}\n'
        '     ]\n'
        '  }}\n'
        ']'
    )
    response = LlmResponse(
        content=types.Content(role="model", parts=[types.Part(text=a2ui_text)])
    )
    callback_result = a2ui_callback(mock_context, response)
    assert callback_result is not None
    assert callback_result.content is not None
    part_text = callback_result.content.parts[0].text
    assert "<a2ui-json>" in part_text
    assert "WBS進捗サマリー" in part_text


def test_a2ui_callback_ignores_prose():
    """Verify that a2ui_callback returns None when response contains only plain text."""
    mock_context = MagicMock()
    response = LlmResponse(
        content=types.Content(
            role="model", parts=[types.Part(text="こんにちは！何か質問はありますか？")]
        )
    )
    result = a2ui_callback(mock_context, response)
    assert result is None
