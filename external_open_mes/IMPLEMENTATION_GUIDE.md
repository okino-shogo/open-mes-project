# 生産計画検索画面 (ガントチャート形式) 実装ガイド

## 概要

このガイドでは、新しい生産計画検索画面をReactフロントエンドに統合する手順を説明します。

## 作成されたファイル

1. **設計書**: `DESIGN_ProductionPlanSearch.md`
   - UI設計、技術仕様、実装優先順位の詳細

2. **Reactコンポーネント**: `frontend/src/pages/ProductionPlanSearchGantt.jsx`
   - 生産計画検索画面のメインコンポーネント
   - 検索フィルター、ガントチャート表示、ステータスフィルター/ソート機能を含む

3. **スタイルシート**: `frontend/src/pages/ProductionPlanSearchGantt.css`
   - ガントチャートスタイル、レスポンシブ対応、アクセシビリティ対応

## 実装手順

### Step 1: ルーティング設定

`frontend/src/App.jsx` にルートを追加:

```jsx
// インポート追加
import ProductionPlanSearchGantt from './pages/ProductionPlanSearchGantt.jsx';

// ルート追加 (line 193付近)
<Route path="/production/plan-gantt" element={<ProductionPlanSearchGantt />} />
```

**変更箇所**:
```diff
  import ProductionPlan from './pages/ProductionPlan.jsx';
+ import ProductionPlanSearchGantt from './pages/ProductionPlanSearchGantt.jsx';
  import PartsUsed from './pages/PartsUsed.jsx';

  // ... (中略)

  <Route path="/production/plan" element={<ProductionPlan />} />
+ <Route path="/production/plan-gantt" element={<ProductionPlanSearchGantt />} />
  <Route path="/production/parts-used" element={<PartsUsed />} />
```

### Step 2: メニュー項目追加

`frontend/src/components/SideMenu.jsx` にメニュー項目を追加:

```jsx
// 生産管理セクション内に追加
<Link to="/production/plan-gantt" className="list-group-item list-group-item-action" onClick={onLinkClick}>
  <i className="bi bi-calendar-week me-2"></i>生産計画検索 (ガントチャート)
</Link>
```

**変更箇所** (例):
```diff
  <Link to="/production/plan" className="list-group-item list-group-item-action" onClick={onLinkClick}>
    <i className="bi bi-clipboard-check me-2"></i>生産計画
  </Link>
+ <Link to="/production/plan-gantt" className="list-group-item list-group-item-action" onClick={onLinkClick}>
+   <i className="bi bi-calendar-week me-2"></i>生産計画検索 (ガントチャート)
+ </Link>
  <Link to="/production/parts-used" className="list-group-item list-group-item-action" onClick={onLinkClick}>
    <i className="bi bi-box-seam me-2"></i>使用部品
  </Link>
```

### Step 3: API確認

**使用するAPI**: `/api/production/plans/`

**必要なレスポンスフィールド** (20列対応):
- `qr_code`
- `reception_no`
- `additional_no`
- `customer_name`
- `site_name`
- `additional_content`
- `planned_shipment_date`
- `delivery_date`
- `product_code`
- `process`
- `planned_quantity`
- `slit_scheduled_date`
- `cut_scheduled_date`
- `molder_scheduled_date`
- `vcut_wrapping_scheduled_date`
- `post_processing_scheduled_date`
- `packing_scheduled_date`
- `veneer_scheduled_date`
- `cut_veneer_scheduled_date`
- `status`

**確認方法**:
```bash
# Dockerコンテナ内で実行
docker compose exec -it frontend npm start

# ブラウザで確認
# http://127.0.0.1:3000/production/plan-gantt
```

### Step 4: バックエンド確認

**ProductionPlanモデル** (`backend/src/production/models.py`):
- ✅ 20列のフィールドがすべて定義済み
- ✅ NULL許容フィールドが適切に設定済み

**REST API** (`backend/src/production/rest_views.py`):
- 既存のProductionPlanViewSetが使用可能
- フィルタリングとページネーション機能が実装済み

