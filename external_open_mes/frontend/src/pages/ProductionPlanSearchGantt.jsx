import React, { useState, useEffect, useCallback } from 'react';
import authFetch from '../utils/api';
import './ProductionPlanSearchGantt.css';

// 工程定義（作業者インターフェースの9工程と一致）
// コンポーネント外で定義することで、useEffect依存配列での再生成を防ぐ
const PROCESS_DEFINITIONS = [
  { key: 'slit_scheduled_date', label: 'スリット', statusKey: 'slit_status' },
  { key: 'cut_scheduled_date', label: 'カット', statusKey: 'cut_status' },
  { key: 'base_material_cut_scheduled_date', label: '基材カット', statusKey: 'base_material_cut_status' },
  { key: 'molder_scheduled_date', label: 'モルダー', statusKey: 'molder_status' },
  { key: 'vcut_wrapping_scheduled_date', label: 'Vカットラッピング', statusKey: 'v_cut_lapping_status' },
  { key: 'post_processing_scheduled_date', label: '後加工', statusKey: 'post_processing_status' },
  { key: 'packing_scheduled_date', label: '梱包', statusKey: 'packing_status' },
  { key: 'veneer_scheduled_date', label: '化粧板貼', statusKey: 'decorative_board_status' },
  { key: 'cut_veneer_scheduled_date', label: 'カット化粧板', statusKey: 'decorative_board_cut_status' }
];

/**
 * 生産計画検索 (ガントチャート形式)
 *
 * 20列のフィールド対応検索機能と、工程スケジュールをガントチャート形式で表示する画面
 * 参考: open_mes/production/gantt_chart.html
 */
