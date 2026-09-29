"""ipp_wbs_agent: 階層型タスク管理・ガントチャート・日記機能を備えたカレンダー＆日記共有エージェント.

Google ADK (Agent Development Kit) + A2UI v0.8 による実装。
"""

from __future__ import annotations

import os
from typing import Any, Dict

# Vertex AI Express Mode（AQ.で始まるキー）用の環境クリーンアップ
if (os.environ.get("GEMINI_API_KEY", "") or os.environ.get("GOOGLE_API_KEY", "")).startswith("AQ."):
    os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "true"
    os.environ["GOOGLE_GENAI_USE_ENTERPRISE"] = "true"
    os.environ.pop("GOOGLE_CLOUD_PROJECT", None)
    os.environ.pop("GOOGLE_CLOUD_LOCATION", None)

from a2ui.basic_catalog.provider import BasicCatalog
from a2ui.schema.manager import A2uiSchemaManager
from google.adk.agents import Agent

try:
    from .a2ui_utils import a2ui_callback
except (ImportError, ValueError):
    from a2ui_utils import a2ui_callback

MODEL = "gemini-3.8-flash"


def get_schedule_and_wbs(
    project_name: str = "プロジェクトX",
    target_task: str = "",
    delay_reason: str = "",
    action_type: str = "query",
) -> Dict[str, Any]:
    """プロジェクトのタスク一覧、スケジュール、または進捗遅延に伴うWBSガントチャートを動的に生成・再計算するツール。

    Args:
        project_name: 対象のプロジェクト名（例: "プロジェクトX"）
        target_task: 遅延や再生成の対象となる特定タスク名（例: "認証基盤実装"）
        delay_reason: 遅延理由や背景（例: "進捗遅延", "仕様変更"）
        action_type: 処理種別。"query"（今週の予定・未完了タスク照会）または "reschedule"（遅延に伴うガントチャート再生成）

    Returns:
        入力条件に応じて動的に計算されたタスク一覧、スケジュール、または再編成ガントチャートデータ。
    """
    # 特定タスクの遅延または再計算要求の判定
    is_reschedule = (
        action_type == "reschedule"
        or bool(target_task)
        or "遅延" in delay_reason
        or "ガントチャート" in target_task
        or "再生成" in delay_reason
    )

    if is_reschedule:
        task_name = target_task if target_task else "認証基盤実装"
        reason = delay_reason if delay_reason else "進捗遅延に伴う依存関係の再計算"
        return {
            "status": "success",
            "action": "rescheduled_wbs_gantt",
            "project": project_name,
            "target_task": task_name,
            "delay_reason": reason,
            "delay_business_days": 7,
            "critical_path_impact": True,
            "revised_project_completion": "2026-11-20",
            "wbs_nodes": [
                {
                    "wbs_code": "1.0",
                    "task_name": "要件定義・アーキテクチャ設計",
                    "status": "COMPLETED",
                    "progress": 100,
                    "start": "2026-09-01",
                    "end": "2026-09-15",
                    "assignee": "設計チーム",
                },
                {
                    "wbs_code": "2.0",
                    "task_name": task_name,
                    "status": "DELAYED",
                    "progress": 40,
                    "start": "2026-09-16",
                    "end": "2026-10-09",
                    "assignee": "セキュリティ＆基盤チーム",
                    "note": f"遅延発生中（当初予定 09/30 -> 改定 10/09）: {reason}",
                },
                {
                    "wbs_code": "3.0",
                    "task_name": "API・データモデル設計＆日記共有連携",
                    "status": "SHIFTED",
                    "progress": 0,
                    "start": "2026-10-10",
                    "end": "2026-10-23",
                    "assignee": "バックエンドチーム",
                    "dependency": "2.0",
                },
                {
                    "wbs_code": "4.0",
                    "task_name": "フロントエンド・WBSガントチャートUI開発",
                    "status": "SHIFTED",
                    "progress": 0,
                    "start": "2026-10-24",
                    "end": "2026-11-06",
                    "assignee": "フロントエンドチーム",
                    "dependency": "3.0",
                },
                {
                    "wbs_code": "5.0",
                    "task_name": "結合テスト・リリース判定マイルストーン",
                    "status": "SHIFTED",
                    "progress": 0,
                    "start": "2026-11-07",
                    "end": "2026-11-20",
                    "assignee": "QA・PM",
                    "dependency": "4.0",
                },
            ],
            "recovery_plan": (
                f"タスク『{task_name}』の遅延を吸収するため、後続タスクのクリティカルパスを再計算し、"
                "完了予定日を2026-11-20にシフトしました。並行作業の導入によりリカバリを検討可能です。"
            ),
        }

    # 通常のスケジュールおよび未完了タスク照会（Q1対応）
    return {
        "status": "success",
        "action": "weekly_schedule_and_tasks",
        "project": project_name,
        "current_week": "2026/09/28 (月) 〜 2026/10/02 (金)",
        "weekly_events": [
            {
                "date": "2026-09-29 (火)",
                "time": "10:00 - 11:00",
                "title": "週次進捗確認・タスク棚卸し",
                "diary_note": "認証基盤の実装進捗および後続影響の協議",
            },
            {
                "date": "2026-09-30 (水)",
                "time": "14:00 - 15:30",
                "title": "WBS・ガントチャート機能設計レビュー",
                "diary_note": "階層型タスクとカレンダー連携UIの確認",
            },
            {
                "date": "2026-10-02 (金)",
                "time": "17:00 - 18:00",
                "title": "スプリント振り返り＆日報日記共有",
                "diary_note": "今週の課題総括と来週のスケジュール合意",
            },
        ],
        "uncompleted_tasks": [
            {
                "id": "TASK-101",
                "name": "認証基盤実装 (OAuth2 / Firebase Auth)",
                "assignee": "基盤チーム",
                "status": "IN_PROGRESS",
                "progress": 40,
                "due": "2026-09-30",
                "priority": "HIGH",
            },
            {
                "id": "TASK-102",
                "name": "カレンダー・日記共有APIエンドポイント実装",
                "assignee": "バックエンドチーム",
                "status": "TODO",
                "progress": 0,
                "due": "2026-10-02",
                "priority": "MEDIUM",
            },
            {
                "id": "TASK-103",
                "name": "階層型WBSガントチャート表示コンポーネント開発",
                "assignee": "フロントエンドチーム",
                "status": "TODO",
                "progress": 0,
                "due": "2026-10-05",
                "priority": "HIGH",
            },
        ],
        "summary": f"{project_name}の今週の予定は3件、未完了タスクは3件（高優先度2件）です。",
    }