### Step 5: 動作確認

1. **Dockerコンテナ起動**:
```bash
cd /Users/okinotakumiware/open-mes-project/external_open_mes
docker compose up
```

2. **フロントエンド開発サーバー起動**:
```bash
cd frontend
npm install  # 初回のみ
npm start
```

3. **アクセス**:
- URL: `http://localhost:3000/production/plan-gantt`
- ログイン後にサイドメニューから「生産計画検索 (ガントチャート)」を選択

4. **確認項目**:
- [ ] 検索フィルターが20列対応で表示される
- [ ] 検索実行でデータが取得できる
- [ ] ガントチャート形式で工程スケジュールが表示される
- [ ] ステータスフィルターが動作する
- [ ] ソート機能が動作する
- [ ] ページネーションが動作する
- [ ] レスポンシブ対応 (モバイル/タブレット/デスクトップ)

## トラブルシューティング

### データが表示されない

**症状**: テーブルに「データがありません」と表示される

**原因と対処**:
1. **CSVインポート未実施**:
   - `/data/import` からCSVをアップロード
   - データタイプ: `production_plan`

2. **API エラー**:
   - ブラウザの開発者ツールで Network タブを確認
   - `/api/production/plans/` のレスポンスを確認

3. **認証エラー**:
   - ログインしているか確認
   - トークンが有効か確認

### スタイルが適用されない

**症状**: ガントチャートのスタイルが崩れている

**原因と対処**:
1. **CSSファイル未読み込み**:
   - `ProductionPlanSearchGantt.jsx` の先頭に以下があることを確認:
   ```jsx
   import './ProductionPlanSearchGantt.css';
   ```

2. **Bootstrap競合**:
   - CSS specificity の問題
   - `!important` を使用するか、クラス名を変更

### 工程ステータスが正しく表示されない

**症状**: すべて「未着手」と表示される

**原因と対処**:
1. **日付データがない**:
   - `slit_scheduled_date` などのフィールドがNULLの場合は正常動作
   - CSVデータに日付が含まれているか確認

2. **ステータス算出ロジック**:
   - `calculateProcessStatuses` 関数を確認
   - 実際の完了日時フィールドがモデルに追加されていない場合、予定日での簡易判定になっている

## 次のステップ

### Phase 1完了後の拡張機能

1. **CSVエクスポート機能**:
```jsx
const handleCsvExport = () => {
  const csv = convertToCSV(filteredPlans);
  downloadCSV(csv, 'production_plan_export.csv');
};
```

2. **工程完了日時フィールド追加**:
- `backend/src/production/models.py` に以下を追加:
```python
slit_start_time = models.DateTimeField(null=True, blank=True)
slit_completion_time = models.DateTimeField(null=True, blank=True)
# ... 他の工程も同様
```

3. **仮想スクロール実装** (大量データ対応):
```bash
npm install react-window
```

4. **リアルタイム更新** (WebSocket):
```bash
npm install socket.io-client
```

## 参考資料

### 関連ファイル
- 既存UI: `/Users/okinotakumiware/open-mes-project/open_mes/scr/templates/production/gantt_chart.html`
- モデル: `backend/src/production/models.py`
- API: `backend/src/production/rest_views.py`

### 技術ドキュメント
- React: https://react.dev/
- Bootstrap 5: https://getbootstrap.com/docs/5.3/
- Django REST Framework: https://www.django-rest-framework.org/

### デザイン参考
- DESIGN_ProductionPlanSearch.md (詳細設計書)
- gantt_chart.html (既存テンプレート)
- daily_gantt_fallback.html (軽量版参考)

## まとめ

以下の手順で実装が完了します:

1. ✅ ファイル作成 (ProductionPlanSearchGantt.jsx, .css)
2. ⏳ App.jsx にルート追加
3. ⏳ SideMenu.jsx にメニュー項目追加
4. ⏳ 動作確認
5. ⏳ フィードバック対応

実装完了後、Phase 2以降の拡張機能を段階的に追加していくことを推奨します。
