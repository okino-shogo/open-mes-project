import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import authFetch from '../utils/api.js';
import './WorkerPerformanceList.css';

const WorkerPerformanceList = () => {
  const navigate = useNavigate();
  const [workers, setWorkers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchWorkers();
  }, []);

  const fetchWorkers = async () => {
    try {
      setLoading(true);
      const response = await authFetch('/api/users/');

      if (!response.ok) {
        throw new Error('作業者リストの取得に失敗しました');
      }

      const data = await response.json();
      setWorkers(data);
      setError(null);
    } catch (err) {
      console.error('Error fetching workers:', err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleWorkerClick = (workerId) => {
    navigate(`/system/worker-performance/${workerId}`);
  };

  if (loading) {
    return (
      <div className="worker-performance-list">
        <h1>作業者パフォーマンス</h1>
        <div className="loading-message">読み込み中...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="worker-performance-list">
        <h1>作業者パフォーマンス</h1>
        <div className="error-message">エラー: {error}</div>
        <button onClick={fetchWorkers} className="retry-button">再読み込み</button>
      </div>
    );
  }

  return (
    <div className="worker-performance-list">
      <h1>作業者パフォーマンス</h1>
      <p className="description">
        作業者を選択して、技能評価と作業実績を確認できます。
      </p>

      <div className="workers-grid">
        {workers.length === 0 ? (
          <div className="no-workers">作業者が登録されていません</div>
        ) : (
          workers.map((worker) => (
            <div
              key={worker.id}
              className="worker-card"
              onClick={() => handleWorkerClick(worker.id)}
            >
              <div className="worker-card-header">
                <div className="worker-name">
                  {worker.last_name} {worker.first_name}
                </div>
                <div className="worker-username">@{worker.username}</div>
              </div>
              <div className="worker-card-footer">
                <span className="view-details-link">詳細を見る →</span>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
};

export default WorkerPerformanceList;
