# Open MES - Manufacturing Execution System

オープンソースの製造実行システム（MES）です。Django REST FrameworkとBootstrap 5を使用して構築されています。

## 主な機能

### 🏭 生産管理
- 生産計画の作成・管理
- ガントチャートによる進捗視覚化
- 作業者インターフェース（リアルタイム工程管理）
- 🤖 AI作業者分析（パフォーマンス分析・最適化提案）
- 生産性分析ダッシュボード

### 📦 在庫管理
- 在庫照会・入出庫履歴
- 部品・材料の引当管理
- 出庫予定・入庫処理

### ✅ 品質管理
- 工程内検査・受入検査
- 改善提案（Kaizen）システム

### 📱 モバイル対応
- スマートフォン・タブレット用インターフェース
- QRコード読み取り機能

### 🔧 設備管理
- 始業点検・点検履歴管理

## 技術スタック

- **Backend**: Django 5.1.7, Django REST Framework
- **Frontend**: Bootstrap 5, JavaScript (ES6+)
- **Database**: PostgreSQL (開発), SQLite (Vercel)
- **AI分析**: Python統計ライブラリ
- **デプロイ**: Vercel, Docker

## ライブデモ

🌐 **[Vercel でライブデモを見る](https://your-app-url.vercel.app)**

## ローカル開発

### Dockerを使用した開発

```bash
# リポジトリをクローン
git clone https://github.com/your-username/open-mes.git
cd open-mes

# Docker Composeで起動
docker compose up -d

# ブラウザでアクセス
http://localhost:8000
```

### 手動セットアップ

```bash
# 仮想環境作成
python -m venv venv
source venv/bin/activate  # Windows: venv\\Scripts\\activate

# 依存関係インストール
pip install -r requirements.txt

# データベース設定
cd scr
python manage.py migrate
python manage.py createsuperuser

# 開発サーバー起動
python manage.py runserver
```

## 主要な画面

### 1. 作業者インターフェース
工程別の作業開始・終了ボタンで、リアルタイムに作業進捗を管理

### 2. AI作業者分析ダッシュボード
- 個人パフォーマンス分析
- スキルマトリックス表示
- 改善提案の自動生成
- 学習進捗の可視化

### 3. 生産計画管理
- ガントチャートによる視覚的な計画管理
- 工程別予定日・実績管理

### 4. 在庫管理
- リアルタイム在庫状況
- 入出庫履歴の追跡

## API仕様

REST APIが利用可能です:

- `GET /api/production/plans/` - 生産計画一覧
- `POST /api/production/plans/update-process-status/` - 工程状態更新
- `GET /api/production/ai-optimization/{worker_id}/worker_analysis/` - AI作業者分析
- `GET /api/inventory/inventory/` - 在庫情報

詳細は `/api/` エンドポイントでAPIドキュメントを確認してください。

## ライセンス

MIT License

## 貢献

プルリクエストやIssueでの貢献を歓迎します！

## 作者

Created with ❤️ for manufacturing efficiency