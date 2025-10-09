import React, { useState, useEffect, useCallback, useMemo, useRef } from 'react';
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
  const [workerId, setWorkerId] = useState('');
  const [workers, setWorkers] = useState([]);
  const [selectedProcess, setSelectedProcess] = useState('');
  const [currentTime, setCurrentTime] = useState(new Date());
  const [operationHistory, setOperationHistory] = useState([]);
  const [recentOperations, setRecentOperations] = useState([]); // 最近の作業操作（WorkProgress）
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [processingPlanId, setProcessingPlanId] = useState(null); // 処理中の計画ID
  const [cancellingWorkProgressId, setCancellingWorkProgressId] = useState(null); // 取り消し処理中の操作ID

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

  // 作業者リスト取得
  const loadWorkers = useCallback(async () => {
    try {
      const response = await authFetch('/api/users/workers/');
      if (response.ok) {
        const data = await response.json();
        setWorkers(data || []);

        // LocalStorageから前回選択した作業者を復元
        const savedWorkerId = localStorage.getItem('selectedWorkerId');
        if (savedWorkerId && data.some(w => w.username === savedWorkerId)) {
          setWorkerId(savedWorkerId);
          const worker = data.find(w => w.username === savedWorkerId);
          addToHistory(`作業者「${worker.display_name}」を選択しました`, 'info');
        }
      } else {
        console.error('作業者リストの取得に失敗:', response.status);
      }
    } catch (err) {
      console.error('作業者リストの取得エラー:', err);
    }
  }, [addToHistory]);

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

  // 最近の操作履歴を取得
  const loadRecentOperations = useCallback(async () => {
    try {
      const response = await authFetch('/api/production/work-progress/recent-operations/?limit=10');
      if (response.ok) {
        const data = await response.json();
        if (data.success && data.operations) {
          setRecentOperations(data.operations);
        }
      } else {
        console.error('最近の操作の取得に失敗:', response.status);
      }
    } catch (err) {
      console.error('最近の操作の取得エラー:', err);
    }
  }, []);

  // 操作を取り消す
  const cancelOperation = useCallback(async (workProgressId) => {
    if (!workProgressId) return;

    if (!confirm('この操作を取り消しますか?')) {
      return;
    }

    setCancellingWorkProgressId(workProgressId);

    try {
      const response = await authFetch('/api/production/work-progress/cancel-operation/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          work_progress_id: workProgressId
        })
      });

      if (!response.ok) {
        let errorData = {};
        try {
          errorData = await response.json();
        } catch (parseError) {
          console.error('エラーレスポンスのJSON parse失敗:', parseError);
        }
        const errorMessage = errorData.error || errorData.message || `HTTP ${response.status}`;
        throw new Error(errorMessage);
      }

      const result = await response.json();

      if (!result.success) {
        const errorMessage = result.message || result.error || '操作の取り消しに失敗しました';
        throw new Error(errorMessage);
      }

      addToHistory(`操作を取り消しました: ${result.message}`, 'success');

      // 更新されたplanデータで状態を更新
      if (result.plan) {
        setProductionPlans(prev =>
          prev.map(p => p.id === result.plan.id ? result.plan : p)
        );
      }

      // 操作履歴を再読み込み
      loadRecentOperations();

    } catch (error) {
      console.error('操作の取り消しエラー:', error);
      addToHistory(`エラー: ${error.message}`, 'error');
    } finally {
      setCancellingWorkProgressId(null);
    }
  }, [addToHistory, loadRecentOperations]);

  // 現在時刻更新（1秒ごと）
  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentTime(new Date());
    }, 1000);
    return () => clearInterval(timer);
  }, []);

  // 初回データ読み込み
  useEffect(() => {
    loadWorkers();
    loadProductionPlans();
    loadRecentOperations();
    addToHistory('システムが初期化されました', 'info');
  }, [loadWorkers, loadProductionPlans, loadRecentOperations, addToHistory]);

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

    // バックエンドから英語のステータスが返ってくるので、そのまま返す
    // 既に英語の値（'PENDING', 'IN_PROGRESS'など）の場合はそのまま
    const validStatuses = ['PENDING', 'IN_PROGRESS', 'COMPLETED', 'DELAYED', 'ON_HOLD', 'CANCELLED'];
    if (validStatuses.includes(status)) {
      return status;
    }

    // 互換性のため、日本語の場合も対応（旧データ用）
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

  // フィルタリングとソート（useMemoでキャッシュ化）
  const filteredAndSortedPlans = useMemo(() => {
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

    return filtered;
  }, [productionPlans, selectedProcess, getProcessStatus]);

  // サマリーデータ（useMemoでキャッシュ化）
  const summaryStats = useMemo(() => ({
    totalItems: filteredAndSortedPlans.length,
    totalProduction: filteredAndSortedPlans.reduce((sum, plan) => sum + (plan.planned_quantity || 0), 0)
  }), [filteredAndSortedPlans]);

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
    console.log('[updateProcessStatusAsync] 開始:', { planId, processType, action, workerId });

    const data = {
      plan_id: planId,
      process_type: processType,
      action: action,
      worker_id: workerId,
      timestamp: new Date().toISOString()
    };

    try {
      const response = await authFetch('/api/production/plans/update-process-status/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
      });

      console.log('[updateProcessStatusAsync] レスポンス受信:', { status: response.status, ok: response.ok });

      if (!response.ok) {
        let errorData = {};
        try {
          errorData = await response.json();
        } catch (parseError) {
          console.error('[updateProcessStatusAsync] エラーレスポンスのJSON parse失敗:', parseError);
        }
        const errorMessage = errorData.error || errorData.message || `HTTP ${response.status}`;
        console.error('[updateProcessStatusAsync] APIエラー:', errorMessage);
        throw new Error(errorMessage);
      }

      let result;
      try {
        result = await response.json();
        console.log('[updateProcessStatusAsync] レスポンスJSON:', result);
      } catch (parseError) {
        console.error('[updateProcessStatusAsync] レスポンスのJSON parse失敗:', parseError);
        throw new Error('サーバーレスポンスの解析に失敗しました');
      }

      if (!result.success) {
        const errorMessage = result.message || result.error || 'ステータス更新に失敗しました';
        console.error('[updateProcessStatusAsync] サーバーエラー:', errorMessage);
        throw new Error(errorMessage);
      }

      console.log('[updateProcessStatusAsync] 成功:', result.message);
      return result;
    } catch (error) {
      console.error('[updateProcessStatusAsync] 例外発生:', error);
      throw error;
    }
  }, []);

  // 作業開始・終了切り替え
  const toggleWork = useCallback(async (planId) => {
    console.log('[toggleWork] 開始:', { planId, selectedProcess, workerId, processingPlanId });

    // 既に処理中の計画がある場合は処理しない
    if (processingPlanId) {
      console.warn('[toggleWork] 既に処理中の計画があります:', processingPlanId);
      addToHistory('他の操作を処理中です。しばらくお待ちください。', 'warning');
      return;
    }

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
    console.log('[toggleWork] 現在のステータス:', currentStatus);

    if (currentStatus === 'COMPLETED') {
      addToHistory('この工程は既に完了しています', 'error');
      return;
    }

    if (currentStatus === 'CANCELLED') {
      addToHistory('この工程は中止されています', 'error');
      return;
    }

    const action = currentStatus === 'IN_PROGRESS' ? 'complete' : 'start';
    console.log('[toggleWork] アクション:', action);

    // 開始ボタンの場合のみ作業者IDチェック
    if (action === 'start' && !workerId) {
      alert('作業者IDを入力してください');
      return;
    }
    const actionText = action === 'start' ? '開始' : '完了';

    // 処理開始
    setProcessingPlanId(planId);

    // 楽観的UI更新
    console.log('[toggleWork] 楽観的UI更新実行');
    updateUIOptimistically(planId, selectedProcess, action);
    addToHistory(`${actionText}中...`, 'info');

    try {
      console.log('[toggleWork] API呼び出し前');
      const result = await updateProcessStatusAsync(planId, selectedProcess, action, workerId);
      console.log('[toggleWork] API呼び出し成功:', result);
      addToHistory(`工程${actionText}: ${result.message}`, 'success');

      // バックエンドから返された更新後のplanデータで状態を更新
      if (result.plan) {
        setProductionPlans(prev =>
          prev.map(p => p.id === planId ? result.plan : p)
        );
        console.log('[toggleWork] サーバーから受け取ったplanデータで状態を更新');
      }

      // 操作履歴を再読み込み
      loadRecentOperations();

      console.log('[toggleWork] 完了');
    } catch (error) {
      console.error('[toggleWork] エラー発生:', error);
      rollbackUI(planId, selectedProcess, currentStatus);
      addToHistory(`エラー: ${error.message}`, 'error');
    } finally {
      // 処理完了
      setProcessingPlanId(null);
      console.log('[toggleWork] 処理終了、ボタン有効化');
    }
  }, [workerId, selectedProcess, productionPlans, processingPlanId, getProcessStatus, updateUIOptimistically, rollbackUI, updateProcessStatusAsync, addToHistory, loadRecentOperations]);

  // 作業者選択変更
  const handleWorkerChange = useCallback((e) => {
    const selectedWorkerId = e.target.value;
    setWorkerId(selectedWorkerId);

    // LocalStorageに保存
    if (selectedWorkerId) {
      localStorage.setItem('selectedWorkerId', selectedWorkerId);
      const worker = workers.find(w => w.username === selectedWorkerId);
      if (worker) {
        addToHistory(`作業者「${worker.display_name}」を選択しました`, 'info');
      }
    } else {
      localStorage.removeItem('selectedWorkerId');
      addToHistory('作業者の選択を解除しました', 'info');
    }
  }, [workers, addToHistory]);

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
                  <span className="text-danger fs-1 fw-bold">{summaryStats.totalItems}</span>
                </div>
                <div className="col-6">
                  <span className="text-danger fs-1 fw-bold">{summaryStats.totalProduction}</span>
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
                  <label className="form-label fw-bold">作業者</label>
                  <select
                    className="form-select form-select-lg"
                    value={workerId}
                    onChange={handleWorkerChange}
                  >
                    <option value="">作業者を選択してください</option>
                    {workers.map(worker => (
                      <option key={worker.username} value={worker.username}>
                        {worker.display_name}
                      </option>
                    ))}
                  </select>
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

      {/* 最近の操作（直近1件のみ） */}
      {recentOperations.length > 0 && (
        <div className="row mb-3">
          <div className="col-12">
            <div className="card">
              <div className="card-header bg-primary text-white d-flex justify-content-between align-items-center">
                <h5 className="mb-0">最近の操作</h5>
                <button
                  className="btn btn-sm btn-light"
                  onClick={loadRecentOperations}
                  title="最新の状態に更新"
                >
                  🔄 更新
                </button>
              </div>
              <div className="card-body">
                {(() => {
                  const operation = recentOperations[0];  // 直近1件のみ
                  const createdAt = new Date(operation.created_at);
                  const timeStr = createdAt.toLocaleTimeString('ja-JP', {
                    hour: '2-digit',
                    minute: '2-digit'
                  });
                  const dateStr = createdAt.toLocaleDateString('ja-JP', {
                    month: '2-digit',
                    day: '2-digit'
                  });
                  const processName = PROCESS_NAMES[operation.process_type] || operation.process_step;
                  const workTypeName = operation.work_type === 'start' ? '開始' : '完了';
                  const planData = operation.production_plan;
                  const receptionNo = planData?.reception_no || planData?.plan_name || '-';
                  const workerName = operation.operator?.display_name || operation.operator?.username || '-';

                  return (
                    <div className="table-responsive">
                      <table className="table table-sm table-hover mb-0">
                        <thead>
                          <tr>
                            <th>時刻</th>
                            <th>受付No</th>
                            <th>工程</th>
                            <th>操作</th>
                            <th>作業者</th>
                            <th></th>
                          </tr>
                        </thead>
                        <tbody>
                          <tr>
                            <td>
                              <small className="text-muted">{dateStr}</small><br />
                              <strong>{timeStr}</strong>
                            </td>
                            <td>{receptionNo}</td>
                            <td>{processName}</td>
                            <td>
                              <span className={`badge ${operation.work_type === 'start' ? 'bg-success' : 'bg-info'}`}>
                                {workTypeName}
                              </span>
                            </td>
                            <td>{workerName}</td>
                            <td>
                              <button
                                className="btn btn-sm btn-outline-danger"
                                onClick={() => cancelOperation(operation.id)}
                                disabled={cancellingWorkProgressId === operation.id}
                              >
                                {cancellingWorkProgressId === operation.id ? '取り消し中...' : '取り消し'}
                              </button>
                            </td>
                          </tr>
                        </tbody>
                      </table>
                    </div>
                  );
                })()}
              </div>
            </div>
          </div>
        </div>
      )}

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
                      {filteredAndSortedPlans.length === 0 ? (
                        <tr>
                          <td colSpan="9" className="text-center">データがありません</td>
                        </tr>
                      ) : (
                        filteredAndSortedPlans.map(plan => {
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
                                  className={`btn btn-sm btn-work-toggle ${processStatus === 'IN_PROGRESS' ? 'btn-end' : 'btn-start'} ${processingPlanId === plan.id ? 'processing' : ''}`}
                                  onClick={() => toggleWork(plan.id)}
                                  disabled={
                                    processStatus === 'COMPLETED' ||
                                    processStatus === 'CANCELLED' ||
                                    processingPlanId !== null
                                  }
                                  data-status={processStatus}
                                >
                                  {processingPlanId === plan.id ? '処理中...' :
                                   processStatus === 'COMPLETED' ? '完了' :
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

      {/* 最近の操作（残りの履歴） */}
      {recentOperations.length > 1 && (
        <div className="row mt-3">
          <div className="col-12">
            <div className="card">
              <div className="card-header bg-primary text-white d-flex justify-content-between align-items-center">
                <h5 className="mb-0">最近の操作</h5>
                <button
                  className="btn btn-sm btn-light"
                  onClick={loadRecentOperations}
                  title="最新の状態に更新"
                >
                  🔄 更新
                </button>
              </div>
              <div className="card-body">
                <div className="table-responsive">
                  <table className="table table-sm table-hover mb-0">
                    <thead>
                      <tr>
                        <th>時刻</th>
                        <th>受付No</th>
                        <th>工程</th>
                        <th>操作</th>
                        <th>作業者</th>
                        <th></th>
                      </tr>
                    </thead>
                    <tbody>
                      {recentOperations.slice(1).map(operation => {
                        const createdAt = new Date(operation.created_at);
                        const timeStr = createdAt.toLocaleTimeString('ja-JP', {
                          hour: '2-digit',
                          minute: '2-digit'
                        });
                        const dateStr = createdAt.toLocaleDateString('ja-JP', {
                          month: '2-digit',
                          day: '2-digit'
                        });
                        const processName = PROCESS_NAMES[operation.process_type] || operation.process_step;
                        const workTypeName = operation.work_type === 'start' ? '開始' : '完了';
                        const planData = operation.production_plan;
                        const receptionNo = planData?.reception_no || planData?.plan_name || '-';
                        const workerName = operation.operator?.display_name || operation.operator?.username || '-';

                        return (
                          <tr key={operation.id}>
                            <td>
                              <small className="text-muted">{dateStr}</small><br />
                              <strong>{timeStr}</strong>
                            </td>
                            <td>{receptionNo}</td>
                            <td>{processName}</td>
                            <td>
                              <span className={`badge ${operation.work_type === 'start' ? 'bg-success' : 'bg-info'}`}>
                                {workTypeName}
                              </span>
                            </td>
                            <td>{workerName}</td>
                            <td>
                              <button
                                className="btn btn-sm btn-outline-danger"
                                onClick={() => cancelOperation(operation.id)}
                                disabled={cancellingWorkProgressId === operation.id}
                              >
                                {cancellingWorkProgressId === operation.id ? '取り消し中...' : '取り消し'}
                              </button>
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

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
