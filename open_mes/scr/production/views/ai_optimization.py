"""
AI最適化機能のAPI View
作業者パフォーマンス分析、最適化推薦などのAPI
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q
from django.utils import timezone
from datetime import datetime, timedelta

from ..ai_worker_analyzer import WorkerSkillAnalyzer, WorkerOptimizationEngine
# from ..worker_skill_models import (
#     WorkerSkillProfile, 
#     WorkerPerformanceHistory, 
#     WorkerOptimizationRecommendation
# )
from users.models import CustomUser
from rest_framework import serializers


class WorkerAnalysisSerializer(serializers.Serializer):
    """作業者分析結果のシリアライザー"""
    worker_info = serializers.JSONField()
    analysis_period = serializers.JSONField()
    basic_stats = serializers.JSONField()
    process_analysis = serializers.JSONField()
    learning_progress = serializers.JSONField()
    overall_assessment = serializers.JSONField()
    improvement_suggestions = serializers.JSONField()
    analysis_timestamp = serializers.DateTimeField()


# class WorkerOptimizationRecommendationSerializer(serializers.ModelSerializer):
#     """作業者最適化推薦のシリアライザー"""
#     worker_name = serializers.CharField(source='worker.username', read_only=True)
#     target_process_name = serializers.CharField(source='get_target_process_display', read_only=True)
#     priority_display = serializers.CharField(source='get_priority_display', read_only=True)
#     recommendation_type_display = serializers.CharField(source='get_recommendation_type_display', read_only=True)
#     
#     class Meta:
#         model = WorkerOptimizationRecommendation
#         fields = [
#             'id', 'worker_name', 'recommendation_type', 'recommendation_type_display',
#             'priority', 'priority_display', 'title', 'description', 'target_process',
#             'target_process_name', 'confidence_score', 'expected_improvement',
#             'is_implemented', 'created_at', 'expires_at'
#         ]


class WorkerListSerializer(serializers.ModelSerializer):
    """作業者一覧のシリアライザー"""
    full_name = serializers.CharField(source='get_full_name', read_only=True)
    
    class Meta:
        model = CustomUser
        fields = ['id', 'username', 'full_name', 'first_name', 'last_name']


class AIOptimizationViewSet(viewsets.ViewSet):
    """
    AI最適化機能のViewSet
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.analyzer = WorkerSkillAnalyzer()
        self.optimizer = WorkerOptimizationEngine()
    
    @action(detail=False, methods=['get'])
    def worker_list(self, request):
        """
        作業者一覧取得（登録ユーザー + 作業者インターフェースで使用されている作業者ID）
        """
        try:
            from production.models import ProductionPlan
            
            # 登録ユーザー
            workers = CustomUser.objects.filter(is_active=True)
            worker_data = []
            
            # 登録ユーザーをリストに追加
            for worker in workers:
                worker_data.append({
                    'id': str(worker.id),
                    'username': worker.username,
                    'full_name': worker.get_full_name() or worker.username,
                    'type': 'registered_user'
                })
            
            # 作業者インターフェースで使用されている作業者ID
            worker_id_fields = [
                'slit_worker_id', 'cut_worker_id', 'base_material_cut_worker_id',
                'molder_worker_id', 'v_cut_lapping_worker_id', 'post_processing_worker_id',
                'packing_worker_id', 'decorative_board_worker_id', 'decorative_board_cut_worker_id'
            ]
            
            interface_worker_ids = set()
            for field in worker_id_fields:
                worker_ids = ProductionPlan.objects.exclude(**{f'{field}__isnull': True}).values_list(field, flat=True).distinct()
                for worker_id in worker_ids:
                    if worker_id and worker_id.strip():
                        interface_worker_ids.add(worker_id.strip())
            
            # 作業者インターフェースのIDをリストに追加（既存ユーザーIDと重複しないもの）
            existing_user_ids = {str(worker.id) for worker in workers}
            existing_usernames = {worker.username for worker in workers}
            
            for worker_id in interface_worker_ids:
                if worker_id not in existing_user_ids and worker_id not in existing_usernames:
                    worker_data.append({
                        'id': worker_id,
                        'username': worker_id,
                        'full_name': worker_id,
                        'type': 'interface_worker'
                    })
            
            return Response(worker_data)
            
        except Exception as e:
            return Response(
                {'error': f'作業者一覧取得エラー: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['get'])
    def worker_analysis(self, request, pk=None):
        """
        作業者個人分析
        GET /api/ai-optimization/{worker_id}/worker_analysis/?days=30
        """
        try:
            days = int(request.query_params.get('days', 30))
            
            # AI分析実行（作業者存在確認は分析エンジン内で実行）
            analysis_result = self.analyzer.analyze_worker_performance(
                worker_id=pk,
                days=days
            )
            
            if 'error' in analysis_result:
                return Response(
                    analysis_result,
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # レスポンス返却
            return Response(analysis_result)
            
        except ValueError:
            return Response(
                {'error': 'daysパラメータは整数で指定してください'},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {'error': f'作業者分析エラー: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'])
    def team_performance_summary(self, request):
        """
        チーム全体のパフォーマンス概要
        """
        try:
            days = int(request.query_params.get('days', 30))
            
            # アクティブな作業者を取得
            workers = CustomUser.objects.filter(is_active=True)
            
            team_summary = {
                'analysis_period': {
                    'days': days,
                    'end_date': timezone.now().isoformat()
                },
                'team_stats': {
                    'total_workers': workers.count(),
                    'analyzed_workers': 0,
                    'avg_skill_level': 0,
                    'top_performers': [],
                    'improvement_candidates': []
                },
                'process_coverage': {},
                'team_recommendations': []
            }
            
            # 各作業者の分析
            worker_analyses = []
            for worker in workers[:10]:  # 最大10人まで分析
                analysis = self.analyzer.analyze_worker_performance(
                    worker_id=str(worker.id),
                    days=days
                )
                
                if 'error' not in analysis:
                    worker_analyses.append(analysis)
                    team_summary['team_stats']['analyzed_workers'] += 1
            
            # チーム統計計算
            if worker_analyses:
                # 平均スキルレベル
                skill_scores = [a['overall_assessment']['overall_score'] for a in worker_analyses]
                team_summary['team_stats']['avg_skill_level'] = sum(skill_scores) / len(skill_scores)
                
                # トップパフォーマー
                top_performers = sorted(
                    worker_analyses, 
                    key=lambda x: x['overall_assessment']['overall_score'], 
                    reverse=True
                )[:3]
                
                team_summary['team_stats']['top_performers'] = [
                    {
                        'worker_name': a['worker_info']['username'],
                        'overall_score': a['overall_assessment']['overall_score'],
                        'skill_level': a['overall_assessment']['skill_level'],
                        'best_processes': a['overall_assessment']['best_processes']
                    }
                    for a in top_performers
                ]
                
                # 改善候補
                improvement_candidates = [
                    a for a in worker_analyses 
                    if a['overall_assessment']['overall_score'] < 60
                ]
                
                team_summary['team_stats']['improvement_candidates'] = [
                    {
                        'worker_name': a['worker_info']['username'],
                        'overall_score': a['overall_assessment']['overall_score'],
                        'weak_processes': a['overall_assessment']['weak_processes'],
                        'improvement_suggestions': len(a['improvement_suggestions'])
                    }
                    for a in improvement_candidates
                ]
            
            return Response(team_summary)
            
        except Exception as e:
            return Response(
                {'error': f'チーム分析エラー: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'])
    def optimization_recommendations(self, request):
        """
        最適化推薦一覧
        """
        try:
            # 現在はモックデータを返す
            mock_recommendations = [
                {
                    'id': 1,
                    'worker_name': 'test',
                    'recommendation_type': 'improvement',
                    'priority': 'medium',
                    'title': 'モルダー工程の改善',
                    'description': 'モルダー工程のパフォーマンスが平均を下回っています。',
                    'target_process': 'molder',
                    'confidence_score': 85.0,
                    'expected_improvement': 16.0,
                    'created_at': timezone.now().isoformat()
                },
                {
                    'id': 2,
                    'worker_name': 'test',
                    'recommendation_type': 'training',
                    'priority': 'medium',
                    'title': 'Vカットラッピング工程の集中トレーニング',
                    'description': 'Vカットラッピング工程で学習効果が見られます。',
                    'target_process': 'v_cut_lapping',
                    'confidence_score': 90.0,
                    'expected_improvement': 18.0,
                    'created_at': timezone.now().isoformat()
                }
            ]
            
            return Response(mock_recommendations)
            
        except Exception as e:
            return Response(
                {'error': f'推薦一覧取得エラー: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['post'])
    def generate_recommendations(self, request):
        """
        作業者向け推薦生成
        """
        try:
            worker_id = request.data.get('worker_id')
            days = int(request.data.get('days', 30))
            
            if not worker_id:
                return Response(
                    {'error': 'worker_idが必要です'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # 作業者分析実行
            analysis_result = self.analyzer.analyze_worker_performance(
                worker_id=worker_id,
                days=days
            )
            
            if 'error' in analysis_result:
                return Response(
                    analysis_result,
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # 推薦をモックデータとして返す（データベース保存は今後実装）
            mock_recommendations = []
            
            for i, suggestion in enumerate(analysis_result['improvement_suggestions']):
                mock_recommendations.append({
                    'id': i + 1,
                    'worker_name': analysis_result['worker_info']['username'],
                    'recommendation_type': suggestion['type'],
                    'priority': suggestion['priority'],
                    'title': suggestion['title'],
                    'description': suggestion['description'],
                    'target_process': suggestion.get('target_process'),
                    'confidence_score': 85.0,
                    'expected_improvement': suggestion.get('expected_improvement', '0%'),
                    'created_at': timezone.now().isoformat()
                })
            
            return Response({
                'message': f'{len(mock_recommendations)}件の推薦を生成しました',
                'recommendations': mock_recommendations,
                'analysis_summary': {
                    'worker_name': analysis_result['worker_info']['username'],
                    'overall_score': analysis_result['overall_assessment']['overall_score'],
                    'skill_level': analysis_result['overall_assessment']['skill_level'],
                    'total_suggestions': len(analysis_result['improvement_suggestions'])
                }
            })
            
        except CustomUser.DoesNotExist:
            return Response(
                {'error': f'作業者ID {worker_id} が見つかりません'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {'error': f'推薦生成エラー: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'])
    def process_skill_matrix(self, request):
        """
        工程別スキルマトリックス
        各工程に対する作業者のスキルレベルを一覧表示
        """
        try:
            days = int(request.query_params.get('days', 30))
            
            # 作業者一覧取得
            workers = CustomUser.objects.filter(is_active=True)
            
            # 工程一覧
            processes = [
                'slit', 'cut', 'base_material_cut', 'molder', 
                'v_cut_lapping', 'post_processing', 'packing',
                'decorative_board', 'decorative_board_cut'
            ]
            
            process_names = {
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
            
            # スキルマトリックス構築
            skill_matrix = []
            
            for worker in workers:
                # 作業者分析
                analysis = self.analyzer.analyze_worker_performance(
                    worker_id=str(worker.id),
                    days=days
                )
                
                if 'error' not in analysis:
                    worker_skills = {
                        'worker_id': str(worker.id),
                        'worker_name': worker.username,
                        'full_name': worker.get_full_name(),
                        'overall_score': analysis['overall_assessment']['overall_score'],
                        'skill_level': analysis['overall_assessment']['skill_level'],
                        'processes': {}
                    }
                    
                    # 各工程のスキルレベル
                    for process in processes:
                        if process in analysis['process_analysis']:
                            process_data = analysis['process_analysis'][process]
                            if process_data['personal_data']['task_count'] > 0:
                                worker_skills['processes'][process] = {
                                    'name': process_names[process],
                                    'score': process_data['performance_rating']['overall_score'],
                                    'rating': process_data['performance_rating']['rating'],
                                    'task_count': process_data['personal_data']['task_count'],
                                    'avg_time': process_data['personal_data']['avg_time'],
                                    'has_experience': True
                                }
                            else:
                                worker_skills['processes'][process] = {
                                    'name': process_names[process],
                                    'score': 0,
                                    'rating': '未経験',
                                    'task_count': 0,
                                    'avg_time': 0,
                                    'has_experience': False
                                }
                        else:
                            worker_skills['processes'][process] = {
                                'name': process_names[process],
                                'score': 0,
                                'rating': '未経験',
                                'task_count': 0,
                                'avg_time': 0,
                                'has_experience': False
                            }
                    
                    skill_matrix.append(worker_skills)
            
            # 工程別統計
            process_stats = {}
            for process in processes:
                scores = []
                experienced_count = 0
                
                for worker in skill_matrix:
                    if worker['processes'][process]['has_experience']:
                        scores.append(worker['processes'][process]['score'])
                        experienced_count += 1
                
                process_stats[process] = {
                    'name': process_names[process],
                    'experienced_workers': experienced_count,
                    'avg_score': sum(scores) / len(scores) if scores else 0,
                    'coverage_rate': (experienced_count / len(skill_matrix)) * 100 if skill_matrix else 0
                }
            
            return Response({
                'skill_matrix': skill_matrix,
                'process_stats': process_stats,
                'summary': {
                    'total_workers': len(skill_matrix),
                    'analysis_period_days': days,
                    'analysis_timestamp': timezone.now().isoformat()
                }
            })
            
        except Exception as e:
            return Response(
                {'error': f'スキルマトリックス取得エラー: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )