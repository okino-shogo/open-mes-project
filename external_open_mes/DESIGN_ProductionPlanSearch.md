# 生産計画検索画面 設計書

## 概要

既存の生産計画検索機能に、ガントチャートスタイルの工程スケジュール表示を統合した新しいUI設計。
ユーザーが提供したスクリーンショットに基づき、`open_mes/production/gantt_chart.html`のUIパターンを参考に設計。

## 設計目標

1. **検索機能の強化**: 20列のフィールドに対応した詳細な検索条件
2. **視覚的な工程管理**: ガントチャート形式で工程スケジュールを一覧表示
3. **リアルタイム進捗**: 各工程のステータス（未着手/着手中/完了/遅延）を色分け表示
4. **レスポンシブ対応**: 大量データでもスムーズに動作する軽量設計

## UI構成

### 1. 検索フィルターセクション

```
┌─────────────────────────────────────────────────────────────────┐
│ 生産計画検索                                                      │
├─────────────────────────────────────────────────────────────────┤
│ [検索条件]                                                        │
│ ┌─────────┬─────────┬─────────┬─────────┬─────────┬─────────┐ │
│ │QRコード │受付No   │追加No   │得意先名 │現場名   │工程     │ │
│ └─────────┴─────────┴─────────┴─────────┴─────────┴─────────┘ │
│ ┌─────────┬─────────┬─────────┬─────────┬─────────┬─────────┐ │
│ │品名     │数量     │製造予定 │出荷予定 │納品日   │ステータス││
│ └─────────┴─────────┴─────────┴─────────┴─────────┴─────────┘ │
│ ┌─────────┬─────────┬─────────────────────────────┐           │
│ │工程予定日範囲 (開始): [____] ～ (終了): [____]   │           │
│ └─────────┴─────────┴─────────────────────────────┘           │
│ [検索] [クリア] [CSV出力]                                       │
└─────────────────────────────────────────────────────────────────┘
```

**フィールド一覧** (ProductionPlanモデルの20列対応):
1. QRコード
2. 受付No
3. 追加No
4. 得意先名
5. 現場名
6. 追加内容
7. 製造予定日
8. 出荷予定日
9. 品名 (product_code)
10. 工程
11. 数量
12. スリット予定日
13. カット予定日
14. モルダー予定日
15. Vカットラッピング予定日
16. 後加工予定日
17. 梱包予定日
18. 納品日
19. 化粧板貼予定日
20. カット化粧板予定日

### 2. 工程スケジュール表示 (ガントチャート形式)

```
┌──────────────────────────────────────────────────────────────────────────────┐
│ 受付No│連番│工程│現場名      │追加内容│品名│数量│納期目標│スリット│カット│… │
├──────────────────────────────────────────────────────────────────────────────┤
│ 24112 │ 15 │ラ │東京日商E…  │-16~19…│受桟│49 │ 5/19  │ ✓完了 │ 着手中│   │
│       │    │    │            │       │(ラ)│   │       │ 5/14  │ 5/19 │   │
│       │    │    │            │       │    │   │       │ 9:00  │ 10:00│   │
├──────────────────────────────────────────────────────────────────────────────┤
│ 25559 │200 │V   │西東京市…   │-7取り…│AW  │ 3 │ 6/27  │ ✓完了 │ ✓完了 │   │
│       │    │    │            │       │(V) │   │       │ 6/26  │ 6/26 │   │
└──────────────────────────────────────────────────────────────────────────────┘
```

**工程列** (左から右へ):
1. スリット予定日
2. カット予定日
3. モルダー予定日
4. Vカットラッピング予定日
5. 後加工予定日
6. 梱包予定日
7. 化粧板貼予定日
8. カット化粧板予定日

**ステータス色分け**:
- 🟢 完了: `#d4edda` (緑背景)
- 🟡 着手中: `#fff3cd` (黄背景)
- ⚪ 未着手: `#f8f9fa` (灰背景)
- 🔴 遅延: `#f8d7da` (赤背景)