const ProductionPlanSearchGantt = () => {
  // 検索フィルター状態
  const [filters, setFilters] = useState({
    qr_code: '',
    reception_no: '',
    additional_no: '',
    customer_name: '',
    site_name: '',
    product_code: '',
    process: '',
    delivery_date_from: '',
    delivery_date_to: '',
    status: ''
  });

  // データ状態
  const [plans, setPlans] = useState([]);
  const [filteredPlans, setFilteredPlans] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [pagination, setPagination] = useState({ count: 0, next: null, previous: null });
  const [pageInfo, setPageInfo] = useState('');

  // UIフィルター状態
  const [statusFilter, setStatusFilter] = useState('all');
  const [sortBy, setSortBy] = useState('delivery');

  const pageSize = 100;

  // 検索クエリ構築
  const buildSearchQuery = useCallback((pageUrl = null) => {
    if (pageUrl) {
      try {
        const url = new URL(pageUrl);
        return url.pathname + url.search;
      } catch (e) {
        return pageUrl;
      }
    }
    const params = new URLSearchParams();
    params.append('page_size', pageSize.toString());

    if (filters.qr_code) params.append('qr_code', filters.qr_code);
    if (filters.reception_no) params.append('reception_no', filters.reception_no);
    if (filters.additional_no) params.append('additional_no', filters.additional_no);
    if (filters.customer_name) params.append('customer_name', filters.customer_name);
    if (filters.site_name) params.append('site_name', filters.site_name);
    if (filters.product_code) params.append('product_code', filters.product_code);
    if (filters.process) params.append('process', filters.process);
    if (filters.status) params.append('status', filters.status);
    if (filters.delivery_date_from) params.append('delivery_date_after', filters.delivery_date_from);
    if (filters.delivery_date_to) params.append('delivery_date_before', filters.delivery_date_to);

    return `/api/production/plans/?${params.toString()}`;
  }, [filters, pageSize]);

  // データ取得
  const fetchProductionPlans = useCallback(async (pageUrl = null) => {
    setLoading(true);
    setError(null);
    const url = buildSearchQuery(pageUrl);
    console.log('📡 API リクエスト URL:', url);

    try {
      const response = await authFetch(url);
      if (!response.ok) {
        throw new Error(`Network response was not ok: ${response.statusText}`);
      }
      const data = await response.json();

      // バックエンドから受け取った生産計画データをそのまま使用
      // ステータスはバックエンドのDBフィールドから取得される
      setPlans(data.results || []);
      setFilteredPlans(data.results || []);
      setPagination({ count: data.count, next: data.next, previous: data.previous });

      // ページ情報更新
      if (data.count > 0) {
        let currentPage = 1;
        if (data.next) {
          const nextPageUrl = new URL(data.next, window.location.origin);
          currentPage = parseInt(nextPageUrl.searchParams.get('page')) - 1;
        } else if (data.previous) {
          const prevPageUrl = new URL(data.previous, window.location.origin);
          currentPage = parseInt(prevPageUrl.searchParams.get('page')) + 1;
        }
        if (currentPage < 1 && data.count > 0) {
          currentPage = 1;
        }
        const totalPages = Math.ceil(data.count / pageSize);
        setPageInfo(`ページ ${currentPage} / ${totalPages} (全 ${data.count} 件)`);
      } else {
        setPageInfo('データがありません');
      }
    } catch (e) {
      const errorMessage = `生産計画データの取得中にエラーが発生しました: ${e.message}`;
      setError(errorMessage);
      console.error('❌ データ取得エラー:', e);
      console.error('❌ エラー詳細:', {
        message: e.message,
        url: url,
        filters: filters
      });
      setPlans([]);
      setFilteredPlans([]);
      setPageInfo('エラー');
    } finally {
      setLoading(false);
    }
  }, [buildSearchQuery, pageSize, filters]);

  // 初期データ取得（マウント時のみ）
  useEffect(() => {
    fetchProductionPlans();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []); // 初回レンダリング時のみ実行

  // フィルター変更ハンドラー
  const handleFilterChange = (e) => {
    const { name, value } = e.target;
    setFilters(prev => ({ ...prev, [name]: value }));
  };

  // 検索実行
  const handleSearch = (e) => {
    e.preventDefault();
    console.log('🔍 検索実行:', filters);
    fetchProductionPlans();
  };

  // 検索クリア
  const handleClearSearch = () => {
    setFilters({
      qr_code: '',
      reception_no: '',
      additional_no: '',
      customer_name: '',
      site_name: '',
      product_code: '',
      process: '',
      delivery_date_from: '',
      delivery_date_to: '',
      status: ''
    });
  };

  // ステータスフィルター適用
  useEffect(() => {
    let filtered = [...plans];

    // ステータスフィルター
    if (statusFilter !== 'all') {
      filtered = filtered.filter(plan => {
        return PROCESS_DEFINITIONS.some(({ statusKey }) => plan[statusKey] === statusFilter);
      });
    }

    // ソート
    filtered.sort((a, b) => {
      switch (sortBy) {
        case 'delivery':
          return (a.delivery_date || '').localeCompare(b.delivery_date || '');
        case 'reception':
          return (a.reception_no || '').localeCompare(b.reception_no || '');
        case 'progress':
          const progressA = PROCESS_DEFINITIONS.filter(({ statusKey }) => a[statusKey] === 'COMPLETED').length;
          const progressB = PROCESS_DEFINITIONS.filter(({ statusKey }) => b[statusKey] === 'COMPLETED').length;
          return progressB - progressA;
        case 'urgent':
          const delayedA = PROCESS_DEFINITIONS.filter(({ statusKey }) => a[statusKey] === 'DELAYED').length;
          const delayedB = PROCESS_DEFINITIONS.filter(({ statusKey }) => b[statusKey] === 'DELAYED').length;
          return delayedB - delayedA;
        default:
          return 0;
      }
    });

    setFilteredPlans(filtered);
  }, [plans, statusFilter, sortBy]);

  // 日付フォーマット
  const formatDate = (dateStr) => {
    if (!dateStr) return '';
    try {
      const date = new Date(dateStr);
      return `${date.getMonth() + 1}/${date.getDate()}`;
    } catch {
      return dateStr;
    }
  };

  // ステータス表示名を取得（英語コード→日本語）
  const getStatusDisplay = (statusCode) => {
    const statusMap = {
      'PENDING': '未着手',
      'IN_PROGRESS': '着手中',
      'COMPLETED': '完了',
      'DELAYED': '遅延',
      'ON_HOLD': '保留',
    };
    return statusMap[statusCode] || '未着手';
  };

  // ステータスクラス取得
  const getStatusClass = (statusCode) => {
    switch (statusCode) {
      case 'COMPLETED': return 'status-completed';
      case 'IN_PROGRESS': return 'status-inprogress';
      case 'DELAYED': return 'status-delayed';
      case 'ON_HOLD': return 'status-onhold';
      default: return 'status-notstarted';
    }
  };

  // ステータスバッジクラス取得
  const getBadgeClass = (statusCode) => {
    switch (statusCode) {
      case 'COMPLETED': return 'bg-success';
      case 'IN_PROGRESS': return 'bg-warning';
      case 'DELAYED': return 'bg-danger';
      case 'ON_HOLD': return 'bg-info';
      default: return 'bg-secondary';
    }
  };

  return (
    <div className="production-plan-search-gantt container-fluid mt-4">
      <h2 className="text-center mb-4">生産計画検索 (工程スケジュール)</h2>

      {/* 検索フィルターセクション */}
      <div className="card card-body bg-light mb-4">
        <form onSubmit={handleSearch}>
          <div className="row gx-2 gy-2 mb-3">
            <div className="col-md-2">
              <input
                type="text"
                name="qr_code"
                value={filters.qr_code}
                onChange={handleFilterChange}
                className="form-control form-control-sm"
                placeholder="QRコード"
              />
            </div>
            <div className="col-md-2">
              <input
                type="text"
                name="reception_no"
                value={filters.reception_no}
                onChange={handleFilterChange}
                className="form-control form-control-sm"
                placeholder="受付No"
              />
            </div>
            <div className="col-md-2">
              <input
                type="text"
                name="additional_no"
                value={filters.additional_no}
                onChange={handleFilterChange}
                className="form-control form-control-sm"
                placeholder="追加No"
              />
            </div>
            <div className="col-md-2">
              <input
                type="text"
                name="customer_name"
                value={filters.customer_name}
                onChange={handleFilterChange}
                className="form-control form-control-sm"
                placeholder="得意先名"
              />
            </div>
            <div className="col-md-2">
              <input
                type="text"
                name="site_name"
                value={filters.site_name}
                onChange={handleFilterChange}
                className="form-control form-control-sm"
                placeholder="現場名"
              />
            </div>
            <div className="col-md-2">
              <input
                type="text"
                name="product_code"
                value={filters.product_code}
                onChange={handleFilterChange}
                className="form-control form-control-sm"
                placeholder="品名"
              />
            </div>
          </div>
          <div className="row gx-2 gy-2 mb-3">
            <div className="col-md-2">
              <input
                type="text"
                name="process"
                value={filters.process}
                onChange={handleFilterChange}
                className="form-control form-control-sm"
                placeholder="工程"
              />
            </div>
            <div className="col-md-2">
              <select
                name="status"
                value={filters.status}
                onChange={handleFilterChange}
                className="form-select form-select-sm"
              >
                <option value="">ステータス (すべて)</option>
                <option value="PENDING">未着手</option>
                <option value="IN_PROGRESS">進行中</option>
                <option value="COMPLETED">完了</option>
                <option value="ON_HOLD">保留</option>
                <option value="CANCELLED">中止</option>
              </select>
            </div>
            <div className="col-md-auto">
              <label className="form-label mb-0 me-1">納品日:</label>
            </div>
            <div className="col-md-2">
              <input
                type="date"
                name="delivery_date_from"
                value={filters.delivery_date_from}
                onChange={handleFilterChange}
                className="form-control form-control-sm"
              />
            </div>
            <div className="col-md-auto text-center px-1">～</div>
            <div className="col-md-2">
              <input
                type="date"
                name="delivery_date_to"
                value={filters.delivery_date_to}
                onChange={handleFilterChange}
                className="form-control form-control-sm"
              />
            </div>
            <div className="col-md-auto ms-md-2 mt-2 mt-md-0">
              <button type="submit" className="btn btn-success btn-sm">検索</button>
              <button type="button" onClick={handleClearSearch} className="btn btn-danger btn-sm ms-1">クリア</button>
            </div>
          </div>
        </form>
      </div>

      {/* ステータスフィルター・ソート */}
      <div className="filter-controls mb-3">
        <div className="mb-2">
          <label className="form-label fw-bold">ステータスフィルター:</label>
          <div className="d-flex flex-wrap gap-2">
            <button
              className={`btn btn-sm btn-outline-success ${statusFilter === 'COMPLETED' ? 'active' : ''}`}
              onClick={() => setStatusFilter('COMPLETED')}
            >
              完了のみ
            </button>
            <button
              className={`btn btn-sm btn-outline-warning ${statusFilter === 'IN_PROGRESS' ? 'active' : ''}`}
              onClick={() => setStatusFilter('IN_PROGRESS')}
            >
              着手中のみ
            </button>
            <button
              className={`btn btn-sm btn-outline-secondary ${statusFilter === 'PENDING' ? 'active' : ''}`}
              onClick={() => setStatusFilter('PENDING')}
            >
              未着手のみ
            </button>
            <button
              className={`btn btn-sm btn-outline-danger ${statusFilter === 'DELAYED' ? 'active' : ''}`}
              onClick={() => setStatusFilter('DELAYED')}
            >
              遅延のみ
            </button>
            <button
              className={`btn btn-sm btn-outline-info ${statusFilter === 'all' ? 'active' : ''}`}
              onClick={() => setStatusFilter('all')}
            >
              すべて表示
            </button>
          </div>
        </div>
        <div>
          <label className="form-label fw-bold">並び替え:</label>
          <div className="d-flex flex-wrap gap-2">
            <button
              className={`btn btn-sm btn-outline-primary ${sortBy === 'delivery' ? 'active' : ''}`}
              onClick={() => setSortBy('delivery')}
            >
              納期順
            </button>
            <button
              className={`btn btn-sm btn-outline-primary ${sortBy === 'reception' ? 'active' : ''}`}
              onClick={() => setSortBy('reception')}
            >
              受注番号順
            </button>
            <button
              className={`btn btn-sm btn-outline-primary ${sortBy === 'progress' ? 'active' : ''}`}
              onClick={() => setSortBy('progress')}
            >
              進捗順
            </button>
            <button
              className={`btn btn-sm btn-outline-primary ${sortBy === 'urgent' ? 'active' : ''}`}
              onClick={() => setSortBy('urgent')}
            >
              緊急度順
            </button>
          </div>
        </div>
      </div>

      {/* ガントチャート表示 */}
      <div className="table-responsive">
        <table className="table table-striped table-hover table-bordered table-sm gantt-table">
          <thead>
            <tr>
              <th rowSpan="2" className="text-center align-middle sticky-col">受付No</th>
              <th rowSpan="2" className="text-center align-middle">連番</th>
              <th rowSpan="2" className="text-center align-middle">工程</th>
              <th rowSpan="2" className="text-center align-middle">現場名</th>
              <th rowSpan="2" className="text-center align-middle">追加内容</th>
              <th rowSpan="2" className="text-center align-middle">品名</th>
              <th rowSpan="2" className="text-center align-middle">数量</th>
              <th rowSpan="2" className="text-center align-middle delivery-target-header">納期目標</th>
              <th colSpan={PROCESS_DEFINITIONS.length} className="text-center">工程スケジュール</th>
            </tr>
            <tr>
              {PROCESS_DEFINITIONS.map(({ label }) => (
                <th key={label} className="text-center">{label}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {loading && (
              <tr>
                <td colSpan={8 + PROCESS_DEFINITIONS.length} className="text-center">読み込み中...</td>
              </tr>
            )}
            {error && (
              <tr>
                <td colSpan={8 + PROCESS_DEFINITIONS.length} className="text-center text-danger">{error}</td>
              </tr>
            )}
            {!loading && !error && filteredPlans.length === 0 && (
              <tr>
                <td colSpan={8 + PROCESS_DEFINITIONS.length} className="text-center">生産計画データがありません。</td>
              </tr>
            )}
            {!loading && !error && filteredPlans.map(plan => (
              <tr key={plan.id}>
                <td className="text-center sticky-col">{plan.reception_no || ''}</td>
                <td className="text-center">{plan.additional_no || ''}</td>
                <td className="text-center">{plan.process || ''}</td>
                <td>{plan.site_name || ''}</td>
                <td>{plan.additional_content || ''}</td>
                <td>{plan.product_code || ''}</td>
                <td className="text-center">{plan.planned_quantity || ''}</td>
                <td className="text-center delivery-target">
                  {plan.delivery_date ? <strong>{formatDate(plan.delivery_date)}</strong> : '-'}
                </td>
                {PROCESS_DEFINITIONS.map(({ key, statusKey }) => {
                  const statusCode = plan[statusKey] || 'PENDING';
                  const statusDisplay = getStatusDisplay(statusCode);
                  const scheduledDate = plan[key];
                  return (
                    <td key={key} className={`text-center process-cell ${getStatusClass(statusCode)}`}>
                      <div className="process-cell-content">
                        <span className={`badge ${getBadgeClass(statusCode)} mb-1`}>
                          {statusDisplay}
                        </span>
                        {scheduledDate && (
                          <small className="d-block">
                            <strong>予定:</strong> {formatDate(scheduledDate)}
                          </small>
                        )}
                      </div>
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* ページネーション */}
      <div className="text-center mt-4">
        <button
          onClick={() => fetchProductionPlans(pagination.previous)}
          className="btn btn-outline-primary mx-1"
          disabled={!pagination.previous}
        >
          前へ
        </button>
        <span className="mx-2">{pageInfo}</span>
        <button
          onClick={() => fetchProductionPlans(pagination.next)}
          className="btn btn-outline-primary mx-1"
          disabled={!pagination.next}
        >
          次へ
        </button>
      </div>
    </div>
  );
};

export default ProductionPlanSearchGantt;
