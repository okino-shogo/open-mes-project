"""
AI作業者分析エンジン
作業者パフォーマンスの分析、スキル評価、最適化推薦を行う
"""

import statistics
import math
from datetime import datetime, timedelta
from django.utils import timezone
from django.db.models import Q, Avg, Count, Sum, StdDev, Min, Max
from django.db.models.functions import Extract
from collections import defaultdict
from typing import Dict, List, Tuple, Optional
import json

from .models import ProductionPlan, WorkProgress
# from .worker_skill_models import (
#     WorkerSkillProfile, 
#     WorkerPerformanceHistory, 
#     WorkerOptimizationRecommendation
# )
from users.models import CustomUser


class WorkerSkillAnalyzer:
    """
    作業者スキル分析エンジン
    個人のパフォーマンスデータから習熟度、適性を分析
    """
    
    def __init__(self):
        self.process_types = [
            'slit', 'cut', 'base_material_cut', 'molder', 
            'v_cut_lapping', 'post_processing', 'packing',
            'decorative_board', 'decorative_board_cut'
        ]
        
        self.process_names = {
            'slit': 'スリット',
            'cut': 'カット',
            'base_material_cut': '基材カット',
            'molder': 'モルダー',
            'v_cut_lapping': 'Vカットラッピング',
            'post_processing': '後加工',
            'packing': '梱包',
            'decorative_board': '化粧板貼付',
            'decorative_board_cut': '化粧板カット'
        }
    
    def analyze_worker_performance(self, worker_id: str, days: int = 30) -> Dict:
        """
        作業者の個人パフォーマンスを分析
        worker_id: CustomUserのIDまたは作業者インターフェースで入力される作業者ID文字列
        """
        try:
            # まずUUIDとして試行、失敗したら作業者ID文字列として扱う
            worker = None
            worker_identifier = worker_id
            worker_name = worker_id
            
            try:
                import uuid
                # UUIDかどうかチェック
                uuid.UUID(worker_id)
                # UUIDとしてCustomUserを検索
                worker = CustomUser.objects.get(id=worker_id)
                worker_identifier = str(worker.id)
                worker_name = worker.get_full_name() or worker.username
            except (CustomUser.DoesNotExist, ValueError):
                # 作業者ID文字列として処理
                worker_identifier = worker_id
                worker_name = worker_id
                
            cutoff_date = timezone.now() - timedelta(days=days)
            
            # 基本統計データ収集
            worker_data = self._collect_worker_data(worker_identifier, cutoff_date)
            
            # 工程別分析
            process_analysis = self._analyze_process_performance(worker_identifier, cutoff_date)
            
            # 習熟度分析
            learning_analysis = self._analyze_learning_progress(worker_identifier, cutoff_date)
            
            # 総合評価
            overall_assessment = self._calculate_overall_assessment(worker_data, process_analysis)
            
            # 改善提案生成
            improvement_suggestions = self._generate_improvement_suggestions(
                worker_identifier, process_analysis, learning_analysis
            )
            
            return {
                'worker_info': {
                    'id': worker_identifier,
                    'username': worker_name,
                    'full_name': worker_name,
                },
                'analysis_period': {
                    'start_date': cutoff_date.isoformat(),
                    'end_date': timezone.now().isoformat(),
                    'days': days
                },
                'basic_stats': worker_data,
                'process_analysis': process_analysis,
                'learning_progress': learning_analysis,
                'overall_assessment': overall_assessment,
                'improvement_suggestions': improvement_suggestions,
                'analysis_timestamp': timezone.now().isoformat()
            }
            
        except Exception as e:
            return {'error': f'分析エラー: {str(e)}'}
    
    def _collect_worker_data(self, worker_identifier: str, cutoff_date: datetime) -> Dict:
        """作業者の基本データを収集"""
        
        # 各工程の実績データを収集
        process_data = {}
        total_tasks = 0
        total_time = 0
        
        for process in self.process_types:
            duration_field = f'{process}_duration_minutes'
            status_field = f'{process}_status'
            worker_id_field = f'{process}_worker_id'
            start_field = f'{process}_start_time'
            completion_field = f'{process}_completion_time'
            
            # 完了したタスクのデータを取得（作業者IDで絞り込み）
            filter_criteria = {
                'updated_at__gte': cutoff_date,
                status_field: '完了',
                f'{duration_field}__isnull': False,
                f'{duration_field}__gt': 0,  # 0分より大きい（0分のデータを除外）
                worker_id_field: worker_identifier  # 作業者IDで絞り込み
            }
            
            completed_plans = ProductionPlan.objects.filter(**filter_criteria)
            
            if completed_plans.exists():
                durations = [getattr(plan, duration_field) for plan in completed_plans]
                
                process_data[process] = {
                    'name': self.process_names[process],
                    'task_count': len(durations),
                    'total_time': sum(durations),
                    'avg_time': statistics.mean(durations),
                    'min_time': min(durations),
                    'max_time': max(durations),
                    'std_dev': statistics.stdev(durations) if len(durations) > 1 else 0,
                    'efficiency_score': self._calculate_efficiency_score(durations, process)
                }
                
                total_tasks += len(durations)
                total_time += sum(durations)
        
        return {
            'total_tasks_completed': total_tasks,
            'total_work_time_minutes': total_time,
            'average_task_time': total_time / total_tasks if total_tasks > 0 else 0,
            'process_data': process_data,
            'analysis_date': timezone.now().isoformat(),
            'note': f'作業者 {worker_identifier} の個別分析データ'
        }
    
    def _analyze_process_performance(self, worker_identifier: str, cutoff_date: datetime) -> Dict:
        """工程別パフォーマンス分析"""
        
        process_performance = {}
        
        for process in self.process_types:
            # 個人データ
            personal_data = self._get_personal_process_data(worker_identifier, process, cutoff_date)
            
            # 全体平均との比較
            benchmark_data = self._get_benchmark_data(process, cutoff_date)
            
            # パフォーマンス評価
            performance_rating = self._calculate_performance_rating(
                personal_data, benchmark_data
            )
            
            process_performance[process] = {
                'name': self.process_names[process],
                'personal_data': personal_data,
                'benchmark_data': benchmark_data,
                'performance_rating': performance_rating,
                'recommendations': self._generate_process_recommendations(
                    process, personal_data, benchmark_data
                )
            }
        
        return process_performance
    
    def _analyze_learning_progress(self, worker_identifier: str, cutoff_date: datetime) -> Dict:
        """学習進捗・習熟度分析"""
        
        learning_data = {}
        
        for process in self.process_types:
            # 時系列データ取得
            time_series_data = self._get_time_series_data(worker_identifier, process, cutoff_date)
            
            if len(time_series_data) >= 3:  # 最低3データポイント必要
                # 習熟曲線分析
                learning_curve = self._analyze_learning_curve(time_series_data)
                
                # 改善トレンド
                improvement_trend = self._calculate_improvement_trend(time_series_data)
                
                learning_data[process] = {
                    'name': self.process_names[process],
                    'data_points': len(time_series_data),
                    'learning_curve': learning_curve,
                    'improvement_trend': improvement_trend,
                    'proficiency_level': self._assess_proficiency_level(learning_curve),
                    'next_milestone': self._predict_next_milestone(learning_curve)
                }
        
        return learning_data
    
    def _calculate_overall_assessment(self, worker_data: Dict, process_analysis: Dict) -> Dict:
        """総合評価の計算"""
        
        # 各工程の得点を計算
        process_scores = []
        best_processes = []
        weak_processes = []
        
        for process, data in process_analysis.items():
            if data['personal_data']['task_count'] > 0:
                score = data['performance_rating']['overall_score']
                process_scores.append(score)
                
                if score >= 80:
                    best_processes.append({
                        'process': process,
                        'name': data['name'],
                        'score': score
                    })
                elif score <= 60:
                    weak_processes.append({
                        'process': process,
                        'name': data['name'],
                        'score': score
                    })
        
        # 総合スコア
        overall_score = statistics.mean(process_scores) if process_scores else 0
        
        # スキルレベル判定
        skill_level = self._determine_skill_level(overall_score, len(process_scores))
        
        return {
            'overall_score': round(overall_score, 1),
            'skill_level': skill_level,
            'processes_analyzed': len(process_scores),
            'best_processes': sorted(best_processes, key=lambda x: x['score'], reverse=True)[:3],
            'weak_processes': sorted(weak_processes, key=lambda x: x['score'])[:3],
            'versatility_score': self._calculate_versatility_score(process_analysis),
            'consistency_score': self._calculate_consistency_score(process_scores)
        }
    
    def _generate_improvement_suggestions(self, worker_identifier: str, process_analysis: Dict, learning_analysis: Dict) -> List[Dict]:
        """改善提案の生成"""
        
        suggestions = []
        
        # 弱い工程の特定と改善提案
        for process, data in process_analysis.items():
            if data['personal_data']['task_count'] > 0:
                score = data['performance_rating']['overall_score']
                
                if score < 70:
                    suggestions.append({
                        'type': 'improvement',
                        'priority': 'high' if score < 50 else 'medium',
                        'title': f'{data["name"]}工程の改善',
                        'description': f'{data["name"]}工程のパフォーマンスが平均を下回っています。',
                        'specific_actions': data['recommendations'],
                        'expected_improvement': f'{(80 - score):.1f}%',
                        'target_process': process
                    })
        
        # 学習効果の高い工程の推薦
        for process, data in learning_analysis.items():
            if data['improvement_trend']['is_improving']:
                suggestions.append({
                    'type': 'training',
                    'priority': 'medium',
                    'title': f'{data["name"]}工程の集中トレーニング',
                    'description': f'{data["name"]}工程で学習効果が見られます。集中的な訓練で更なる向上が期待できます。',
                    'specific_actions': [
                        f'現在の習熟度: {data["proficiency_level"]}',
                        f'次のマイルストーン: {data["next_milestone"]}'
                    ],
                    'expected_improvement': f'{data["improvement_trend"]["improvement_rate"]:.1f}%',
                    'target_process': process
                })
        
        return suggestions
    
    def _get_personal_process_data(self, worker_identifier: str, process: str, cutoff_date: datetime) -> Dict:
        """個人の工程データ取得"""
        
        duration_field = f'{process}_duration_minutes'
        status_field = f'{process}_status'
        worker_id_field = f'{process}_worker_id'
        
        filter_criteria = {
            'updated_at__gte': cutoff_date,
            status_field: '完了',
            f'{duration_field}__isnull': False,
            f'{duration_field}__gt': 0,  # 0分より大きい（0分のデータを除外）
            worker_id_field: worker_identifier  # 作業者IDで絞り込み
        }
        
        plans = ProductionPlan.objects.filter(**filter_criteria)
        
        if plans.exists():
            durations = [getattr(plan, duration_field) for plan in plans]
            return {
                'task_count': len(durations),
                'avg_time': statistics.mean(durations),
                'min_time': min(durations),
                'max_time': max(durations),
                'std_dev': statistics.stdev(durations) if len(durations) > 1 else 0,
                'total_time': sum(durations)
            }
        
        return {
            'task_count': 0,
            'avg_time': 0,
            'min_time': 0,
            'max_time': 0,
            'std_dev': 0,
            'total_time': 0
        }
    
    def _get_benchmark_data(self, process: str, cutoff_date: datetime) -> Dict:
        """ベンチマークデータ取得（全体平均）"""
        
        duration_field = f'{process}_duration_minutes'
        status_field = f'{process}_status'
        
        plans = ProductionPlan.objects.filter(
            updated_at__gte=cutoff_date,
            **{status_field: '完了', f'{duration_field}__isnull': False, f'{duration_field}__gt': 0}
        )
        
        if plans.exists():
            durations = [getattr(plan, duration_field) for plan in plans]
            return {
                'task_count': len(durations),
                'avg_time': statistics.mean(durations),
                'min_time': min(durations),
                'max_time': max(durations),
                'std_dev': statistics.stdev(durations) if len(durations) > 1 else 0
            }
        
        return {
            'task_count': 0,
            'avg_time': 0,
            'min_time': 0,
            'max_time': 0,
            'std_dev': 0
        }
    
    def _calculate_efficiency_score(self, durations: List[float], process: str) -> float:
        """効率スコア計算"""
        if not durations:
            return 0
        
        # 標準的な作業時間の設定（工程別）
        standard_times = {
            'slit': 90,
            'cut': 30,
            'base_material_cut': 45,
            'molder': 120,
            'v_cut_lapping': 60,
            'post_processing': 90,
            'packing': 30,
            'decorative_board': 180,
            'decorative_board_cut': 240
        }
        
        standard_time = standard_times.get(process, 60)
        avg_time = statistics.mean(durations)
        
        # 効率スコア = (標準時間 / 実際の時間) * 100
        if avg_time > 0:
            efficiency = (standard_time / avg_time) * 100
            # 100%を上限とする
            return min(efficiency, 100)
        else:
            return 0
    
    def _calculate_performance_rating(self, personal_data: Dict, benchmark_data: Dict) -> Dict:
        """パフォーマンス評価計算"""
        
        if personal_data['task_count'] == 0:
            return {
                'overall_score': 0,
                'speed_score': 0,
                'consistency_score': 0,
                'experience_score': 0,
                'rating': 'データなし'
            }
        
        # 速度スコア（平均時間の比較）
        if benchmark_data['avg_time'] > 0:
            speed_score = (benchmark_data['avg_time'] / personal_data['avg_time']) * 100
            speed_score = min(speed_score, 100)
        else:
            speed_score = 50
        
        # 一貫性スコア（標準偏差の比較）
        if personal_data['std_dev'] == 0:
            consistency_score = 100
        elif benchmark_data['std_dev'] > 0:
            consistency_score = max(0, 100 - (personal_data['std_dev'] / benchmark_data['std_dev']) * 50)
        else:
            consistency_score = 70
        
        # 経験スコア（タスク数）
        experience_score = min(personal_data['task_count'] * 10, 100)
        
        # 総合スコア
        overall_score = (speed_score * 0.4 + consistency_score * 0.3 + experience_score * 0.3)
        
        # 評価レベル
        if overall_score >= 80:
            rating = 'エキスパート'
        elif overall_score >= 70:
            rating = '熟練'
        elif overall_score >= 60:
            rating = '中級'
        elif overall_score >= 50:
            rating = '初級'
        else:
            rating = '要改善'
        
        return {
            'overall_score': round(overall_score, 1),
            'speed_score': round(speed_score, 1),
            'consistency_score': round(consistency_score, 1),
            'experience_score': round(experience_score, 1),
            'rating': rating
        }
    
    def _generate_process_recommendations(self, process: str, personal_data: Dict, benchmark_data: Dict) -> List[str]:
        """工程別推薦事項生成"""
        
        recommendations = []
        
        if personal_data['task_count'] == 0:
            recommendations.append(f'{self.process_names[process]}工程の経験を積む')
            return recommendations
        
        # 速度改善
        if benchmark_data['avg_time'] > 0 and personal_data['avg_time'] > benchmark_data['avg_time'] * 1.2:
            recommendations.append('作業速度の向上（標準手順の確認）')
        
        # 一貫性改善
        if personal_data['std_dev'] > benchmark_data['std_dev'] * 1.5:
            recommendations.append('作業の一貫性向上（品質管理の徹底）')
        
        # 経験積み上げ
        if personal_data['task_count'] < 10:
            recommendations.append('経験値の積み上げ（より多くのタスク経験）')
        
        return recommendations
    
    def _get_time_series_data(self, worker_identifier: str, process: str, cutoff_date: datetime) -> List[Dict]:
        """時系列データ取得"""
        
        duration_field = f'{process}_duration_minutes'
        status_field = f'{process}_status'
        completion_field = f'{process}_completion_time'
        worker_id_field = f'{process}_worker_id'
        
        filter_criteria = {
            'updated_at__gte': cutoff_date,
            status_field: '完了',
            f'{duration_field}__isnull': False,
            f'{duration_field}__gt': 0,  # 0分より大きい（0分のデータを除外）
            f'{completion_field}__isnull': False,
            worker_id_field: worker_identifier  # 作業者IDで絞り込み
        }
        
        plans = ProductionPlan.objects.filter(**filter_criteria).order_by(completion_field)
        
        time_series = []
        for plan in plans:
            time_series.append({
                'date': getattr(plan, completion_field),
                'duration': getattr(plan, duration_field),
                'plan_name': plan.plan_name
            })
        
        return time_series
    
    def _analyze_learning_curve(self, time_series_data: List[Dict]) -> Dict:
        """習熟曲線分析"""
        
        if len(time_series_data) < 3:
            return {'trend': 'insufficient_data', 'improvement_rate': 0}
        
        # 時系列順にソート
        sorted_data = sorted(time_series_data, key=lambda x: x['date'])
        durations = [item['duration'] for item in sorted_data]
        
        # 線形回帰による傾向分析
        n = len(durations)
        x = list(range(n))
        y = durations
        
        # 最小二乗法による傾き計算
        if n > 0:
            x_mean = sum(x) / n
            y_mean = sum(y) / n
            
            numerator = sum((x[i] - x_mean) * (y[i] - y_mean) for i in range(n))
            denominator = sum((x[i] - x_mean) ** 2 for i in range(n))
            
            slope = numerator / denominator if denominator != 0 else 0
        else:
            slope = 0
            y_mean = 0
        
        # 改善率計算
        if y_mean > 0:
            improvement_rate = abs(slope) / y_mean * 100
        else:
            improvement_rate = 0
        
        return {
            'trend': 'improving' if slope < 0 else 'declining' if slope > 0 else 'stable',
            'improvement_rate': round(improvement_rate, 2),
            'slope': round(slope, 2),
            'data_points': n
        }
    
    def _calculate_improvement_trend(self, time_series_data: List[Dict]) -> Dict:
        """改善トレンド計算"""
        
        if len(time_series_data) < 2:
            return {'is_improving': False, 'improvement_rate': 0}
        
        # 最初と最後の比較
        first_duration = time_series_data[0]['duration']
        last_duration = time_series_data[-1]['duration']
        
        if first_duration > 0:
            improvement_rate = ((first_duration - last_duration) / first_duration) * 100
        else:
            improvement_rate = 0
        
        return {
            'is_improving': improvement_rate > 0,
            'improvement_rate': round(improvement_rate, 2),
            'first_duration': first_duration,
            'last_duration': last_duration
        }
    
    def _assess_proficiency_level(self, learning_curve: Dict) -> str:
        """習熟度レベル評価"""
        
        if learning_curve['trend'] == 'insufficient_data':
            return '評価不可'
        
        improvement_rate = learning_curve['improvement_rate']
        
        if improvement_rate > 20:
            return '急速習熟中'
        elif improvement_rate > 10:
            return '習熟中'
        elif improvement_rate > 5:
            return '緩やか習熟'
        elif learning_curve['trend'] == 'stable':
            return '安定'
        else:
            return '要改善'
    
    def _predict_next_milestone(self, learning_curve: Dict) -> str:
        """次のマイルストーン予測"""
        
        if learning_curve['trend'] == 'improving':
            return '更なる効率向上が期待される'
        elif learning_curve['trend'] == 'stable':
            return '現在のレベルを維持'
        else:
            return '改善が必要'
    
    def _determine_skill_level(self, overall_score: float, processes_count: int) -> str:
        """スキルレベル判定"""
        
        if processes_count == 0:
            return '未評価'
        
        if overall_score >= 90:
            return 'エキスパート'
        elif overall_score >= 80:
            return '熟練者'
        elif overall_score >= 70:
            return '中級者'
        elif overall_score >= 60:
            return '初級者'
        else:
            return '要訓練'
    
    def _calculate_versatility_score(self, process_analysis: Dict) -> float:
        """汎用性スコア計算"""
        
        process_scores = []
        for process, data in process_analysis.items():
            if data['personal_data']['task_count'] > 0:
                process_scores.append(data['performance_rating']['overall_score'])
        
        if not process_scores:
            return 0
        
        # 汎用性 = 平均スコア * 対応工程数の係数
        if process_scores:
            avg_score = statistics.mean(process_scores)
            versatility_bonus = min(len(process_scores) * 0.1, 0.5)  # 最大50%のボーナス
            return round(avg_score * (1 + versatility_bonus), 1)
        else:
            return 0
    
    def _calculate_consistency_score(self, process_scores: List[float]) -> float:
        """一貫性スコア計算"""
        
        if len(process_scores) < 2:
            return 100 if process_scores else 0
        
        # 標準偏差が小さいほど一貫性が高い
        if len(process_scores) > 1:
            std_dev = statistics.stdev(process_scores)
            mean_score = statistics.mean(process_scores)
            
            if mean_score > 0:
                consistency = max(0, 100 - (std_dev / mean_score) * 100)
            else:
                consistency = 0
        else:
            consistency = 100 if process_scores else 0
        
        return round(consistency, 1)


class WorkerOptimizationEngine:
    """
    作業者配置最適化エンジン
    """
    
    def __init__(self):
        self.analyzer = WorkerSkillAnalyzer()
    
    def optimize_worker_assignment(self, production_plans: List[str], target_date: str = None) -> Dict:
        """
        作業者配置最適化
        """
        
        # 実装予定: 線形計画法による最適配置
        # 制約条件: 作業者の可用性、スキルレベル、工程要件
        # 目的関数: 総効率の最大化
        
        return {
            'optimization_result': 'この機能は次のリリースで実装予定です',
            'message': '現在、WorkerSkillAnalyzerが実装済みです'
        }
    
    def predict_production_capacity(self, workers: List[str], days: int = 7) -> Dict:
        """
        生産能力予測
        """
        
        # 実装予定: 作業者の過去データから未来の生産能力を予測
        
        return {
            'prediction_result': 'この機能は次のリリースで実装予定です',
            'message': '現在、WorkerSkillAnalyzerが実装済みです'
        }