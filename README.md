# WBS＆スケジュール管理Bot (ipp_wbs_agent)

階層型タスク管理・ガントチャート・日記機能を備えたカレンダー＆日記共有AIエージェント。

## 概要
Google ADK (Agent Development Kit) と Gemini 3.8 Flash、および A2UI (Agent-to-UI) v0.8 を活用した実践的AIエージェントアプリケーションです。

- **エージェント名**: `ipp_wbs_agent`
- **表示名**: WBS＆スケジュール管理Bot
- **主要機能**:
  - 週次予定・未完了タスク一覧の動的検索
  - タスク遅延に応じた後続影響・クリティカルパスの自動再計算およびWBSガントチャート再生成
  - A2UI v0.8 リッチカード表示による可視化
  - FastAPI チャットプロキシフロントエンド

## ディレクトリ構成
- `agent.py`: ADK Agent コアロジック、自作関数ツール `get_schedule_and_wbs`、A2UI コールバック
- `a2ui_utils.py`: A2UI v0.8 サーフェス定義・レンダリング補助
- `frontend/main.py`: FastAPI プロキシサーバー
- `frontend/static/index.html`: チャットUI ＆ A2UI レンダラー
- `tests/test_agent.py`: 単体テスト
- `Dockerfile`: Cloud Run 本番デプロイ用コンテナ定義
