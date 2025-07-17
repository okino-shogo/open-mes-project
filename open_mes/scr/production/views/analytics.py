from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Avg, Count, Sum, F, Case, When, Value, FloatField, Q
from django.db.models.functions import Extract, TruncDate
from django.utils import timezone
from datetime import datetime, timedelta

from ..models import ProductionPlan, WorkProgress
from ..serializers_analytics import (
    ProcessDurationAnalyticsSerializer,
    PlanVsActualAnalyticsSerializer,
    WorkerProductivityAnalyticsSerializer,
    DashboardSummarySerializer,
    ProcessTrendSerializer
)


class ProductionAnalyticsViewSet(viewsets.ViewSet):
    """
    生産性分析用API ViewSet
    """

    @action(detail=False, methods=['get'])
    def process_duration(self, request):
        """
        工程別所要時間分析
        各工程の平均所要時間、最小/最大時間、完了率を分析
        """
        try:
            # クエリパラメータ
            days = int(request.query_params.get('days', 30))
            cutoff_date = timezone.now() - timedelta(days=days)
            
            # 工程リスト
            processes = [
                'slit', 'cut', 'base_material_cut', 'molder', 
                'v_cut_lapping', 'post_processing', 'packing',
                'decorative_board', 'decorative_board_cut'
            ]
            
            # 工程名マッピング
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
            
            analytics_data = []
            
            for process in processes:
                # 工程の統計データを計算
                duration_field = f'{process}_duration_minutes'
                status_field = f'{process}_status'
                
                # 基本フィルタ: 更新日が指定期間内
                base_filter = Q(updated_at__gte=cutoff_date)
                
                # 所要時間データがある計画
                duration_data = ProductionPlan.objects.filter(
                    base_filter & Q(**{f'{duration_field}__isnull': False})
                ).values_list(duration_field, flat=True)
                
                # 完了した計画の数
                completed_count = ProductionPlan.objects.filter(
                    base_filter & Q(**{status_field: '完了'})
                ).count()
                
                # 全体の計画数（この工程に関わる）
                total_count = ProductionPlan.objects.filter(
                    base_filter & ~Q(**{status_field: '未着手'})
                ).count()
                
                if duration_data:
                    durations = list(duration_data)
                    avg_duration = sum(durations) / len(durations)
                    min_duration = min(durations)
                    max_duration = max(durations)
                else:
                    avg_duration = 0
                    min_duration = 0
                    max_duration = 0
                
                completion_rate = (completed_count / total_count * 100) if total_count > 0 else 0
                
                analytics_data.append({
                    'process_name': process_names.get(process, process),
                    'avg_duration': round(avg_duration, 1),
                    'min_duration': min_duration,
                    'max_duration': max_duration,
                    'total_plans': total_count,
                    'completion_rate': round(completion_rate, 1)
                })
            
            serializer = ProcessDurationAnalyticsSerializer(analytics_data, many=True)
            return Response(serializer.data)
            
        except Exception as e:
            return Response(
                {'error': f'工程別所要時間分析でエラーが発生しました: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'])
    def plan_vs_actual(self, request):
        """
        予実差分析
        計画と実績の差分を分析
        """
        try:
            # クエリパラメータ
            days = int(request.query_params.get('days', 30))
            cutoff_date = timezone.now() - timedelta(days=days)
            
            # 完了した計画のみを対象
            completed_plans = ProductionPlan.objects.filter(
                updated_at__gte=cutoff_date,
                actual_start_datetime__isnull=False,
                actual_end_datetime__isnull=False
            )
            
            analytics_data = []
            
            for plan in completed_plans:
                # 計画時間と実績時間を計算
                planned_duration = (plan.planned_end_datetime - plan.planned_start_datetime).total_seconds() / 3600
                actual_duration = (plan.actual_end_datetime - plan.actual_start_datetime).total_seconds() / 3600
                
                variance_hours = actual_duration - planned_duration
                variance_percentage = (variance_hours / planned_duration * 100) if planned_duration > 0 else 0
                
                analytics_data.append({
                    'plan_name': plan.plan_name,
                    'planned_duration_hours': round(planned_duration, 2),
                    'actual_duration_hours': round(actual_duration, 2),
                    'variance_hours': round(variance_hours, 2),
                    'variance_percentage': round(variance_percentage, 1),
                    'status': plan.get_status_display(),
                    'planned_start': plan.planned_start_datetime,
                    'actual_start': plan.actual_start_datetime,
                    'planned_end': plan.planned_end_datetime,
                    'actual_end': plan.actual_end_datetime
                })
            
            serializer = PlanVsActualAnalyticsSerializer(analytics_data, many=True)
            return Response(serializer.data)
            
        except Exception as e:
            return Response(
                {'error': f'予実差分析でエラーが発生しました: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'])
    def worker_productivity(self, request):
        """
        作業者別生産性分析
        作業者ごとの完了タスク数、平均完了時間、効率スコアを分析
        """
        try:
            # クエリパラメータ
            days = int(request.query_params.get('days', 30))
            cutoff_date = timezone.now() - timedelta(days=days)
            
            # WorkProgressモデルから作業者別データを集計
            worker_stats = WorkProgress.objects.filter(
                updated_at__gte=cutoff_date,
                operator__isnull=False,
                status='COMPLETED'
            ).values(
                'operator__username'
            ).annotate(
                completed_tasks=Count('id'),
                avg_completion_time=Avg(
                    Case(
                        When(
                            start_datetime__isnull=False,
                            end_datetime__isnull=False,
                            then=Value(1.0)  # 仮の値、実際の計算は後で処理
                        ),
                        default=Value(0),
                        output_field=FloatField()
                    )
                )
            ).order_by('-completed_tasks')
            
            analytics_data = []
            
            for worker_stat in worker_stats:
                worker_name = worker_stat['operator__username']
                completed_tasks = worker_stat['completed_tasks']
                
                # 実際の平均完了時間を計算
                worker_progress = WorkProgress.objects.filter(
                    operator__username=worker_name,
                    updated_at__gte=cutoff_date,
                    status='COMPLETED',
                    start_datetime__isnull=False,
                    end_datetime__isnull=False
                )
                
                if worker_progress.exists():
                    total_hours = 0
                    count = 0
                    for progress in worker_progress:
                        duration = (progress.end_datetime - progress.start_datetime).total_seconds() / 3600.0
                        total_hours += duration
                        count += 1
                    avg_completion_time = total_hours / count if count > 0 else 0
                else:
                    avg_completion_time = 0
                
                # 効率スコア計算（完了タスク数 / 平均完了時間）
                efficiency_score = (completed_tasks / avg_completion_time) if avg_completion_time > 0 else completed_tasks
                
                # 品質スコア（仮想的な計算 - 実際の品質データがある場合は置き換え）
                quality_score = max(85, min(100, 95 - (avg_completion_time * 2)))
                
                # よく担当する工程
                favorite_processes = list(
                    WorkProgress.objects.filter(
                        operator__username=worker_name,
                        updated_at__gte=cutoff_date
                    ).values_list(
                        'process_step', flat=True
                    ).distinct()[:3]
                )
                
                analytics_data.append({
                    'worker_name': worker_name,
                    'total_completed_tasks': completed_tasks,
                    'avg_completion_time_hours': round(avg_completion_time, 2),
                    'efficiency_score': round(efficiency_score, 2),
                    'quality_score': round(quality_score, 1),
                    'favorite_processes': favorite_processes
                })
            
            serializer = WorkerProductivityAnalyticsSerializer(analytics_data, many=True)
            return Response(serializer.data)
            
        except Exception as e:
            return Response(
                {'error': f'作業者別生産性分析でエラーが発生しました: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'])
    def dashboard_summary(self, request):
        """
        ダッシュボードサマリー
        全体的な生産状況のサマリーデータ
        """
        try:
            # クエリパラメータ
            days = int(request.query_params.get('days', 30))
            cutoff_date = timezone.now() - timedelta(days=days)
            
            # 基本統計
            total_plans = ProductionPlan.objects.filter(created_at__gte=cutoff_date).count()
            completed_plans = ProductionPlan.objects.filter(
                created_at__gte=cutoff_date,
                status='COMPLETED'
            ).count()
            in_progress_plans = ProductionPlan.objects.filter(
                created_at__gte=cutoff_date,
                status='IN_PROGRESS'
            ).count()
            
            # 遅延計画（予定終了日を過ぎているが未完了）
            delayed_plans = ProductionPlan.objects.filter(
                created_at__gte=cutoff_date,
                planned_end_datetime__lt=timezone.now(),
                status__in=['PENDING', 'IN_PROGRESS']
            ).count()
            
            # 完了率
            avg_completion_rate = (completed_plans / total_plans * 100) if total_plans > 0 else 0
            
            # 納期内完了率（実績終了日が計画終了日以内）
            on_time_completed = ProductionPlan.objects.filter(
                created_at__gte=cutoff_date,
                status='COMPLETED',
                actual_end_datetime__lte=F('planned_end_datetime')
            ).count()
            on_time_delivery_rate = (on_time_completed / completed_plans * 100) if completed_plans > 0 else 0
            
            summary_data = {
                'total_plans': total_plans,
                'completed_plans': completed_plans,
                'in_progress_plans': in_progress_plans,
                'delayed_plans': delayed_plans,
                'avg_completion_rate': round(avg_completion_rate, 1),
                'on_time_delivery_rate': round(on_time_delivery_rate, 1)
            }
            
            serializer = DashboardSummarySerializer(summary_data)
            return Response(serializer.data)
            
        except Exception as e:
            return Response(
                {'error': f'ダッシュボードサマリーでエラーが発生しました: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'])
    def process_trend(self, request):
        """
        工程別トレンド分析
        日別の工程パフォーマンス推移
        """
        try:
            # クエリパラメータ
            days = int(request.query_params.get('days', 14))  # デフォルト2週間
            process_type = request.query_params.get('process', 'slit')
            cutoff_date = timezone.now() - timedelta(days=days)
            
            # 工程名マッピング
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
            
            # 日別トレンドデータ
            duration_field = f'{process_type}_duration_minutes'
            status_field = f'{process_type}_status'
            
            # 日別の平均所要時間と完了数を集計
            daily_stats = ProductionPlan.objects.filter(
                updated_at__gte=cutoff_date
            ).annotate(
                date=TruncDate('updated_at')
            ).values('date').annotate(
                avg_duration=Avg(
                    Case(
                        When(**{f'{duration_field}__isnull': False}, then=F(duration_field)),
                        default=Value(0),
                        output_field=FloatField()
                    )
                ),
                completed_count=Count(
                    Case(
                        When(**{status_field: '完了'}, then=1),
                        default=None
                    )
                )
            ).order_by('date')
            
            analytics_data = []
            process_name = process_names.get(process_type, process_type)
            
            for stat in daily_stats:
                analytics_data.append({
                    'date': stat['date'],
                    'process_name': process_name,
                    'avg_duration': round(stat['avg_duration'] or 0, 1),
                    'completed_count': stat['completed_count']
                })
            
            serializer = ProcessTrendSerializer(analytics_data, many=True)
            return Response(serializer.data)
            
        except Exception as e:
            return Response(
                {'error': f'工程別トレンド分析でエラーが発生しました: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )