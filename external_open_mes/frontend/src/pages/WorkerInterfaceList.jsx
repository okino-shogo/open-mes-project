import React, { useState, useEffect, useCallback, useRef } from 'react';
import authFetch from '../utils/api.js';
import './WorkerInterfaceList.css';

// ユニークID生成用カウンター
let historyIdCounter = 0;
const generateUniqueId = () => {
  return `${Date.now()}-${historyIdCounter++}`;
};

// 工程名のマッピング
const PROCESS_NAMES = {
  'slit': 'スリット',
  'cut': 'カット',
  'base_material_cut': '基材カット',
  'molder': 'モルダー',
  'v_cut_lapping': 'Vカットラッピング',
  'post_processing': '後加工',
  'packing': '梱包',
  'decorative_board': '化粧板貼付',
  'decorative_board_cut': '化粧板カット'
};

// 工程定義（APIフィールドとのマッピング）
const PROCESSES = [
  { key: 'slit', label: 'スリット', dateField: 'slit_scheduled_date', statusField: 'slit_status' },
  { key: 'cut', label: 'カット', dateField: 'cut_scheduled_date', statusField: 'cut_status' },
  { key: 'base_material_cut', label: '基材カット', dateField: 'base_material_cut_scheduled_date', statusField: 'base_material_cut_status' },
  { key: 'molder', label: 'モルダー', dateField: 'molder_scheduled_date', statusField: 'molder_status' },
  { key: 'v_cut_lapping', label: 'Vカットラッピング', dateField: 'vcut_wrapping_scheduled_date', statusField: 'v_cut_lapping_status' },
  { key: 'post_processing', label: '後加工', dateField: 'post_processing_scheduled_date', statusField: 'post_processing_status' },
  { key: 'packing', label: '梱包', dateField: 'packing_scheduled_date', statusField: 'packing_status' },
  { key: 'decorative_board', label: '化粧板貼付', dateField: 'veneer_scheduled_date', statusField: 'decorative_board_status' },
  { key: 'decorative_board_cut', label: '化粧板カット', dateField: 'cut_veneer_scheduled_date', statusField: 'decorative_board_cut_status' }
];

