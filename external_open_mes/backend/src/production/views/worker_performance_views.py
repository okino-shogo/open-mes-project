"""
Worker Performance API Views
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import get_user_model

from production.utils.worker_performance import (
    calculate_worker_score,
    determine_skill_level,
    get_skill_trend,
    get_worker_all_process_scores,
    VALID_PROCESSES,
)


class WorkerPerformanceView(APIView):
    """
    作業者パフォーマンスAPI

    GET /api/production/worker-performance/<worker_id>/
        全工程のスコアを取得

    GET /api/production/worker-performance/<worker_id>/<process>/
        特定工程のスコアと推移を取得
    """

    def get(self, request, worker_id, process=None):
        """
        作業者パフォーマンスデータを取得

        Args:
            request: リクエストオブジェクト
            worker_id (UUID): 作業者ID
            process (str, optional): 工程名

        Returns:
            Response: パフォーマンスデータ
        """
        User = get_user_model()

        # 作業者取得
        try:
            worker = User.objects.get(id=worker_id)
        except User.DoesNotExist:
            return Response(
                {
                    "success": False,
                    "error": "作業者が見つかりません",
                    "detail": f"ID: {worker_id}"
                },
                status=status.HTTP_404_NOT_FOUND
            )

        # 特定工程の詳細取得
        if process:
            # 工程名バリデーション
            if process not in VALID_PROCESSES:
                return Response(
                    {
                        "success": False,
                        "error": "無効な工程名",
                        "detail": f"工程: {process}",
                        "valid_processes": VALID_PROCESSES
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

            # スコア計算
            score_data = calculate_worker_score(worker, process)

            if score_data is None:
                return Response(
                    {
                        "success": False,
                        "error": "評価データ不足",
                        "detail": "過去30日間のタスクが5件未満、または有効なデータがありません",
                        "process": process
                    },
                    status=status.HTTP_200_OK  # データ不足はエラーではなく正常レスポンス
                )

            # 推移データ取得
            trend = get_skill_trend(worker, process, months=6)

            # 成長率計算
            growth_rate = None
            if len(trend) >= 2:
                oldest_score = trend[0]['score']
                latest_score = trend[-1]['score']
                if oldest_score > 0:
                    growth_rate = round(
                        ((latest_score - oldest_score) / oldest_score) * 100,
                        1
                    )

            return Response({
                "success": True,
                "data": {
                    "worker_id": str(worker.id),
                    "worker_name": worker.get_full_name() or worker.username,
                    "process": process,
                    "process_display": score_data.get('process_display', process),
                    "score": score_data['score'],
                    "skill_level": score_data['skill_level'],
                    "skill_level_display": score_data['skill_level_display'],
                    "task_count": score_data['task_count'],
                    "trend": trend,
                    "growth_rate": growth_rate,
                    "evaluation_period_days": 30
                }
            })

        # 全工程のスコア取得
        else:
            all_scores = get_worker_all_process_scores(worker)

            if not all_scores:
                return Response(
                    {
                        "success": False,
                        "error": "評価データなし",
                        "detail": "どの工程でも評価可能なデータがありません"
                    },
                    status=status.HTTP_200_OK
                )

            # 全工程の平均スコア計算
            average_score = sum(p['score'] for p in all_scores) / len(all_scores)
            primary_skill_level, primary_level_display = determine_skill_level(average_score)

            return Response({
                "success": True,
                "data": {
                    "worker_id": str(worker.id),
                    "worker_name": worker.get_full_name() or worker.username,
                    "process_skills": all_scores,
                    "summary": {
                        "average_score": round(average_score, 2),
                        "primary_skill_level": primary_skill_level,
                        "primary_skill_level_display": primary_level_display,
                        "total_processes": len(all_scores),
                        "total_tasks": sum(p['task_count'] for p in all_scores)
                    },
                    "evaluation_period_days": 30
                }
            })