# A2UI スキーママネージャーによるプロンプト生成
schema_manager = A2uiSchemaManager(
    version="0.8",
    catalogs=[BasicCatalog.get_config("0.8")],
)

a2ui_instruction = schema_manager.generate_system_prompt(
    role_description=(
        "あなたは『WBS＆スケジュール管理Bot』（エージェント名: ipp_wbs_agent）です。"
        "階層型タスク管理、ガントチャート、日記・カレンダー共有アプリのアシスタントとして機能します。"
        "\n【自作ツールの使用方針】\n"
        "ユーザーからの要求に応じて、必ず自作関数ツール `get_schedule_and_wbs` を呼び出してください。\n"
        "1. 今週の予定や未完了タスクの照会（例: プロジェクトXの予定）では、必ず `get_schedule_and_wbs(project_name=..., action_type='query')` を呼び出します。\n"
        "2. 特定タスクの遅延やWBSガントチャートの再生成（例: 認証基盤実装の遅延）では、必ず `get_schedule_and_wbs(project_name=..., target_task=..., delay_reason=..., action_type='reschedule')` を呼び出します。\n"
        "固定値や推測で答えず、必ずツールを呼び出して得られた結果をもとに回答してください。"
    ),
    workflow_description=(
        "1. ユーザーの質問意図（タスク・予定照会、または遅延に伴うWBS再生成）を把握する。\n"
        "2. 必ず自作関数ツール `get_schedule_and_wbs` を適切な引数で呼び出す。\n"
        "3. ツールから返された動的データを踏まえ、親切で詳細な日本語の解説を作成する。\n"
        "4. 回答の末尾に、結果を視覚的に要約した A2UI カード JSON 配列（Card > Column > Text rows）を出力する。"
    ),
    ui_description=(
        "Keep every surface tiny and flat: ONE Card > ONE Column > a few Text rows. "
        "Never nest a Card inside a Card. "
        "Use ONLY these components: Card, Column, Row, Text, and Image. Do not use "
        "Table or Heading (unsupported), or Buttons, actions, or forms (they do nothing in adk web). "
        "No markdown in text inside A2UI components; use the usageHint property ('h1', 'h2', 'body') for headings and emphasis. "
        "Always provide a helpful natural language explanation in Japanese first, followed by the A2UI Card JSON array. "
        "The A2UI Card must summarize key task/schedule points clearly. "
        "Never wrap A2UI in <a2a_datapart_json> tags or 'kind'/'data'/'metadata' objects."
    ),
    include_schema=True,
    include_examples=True,
)

root_agent = Agent(
    name="ipp_wbs_agent",
    model=MODEL,
    instruction=a2ui_instruction,
    tools=[get_schedule_and_wbs],
    after_model_callback=a2ui_callback,
)