### 3. フィルター・ソート機能

```
┌─────────────────────────────────────────────────────────────────┐
│ [ステータスフィルター]                                            │
│ [完了のみ] [着手中のみ] [未着手のみ] [遅延のみ] [すべて表示]    │
│                                                                  │
│ [並び替え]                                                       │
│ [納期順] [受注番号順] [進捗順] [緊急度順]                        │
└─────────────────────────────────────────────────────────────────┘
```

## 技術仕様

### コンポーネント構成

```
ProductionPlanSearch/
├── ProductionPlanSearch.jsx          // メインコンポーネント
├── components/
│   ├── SearchFilters.jsx             // 検索フィルター
│   ├── GanttScheduleTable.jsx        // 工程スケジュール表
│   ├── ProcessCell.jsx               // 工程セル (ステータス表示)
│   └── StatusFilters.jsx             // ステータスフィルター/ソート
└── styles/
    └── ProductionPlanSearch.css      // スタイルシート
```

### API エンドポイント

**既存API**: `/api/production/plans/`

**レスポンス例**:
```json
{
  "count": 106,
  "next": "http://...",
  "previous": null,
  "results": [
    {
      "id": "uuid",
      "qr_code": "241120150",
      "reception_no": "24112",
      "additional_no": "15",
      "customer_name": "(株)長谷工ファニシング",
      "site_name": "東京日商E八王子市東浅川町",
      "additional_content": "-16~19芯材加工用",
      "planned_shipment_date": "2025-05-19",
      "delivery_date": "2025-08-03",
      "product_code": "受桟 (ラ)",
      "process": "ラッピング",
      "planned_quantity": 49,
      "slit_scheduled_date": null,
      "cut_scheduled_date": "2025-05-14",
      "molder_scheduled_date": "2025-05-19",
      "vcut_wrapping_scheduled_date": null,
      "post_processing_scheduled_date": null,
      "packing_scheduled_date": null,
      "veneer_scheduled_date": null,
      "cut_veneer_scheduled_date": null,
      "status": "IN_PROGRESS",
      "created_at": "2025-01-07T10:00:00Z",
      "updated_at": "2025-01-07T10:00:00Z"
    }
  ]
}
```

### 状態管理

```javascript
const [searchFilters, setSearchFilters] = useState({
  qr_code: '',
  reception_no: '',
  additional_no: '',
  customer_name: '',
  site_name: '',
  additional_content: '',
  product_code: '',
  process: '',
  planned_quantity: '',
  planned_shipment_date_from: '',
  planned_shipment_date_to: '',
  delivery_date_from: '',
  delivery_date_to: '',
  slit_scheduled_date_from: '',
  slit_scheduled_date_to: '',
  cut_scheduled_date_from: '',
  cut_scheduled_date_to: '',
  molder_scheduled_date_from: '',
  molder_scheduled_date_to: '',
  vcut_wrapping_scheduled_date_from: '',
  vcut_wrapping_scheduled_date_to: '',
  post_processing_scheduled_date_from: '',
  post_processing_scheduled_date_to: '',
  packing_scheduled_date_from: '',
  packing_scheduled_date_to: '',
  veneer_scheduled_date_from: '',
  veneer_scheduled_date_to: '',
  cut_veneer_scheduled_date_from: '',
  cut_veneer_scheduled_date_to: '',
  status: ''
});

const [statusFilter, setStatusFilter] = useState('all');
const [sortBy, setSortBy] = useState('delivery');
const [plans, setPlans] = useState([]);
const [loading, setLoading] = useState(false);
const [pagination, setPagination] = useState({
  count: 0,
  next: null,
  previous: null
});
```

## スタイルガイド

### カラーパレット