const WorkerInterfaceList = () => {
  // 状態管理
  const [productionPlans, setProductionPlans] = useState([]);
  const [filteredPlans, setFilteredPlans] = useState([]);
  const [workerId, setWorkerId] = useState('');
  const [selectedProcess, setSelectedProcess] = useState('');
  const [currentTime, setCurrentTime] = useState(new Date());
  const [operationHistory, setOperationHistory] = useState([]);
  const [summaryData, setSummaryData] = useState({ totalItems: 0, totalProduction: 0 });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // 操作履歴に追加
  const addToHistory = useCallback((message, type = 'info') => {
    const timestamp = new Date().toLocaleTimeString('ja-JP');
    const historyItem = {
      id: generateUniqueId(),
      timestamp,
      message,
      type
    };
    setOperationHistory(prev => [historyItem, ...prev]);
  }, []);

  // 生産計画データ取得
  const loadProductionPlans = useCallback(async (silent = false) => {
    try {
      setLoading(true);
      const response = await authFetch('/api/production/plans/?page_size=100');
      if (response.ok) {
        const data = await response.json();
        const plans = data.results || [];
        setProductionPlans(plans);

        if (!silent && plans.length > 0) {
          addToHistory(`${plans.length}件の生産計画を読み込みました`, 'success');
        }
      } else {
        throw new Error(`HTTP ${response.status}`);
      }
    } catch (err) {
      console.error('生産計画の取得に失敗:', err);
      setError(err.message);
      addToHistory('エラー: 生産計画の読み込みに失敗しました', 'error');
    } finally {
      setLoading(false);
    }
  }, [addToHistory]);

  // 現在時刻更新（1秒ごと）
  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentTime(new Date());
    }, 1000);
    return () => clearInterval(timer);
  }, []);

  // 初回データ読み込み
  useEffect(() => {
    loadProductionPlans();
    addToHistory('システムが初期化されました', 'info');
  }, [loadProductionPlans, addToHistory]);

  // バックグラウンド同期（5分ごと）
  useEffect(() => {
    const syncInterval = setInterval(() => {
      console.log('バックグラウンド同期開始...');
      loadProductionPlans(true); // silent mode
    }, 5 * 60 * 1000);

    return () => clearInterval(syncInterval);
  }, [loadProductionPlans]);

  // 工程ステータスを取得
  const getProcessStatus = useCallback((plan, processType) => {
    if (!processType) return plan.status || 'PENDING';

    const process = PROCESSES.find(p => p.key === processType);
    if (!process) return 'PENDING';

    const status = plan[process.statusField];

    // 日本語ステータスを英語にマッピング
    const statusMap = {
      '未着手': 'PENDING',
      '着手中': 'IN_PROGRESS',
      '完了': 'COMPLETED',
      '遅延': 'DELAYED',
      '保留': 'ON_HOLD',
      '中止': 'CANCELLED'
    };

    return statusMap[status] || 'PENDING';
  }, []);

  // 工程の予定日を取得
  const getProcessScheduledDate = useCallback((plan, processType) => {
    if (!processType) return '-';

    const process = PROCESSES.find(p => p.key === processType);
    if (!process) return '-';

    const scheduledDate = plan[process.dateField];

    if (!scheduledDate) {
      // フォールバック日付
      const fallbackDates = [
        plan.planned_start_datetime,
        plan.planned_shipment_date,
        plan.delivery_date
      ];

      for (const fallbackDate of fallbackDates) {
        if (fallbackDate) {
          try {
            const date = new Date(fallbackDate);
            if (!isNaN(date.getTime())) {
              return `(${date.toLocaleDateString('ja-JP')})`;
            }
          } catch (error) {
            continue;
          }
        }
      }
      return '-';
    }

    try {
      const date = new Date(scheduledDate);
      if (isNaN(date.getTime())) return '-';

      return date.toLocaleDateString('ja-JP', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit'
      });
    } catch (error) {
      return '-';
    }
  }, []);

  // ステータスのCSSクラスを取得
  const getStatusClass = useCallback((status) => {
    const classMap = {
      'IN_PROGRESS': 'status-in-progress',
      'COMPLETED': 'status-completed',
      'DELAYED': 'status-delayed',
      'ON_HOLD': 'status-on-hold',
      'CANCELLED': 'status-cancelled',
      'PENDING': 'status-not-started'
    };
    return classMap[status] || 'status-not-started';
  }, []);

  // ステータスのテキストを取得
  const getStatusText = useCallback((status) => {
    const textMap = {
      'IN_PROGRESS': '着手中',
      'COMPLETED': '完了',
      'DELAYED': '遅延',
      'ON_HOLD': '保留',
      'CANCELLED': '中止',
      'PENDING': '未着手'
    };
    return textMap[status] || '未着手';
  }, []);

  // フィルタリングとソート
  useEffect(() => {
    let filtered = [...productionPlans];

    // 工程フィルター
    if (selectedProcess) {
      filtered = filtered.filter(plan => {
        const processStatus = getProcessStatus(plan, selectedProcess);
        return processStatus !== 'COMPLETED' && processStatus !== 'CANCELLED';
      });
    }

    // 予定日順にソート
    filtered.sort((a, b) => {
      const dateA = selectedProcess
        ? PROCESSES.find(p => p.key === selectedProcess)?.dateField
          ? a[PROCESSES.find(p => p.key === selectedProcess).dateField]
          : null
        : a.planned_start_datetime;

      const dateB = selectedProcess
        ? PROCESSES.find(p => p.key === selectedProcess)?.dateField
          ? b[PROCESSES.find(p => p.key === selectedProcess).dateField]
          : null
        : b.planned_start_datetime;

      if (!dateA && !dateB) return 0;
      if (!dateA) return 1;
      if (!dateB) return -1;

      return new Date(dateA) - new Date(dateB);
    });

    setFilteredPlans(filtered);

    // サマリー更新
    setSummaryData({
      totalItems: filtered.length,
      totalProduction: filtered.reduce((sum, plan) => sum + (plan.planned_quantity || 0), 0)
    });
  }, [productionPlans, selectedProcess, getProcessStatus]);

  // 楽観的UI更新
  const updateUIOptimistically = useCallback((planId, processType, action) => {
    setProductionPlans(prev => prev.map(plan => {
      if (plan.id !== planId) return plan;

      const process = PROCESSES.find(p => p.key === processType);
      if (!process) return plan;

      const updatedPlan = { ...plan };

      if (action === 'start') {
        updatedPlan[process.statusField] = '着手中';
      } else if (action === 'complete') {
        updatedPlan[process.statusField] = '完了';
      }

      return updatedPlan;
    }));
  }, []);

  // UIロールバック
  const rollbackUI = useCallback((planId, processType, originalStatus) => {
    setProductionPlans(prev => prev.map(plan => {
      if (plan.id !== planId) return plan;

      const process = PROCESSES.find(p => p.key === processType);
      if (!process) return plan;

      const updatedPlan = { ...plan };
      const statusMap = {
        'PENDING': '未着手',
        'IN_PROGRESS': '着手中',
        'COMPLETED': '完了',
        'DELAYED': '遅延',
        'ON_HOLD': '保留',
        'CANCELLED': '中止'
      };

      updatedPlan[process.statusField] = statusMap[originalStatus] || '未着手';
      return updatedPlan;
    }));
  }, []);

  // 工程ステータス更新API
  const updateProcessStatusAsync = useCallback(async (planId, processType, action, workerId) => {
    const data = {
      plan_id: planId,
      process_type: processType,
      action: action,
      worker_id: workerId,
      timestamp: new Date().toISOString()
    };

    const response = await authFetch('/api/production/plans/update-process-status/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(data)
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.error || errorData.message || `HTTP ${response.status}`);
    }

    const result = await response.json();
    if (!result.success) {
      throw new Error(result.message || result.error || 'ステータス更新に失敗しました');
    }

    return result;
  }, []);

  // 単一計画同期
  const syncSinglePlan = useCallback(async (planId) => {
    try {
      const response = await authFetch(`/api/production/plans/${planId}/`);
      if (response.ok) {
        const updatedPlan = await response.json();
        setProductionPlans(prev =>
          prev.map(p => p.id === planId ? updatedPlan : p)
        );
      }
    } catch (error) {
      console.warn('単一計画同期エラー:', error);
    }
  }, []);

  // 作業開始・終了切り替え
  const toggleWork = useCallback(async (planId) => {
    if (!selectedProcess) {
      alert('工程を選択してください');
      return;
    }

    const plan = productionPlans.find(p => p.id === planId);
    if (!plan) {
      alert('計画が見つかりません');
      return;
    }

    const currentStatus = getProcessStatus(plan, selectedProcess);

    if (currentStatus === 'COMPLETED') {
      addToHistory('この工程は既に完了しています', 'error');
      return;
    }

    if (currentStatus === 'CANCELLED') {
      addToHistory('この工程は中止されています', 'error');
      return;
    }

    const action = currentStatus === 'IN_PROGRESS' ? 'complete' : 'start';

    // 開始ボタンの場合のみ作業者IDチェック
    if (action === 'start' && !workerId) {
      alert('作業者IDを入力してください');
      return;
    }
    const actionText = action === 'start' ? '開始' : '完了';

    // 楽観的UI更新
    updateUIOptimistically(planId, selectedProcess, action);
    addToHistory(`${actionText}中...`, 'info');

    try {
      const result = await updateProcessStatusAsync(planId, selectedProcess, action, workerId);
      addToHistory(`工程${actionText}: ${result.message}`, 'success');
      await syncSinglePlan(planId);
    } catch (error) {
      rollbackUI(planId, selectedProcess, currentStatus);
      addToHistory(`エラー: ${error.message}`, 'error');
    }
  }, [workerId, selectedProcess, productionPlans, getProcessStatus, updateUIOptimistically, rollbackUI, updateProcessStatusAsync, syncSinglePlan, addToHistory]);

  // 工程選択変更
  const handleProcessChange = useCallback((e) => {
    const process = e.target.value;
    setSelectedProcess(process);

    const processName = process ? PROCESS_NAMES[process] || process : '全工程';
    if (process) {
      addToHistory(`工程「${processName}」を選択しました`, 'info');
    } else {
      addToHistory('全工程を表示します', 'info');
    }
  }, [addToHistory]);

  // 日報作成（準備中）
  const generateReport = useCallback(() => {
    addToHistory('日報作成機能は準備中です', 'info');
  }, [addToHistory]);

  return (
    <div className="worker-interface-list container-fluid">
      {/* ヘッダー */}
      <div className="row mb-3">
        <div className="col-12">
          <div className="card">
            <div className="card-header bg-dark text-white text-center">
              <div className="row align-items-center">
                <div className="col-4">
                  <h4 className="mb-0">物件数</h4>
                </div>
                <div className="col-4">
                  <h4 className="mb-0">製作数</h4>
                </div>
                <div className="col-4">
                  <button className="btn btn-warning btn-lg" onClick={generateReport}>
                    <strong>日報<br />作成</strong>
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* 本日の製作完了予定残数 */}
      <div className="row mb-3">
        <div className="col-12">
          <div className="card">
            <div className="card-header bg-dark text-white text-center">
              <h5 className="mb-0">本日の製作完了予定残数</h5>
              <div className="row mt-2">
                <div className="col-6">
                  <span className="text-danger fs-1 fw-bold">{summaryData.totalItems}</span>
                </div>
                <div className="col-6">
                  <span className="text-danger fs-1 fw-bold">{summaryData.totalProduction}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* 作業者情報入力 */}
      <div className="row mb-3">
        <div className="col-12">
          <div className="card">
            <div className="card-body">
              <div className="row g-2">
                <div className="col-md-4">
                  <label className="form-label fw-bold">作業者ID</label>
                  <input
                    type="text"
                    className="form-control form-control-lg"
                    placeholder="作業者IDを入力"
                    value={workerId}
                    onChange={(e) => setWorkerId(e.target.value)}
                  />
                </div>
                <div className="col-md-4">
                  <label className="form-label fw-bold">工程選択</label>
                  <select
                    className="form-select form-select-lg"
                    value={selectedProcess}
                    onChange={handleProcessChange}
                  >
                    <option value="">工程を選択してください</option>
                    {PROCESSES.map(process => (
                      <option key={process.key} value={process.key}>
                        {process.label}
                      </option>
                    ))}
                  </select>
                </div>
                <div className="col-md-4">
                  <label className="form-label fw-bold">現在時刻</label>
                  <div className="form-control form-control-lg text-center bg-light">
                    {currentTime.toLocaleString('ja-JP', {
                      year: 'numeric',
                      month: '2-digit',
                      day: '2-digit',
                      hour: '2-digit',
                      minute: '2-digit',
                      second: '2-digit'
                    })}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* 製作計画一覧 */}
      <div className="row">
        <div className="col-12">
          <div className="card">
            <div className="card-header bg-dark text-white">
              <h5 className="mb-0">生産計画一覧</h5>
            </div>
            <div className="card-body p-0">
              {loading && <div className="text-center p-3">読み込み中...</div>}
              {error && <div className="alert alert-danger m-3">エラー: {error}</div>}

              {!loading && !error && (
                <div className="table-responsive">
                  <table className="table table-hover table-striped mb-0">
                    <thead className="table-dark">
                      <tr>
                        <th>区分</th>
                        <th>受付No.</th>
                        <th>追加No.</th>
                        <th>現場名</th>
                        <th>追加内容</th>
                        <th>品名</th>
                        <th>製作数</th>
                        <th>{selectedProcess ? `${PROCESS_NAMES[selectedProcess]}予定日` : '予定日'}</th>
                        <th>開始終了</th>
                      </tr>
                    </thead>
                    <tbody>
                      {filteredPlans.length === 0 ? (
                        <tr>
                          <td colSpan="9" className="text-center">データがありません</td>
                        </tr>
                      ) : (
                        filteredPlans.map(plan => {
                          const processStatus = getProcessStatus(plan, selectedProcess);
                          const statusClass = getStatusClass(processStatus);
                          const statusText = getStatusText(processStatus);
                          const scheduledDate = getProcessScheduledDate(plan, selectedProcess);
                          const displayProcessName = selectedProcess ? PROCESS_NAMES[selectedProcess] || selectedProcess : '全工程';

                          return (
                            <tr key={plan.id}>
                              <td>{displayProcessName}</td>
                              <td>{plan.reception_no || plan.plan_name || '-'}</td>
                              <td>{plan.additional_no || '-'}</td>
                              <td>{plan.site_name || '-'}</td>
                              <td>{plan.additional_content || '-'}</td>
                              <td>{plan.product_name || plan.product_code || '-'}</td>
                              <td>{plan.planned_quantity || 0}</td>
                              <td>{scheduledDate}</td>
                              <td>
                                <button
                                  className={`btn btn-sm btn-work-toggle ${processStatus === 'IN_PROGRESS' ? 'btn-end' : 'btn-start'}`}
                                  onClick={() => toggleWork(plan.id)}
                                  disabled={processStatus === 'COMPLETED' || processStatus === 'CANCELLED'}
                                  data-status={processStatus}
                                >
                                  {processStatus === 'COMPLETED' ? '完了' :
                                   processStatus === 'CANCELLED' ? '中止' :
                                   processStatus === 'IN_PROGRESS' ? '終了' : '開始'}
                                </button>
                                <br />
                                <span className={`status-badge ${statusClass}`}>{statusText}</span>
                              </td>
                            </tr>
                          );
                        })
                      )}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* 操作履歴 */}
      <div className="row mt-3">
        <div className="col-12">
          <div className="card">
            <div className="card-header bg-secondary text-white">
              <h5 className="mb-0">操作履歴</h5>
            </div>
            <div className="card-body">
              <div className="operation-history">
                {operationHistory.length === 0 ? (
                  <div className="text-muted">操作履歴はここに表示されます</div>
                ) : (
                  operationHistory.map(item => (
                    <div
                      key={item.id}
                      className={`mb-1 ${
                        item.type === 'error' ? 'text-danger' :
                        item.type === 'success' ? 'text-success' :
                        'text-info'
                      }`}
                    >
                      <span className="text-muted">{item.timestamp}</span> - {item.message}
                    </div>
                  ))
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default WorkerInterfaceList;
