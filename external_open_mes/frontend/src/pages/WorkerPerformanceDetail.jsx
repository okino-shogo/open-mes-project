import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import authFetch from '../utils/api.js';
import './WorkerPerformanceDetail.css';

const WorkerPerformanceDetail = () => {
  const { workerId } = useParams();
  const navigate = useNavigate();
  const [performanceData, setPerformanceData] = useState(null);
  const [selectedProcess, setSelectedProcess] = useState(null);
  const [processTrend, setProcessTrend] = useState(null);
  const [loading, setLoading] = useState(true);
  const [trendLoading, setTrendLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchPerformanceData();
  }, [workerId]);

  useEffect(() => {
    if (selectedProcess) {
      fetchProcessTrend(selectedProcess);
    }
  }, [selectedProcess]);

  const fetchPerformanceData = async () => {
    try {
      setLoading(true);
      const response = await authFetch(`/api/production/worker-performance/${workerId}/`);

      if (!response.ok) {
        throw new Error('パフォーマンスデータの取得に失敗しました');
      }

      const data = await response.json();

      if (!data.success) {
        throw new Error(data.error || 'データの取得に失敗しました');
      }

      setPerformanceData(data.data);
      setError(null);

      // 最初の工程を自動選択
      if (data.data.process_skills && data.data.process_skills.length > 0) {
        setSelectedProcess(data.data.process_skills[0].process);
      }
    } catch (err) {
      console.error('Error fetching performance data:', err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const fetchProcessTrend = async (process) => {
    try {
      setTrendLoading(true);
      const response = await authFetch(
        `/api/production/worker-performance/${workerId}/${process}/`
      );

      if (!response.ok) {
        throw new Error('推移データの取得に失敗しました');
      }

      const data = await response.json();

      if (data.success) {
        setProcessTrend(data.data);
      }
    } catch (err) {
      console.error('Error fetching trend data:', err);
    } finally {
      setTrendLoading(false);
    }
  };

  const getSkillLevelColor = (skillLevel) => {
    const colors = {
      ADVANCED: '#4caf50',
      PROFICIENT: '#2196f3',
      COMPETENT: '#ff9800',
      DEVELOPING: '#ff5722',
      FOUNDATIONAL: '#9e9e9e',
    };
    return colors[skillLevel] || '#9e9e9e';
  };

  const getSkillLevelBadge = (skillLevel, display) => {
    return (
      <span
        className="skill-level-badge"
        style={{ backgroundColor: getSkillLevelColor(skillLevel) }}
      >
        {display}
      </span>
    );
  };

  if (loading) {
    return (
      <div className="worker-performance-detail">
        <div className="loading-message">読み込み中...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="worker-performance-detail">
        <div className="error-message">エラー: {error}</div>
        <button onClick={() => navigate('/system/worker-performance')} className="back-button">
          作業者一覧に戻る
        </button>
      </div>
    );
  }

  if (!performanceData) {
    return (
      <div className="worker-performance-detail">
        <div className="no-data">データがありません</div>
        <button onClick={() => navigate('/system/worker-performance')} className="back-button">
          作業者一覧に戻る
        </button>
      </div>
    );
  }

  return (
    <div className="worker-performance-detail">
      <div className="header-section">
        <button onClick={() => navigate('/system/worker-performance')} className="back-link">
          ← 作業者一覧に戻る
        </button>
        <h1>作業者技能プロフィール</h1>
        <h2 className="worker-name">{performanceData.worker_name}</h2>
      </div>

      {performanceData.summary && (
        <div className="summary-card">
          <h3>総合評価</h3>
          <div className="summary-grid">
            <div className="summary-item">
              <div className="summary-label">平均スコア</div>
              <div className="summary-value">{performanceData.summary.average_score}点</div>
            </div>
            <div className="summary-item">
              <div className="summary-label">総合技能レベル</div>
              <div className="summary-value">
                {getSkillLevelBadge(
                  performanceData.summary.primary_skill_level,
                  performanceData.summary.primary_skill_level_display
                )}
              </div>
            </div>
            <div className="summary-item">
              <div className="summary-label">評価工程数</div>
              <div className="summary-value">{performanceData.summary.total_processes}工程</div>
            </div>
            <div className="summary-item">
              <div className="summary-label">総タスク数</div>
              <div className="summary-value">{performanceData.summary.total_tasks}件</div>
            </div>
          </div>
          <div className="evaluation-note">
            <small>評価期間: 過去{performanceData.evaluation_period_days}日間</small>
            <br />
            <small>スコアの見方: 100点=平均, 100点超=平均より速い, 100点未満=平均より遅い</small>
          </div>
        </div>
      )}

      <div className="process-skills-section">
        <h3>工程別スコア</h3>
        <div className="process-grid">
          {performanceData.process_skills.map((processSkill) => (
            <div
              key={processSkill.process}
              className={`process-card ${
                selectedProcess === processSkill.process ? 'selected' : ''
              }`}
              onClick={() => setSelectedProcess(processSkill.process)}
            >
              <div className="process-name">{processSkill.process_display}</div>
              <div className="process-score">{processSkill.score}点</div>
              <div className="process-level">
                {getSkillLevelBadge(processSkill.skill_level, processSkill.skill_level_display)}
              </div>
              <div className="process-tasks">
                <small>{processSkill.task_count}タスク</small>
              </div>
            </div>
          ))}
        </div>
      </div>

      {selectedProcess && processTrend && (
        <div className="trend-section">
          <h3>{processTrend.process_display || selectedProcess}工程 - 詳細情報</h3>

          {trendLoading ? (
            <div className="loading-message">読み込み中...</div>
          ) : (
            <>
              <div className="current-score-card">
                <div className="score-item">
                  <div className="score-label">現在のスコア</div>
                  <div className="score-value large">{processTrend.score}点</div>
                </div>
                <div className="score-item">
                  <div className="score-label">技能レベル</div>
                  <div className="score-value">
                    {getSkillLevelBadge(
                      processTrend.skill_level,
                      processTrend.skill_level_display
                    )}
                  </div>
                </div>
                {processTrend.growth_rate !== null && (
                  <div className="score-item">
                    <div className="score-label">成長率（6ヶ月）</div>
                    <div
                      className={`score-value ${
                        processTrend.growth_rate > 0 ? 'positive' : 'negative'
                      }`}
                    >
                      {processTrend.growth_rate > 0 ? '+' : ''}
                      {processTrend.growth_rate}%
                    </div>
                  </div>
                )}
              </div>

              {processTrend.trend && processTrend.trend.length > 0 && (
                <div className="trend-chart-section">
                  <h4>月次推移（過去6ヶ月）</h4>
                  <div className="trend-chart">
                    {processTrend.trend.map((monthData, index) => (
                      <div key={index} className="trend-bar-wrapper">
                        <div className="trend-month">{monthData.month}</div>
                        <div className="trend-bar-container">
                          <div
                            className="trend-bar"
                            style={{
                              width: `${Math.min((monthData.score / 150) * 100, 100)}%`,
                              backgroundColor: getSkillLevelColor(
                                monthData.score >= 110
                                  ? 'ADVANCED'
                                  : monthData.score >= 105
                                  ? 'PROFICIENT'
                                  : monthData.score >= 95
                                  ? 'COMPETENT'
                                  : monthData.score >= 90
                                  ? 'DEVELOPING'
                                  : 'FOUNDATIONAL'
                              ),
                            }}
                          >
                            <span className="trend-score">{monthData.score}点</span>
                          </div>
                        </div>
                        <div className="trend-task-count">
                          <small>{monthData.task_count}件</small>
                        </div>
                      </div>
                    ))}
                  </div>
                  <div className="trend-legend">
                    <div className="legend-item">
                      <span className="legend-marker" style={{ backgroundColor: '#4caf50' }}></span>
                      <span>110点以上（高度）</span>
                    </div>
                    <div className="legend-item">
                      <span className="legend-marker" style={{ backgroundColor: '#2196f3' }}></span>
                      <span>105-109点（熟練）</span>
                    </div>
                    <div className="legend-item">
                      <span className="legend-marker" style={{ backgroundColor: '#ff9800' }}></span>
                      <span>95-104点（標準）</span>
                    </div>
                    <div className="legend-item">
                      <span className="legend-marker" style={{ backgroundColor: '#ff5722' }}></span>
                      <span>90-94点（育成）</span>
                    </div>
                    <div className="legend-item">
                      <span className="legend-marker" style={{ backgroundColor: '#9e9e9e' }}></span>
                      <span>90点未満（基礎）</span>
                    </div>
                  </div>
                </div>
              )}
            </>
          )}
        </div>
      )}
    </div>
  );
};

export default WorkerPerformanceDetail;