```css
:root {
  /* ステータス色 */
  --status-completed: #d4edda;
  --status-inprogress: #fff3cd;
  --status-notstarted: #f8f9fa;
  --status-delayed: #f8d7da;
  --status-onhold: #e2e3e5;

  /* 工程別アクセントカラー */
  --process-slit: #e3f2fd;
  --process-cut: #f3e5f5;
  --process-molder: #e8f5e8;
  --process-vcut: #fce4ec;
  --process-post: #f3e5f5;
  --process-packing: #e0f2f1;
  --process-veneer: #fff8e1;
  --process-cut-veneer: #ffebee;

  /* UI要素 */
  --grid-color: #e3e6ea;
  --grid-dark: #cfd3d8;
  --header-bg: linear-gradient(135deg, #2c3e50, #34495e);
  --row-height: 80px;
  --cell-padding: 0.5rem;
}
```

### レスポンシブブレークポイント

```css
/* モバイル: < 768px */
@media (max-width: 768px) {
  .table thead th { font-size: 0.7rem; }
  .process-cell { min-height: 60px; padding: 0.2rem; }
}

/* タブレット: 768px ~ 1200px */
@media (max-width: 1200px) {
  .table-responsive { font-size: 0.75rem; }
  .process-cell { min-height: 70px; }
}

/* デスクトップ: >= 1200px */
@media (min-width: 1200px) {
  .table-responsive { font-size: 0.85rem; }
  .process-cell { min-height: 80px; }
}
```

## 実装の優先順位

### Phase 1: 基本機能 (Week 1)
1. ✅ 検索フィルターUI実装
2. ✅ API統合とデータ取得
3. ✅ 基本テーブル表示
4. ✅ ページネーション

### Phase 2: ガントチャート表示 (Week 2)
1. ⏳ 工程スケジュール列の追加
2. ⏳ ステータス色分け実装
3. ⏳ 工程セルコンポーネント
4. ⏳ プログレスバー表示

### Phase 3: フィルター・ソート機能 (Week 3)
1. ⏳ ステータスフィルター実装
2. ⏳ ソート機能実装
3. ⏳ クライアントサイドフィルタリング
4. ⏳ CSVエクスポート機能

### Phase 4: 最適化・UX改善 (Week 4)
1. ⏳ パフォーマンス最適化 (仮想スクロール)
2. ⏳ レスポンシブ対応強化
3. ⏳ アクセシビリティ改善
4. ⏳ ユーザーテスト・フィードバック反映

## パフォーマンス要件

- **初回ロード**: < 2秒 (100件データ)
- **検索レスポンス**: < 500ms
- **フィルタ切替**: < 100ms (クライアントサイド)
- **スクロール**: 60fps維持 (仮想スクロール使用)
- **メモリ使用**: < 50MB (1000件データ)

## アクセシビリティ要件

- **WCAG 2.1 AA準拠**
- **キーボードナビゲーション**: Tab, Enter, Escapeキー対応
- **スクリーンリーダー**: ARIAラベル、role属性適切に設定
- **色覚異常対応**: 色だけでなくアイコン・テキストでステータス表示
- **コントラスト比**: 4.5:1以上 (テキスト)

## セキュリティ考慮事項

- **認証**: Token認証必須 (authFetch使用)
- **XSS対策**: ユーザー入力のサニタイズ
- **CSRF対策**: CSRFトークン検証
- **権限管理**: 閲覧権限チェック

## 今後の拡張機能

1. **リアルタイム更新**: WebSocketで工程ステータス自動更新
2. **工程ドラッグ&ドロップ**: スケジュール調整機能
3. **カレンダービュー**: 月間/週間表示切替
4. **通知機能**: 納期接近アラート
5. **レポート機能**: 進捗レポート自動生成
6. **モバイルアプリ**: 現場でのステータス更新

## 参考資料

- 既存テンプレート: `/Users/okinotakumiware/open-mes-project/open_mes/scr/templates/production/gantt_chart.html`
- 既存コンポーネント: `frontend/src/pages/ProductionPlan.jsx`
- モデル定義: `backend/src/production/models.py`
- API設定: `backend/src/production/rest_views.py`
