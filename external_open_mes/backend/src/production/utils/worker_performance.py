"""
Worker Performance Analysis Utilities

製品名×工程の全作業者平均を基準とした作業者パフォーマンス評価システム
"""

from datetime import timedelta, date
from django.utils import timezone
from django.core.cache import cache
from django.contrib.auth import get_user_model
from production.models import WorkProgress


# 定数定義
VALID_PROCESSES = [
    'slit',
    'cut',
    'base_material_cut',
    'molder',
    'v_cut_lapping',
    'post_processing',
    'packing',
    'decorative_board',
    'decorative_board_cut',
]

# 技能レベル定義 (スコア閾値, レベルコード, 表示名)
SKILL_LEVELS = [
    (110, 'ADVANCED', '高度な技能レベル'),
    (105, 'PROFICIENT', '熟練レベル'),
    (95, 'COMPETENT', '標準レベル'),
    (90, 'DEVELOPING', '育成段階'),
    (0, 'FOUNDATIONAL', '基礎訓練段階'),
]


def get_product_process_average(product_name, process, period_days=30):
    """
    製品×工程の全作業者平均単位時間を取得

    Args:
        product_name (str): 製品名
        process (str): 工程名
        period_days (int): 評価期間（日数）

    Returns:
        float | None: 平均単位時間（分/個）、データ不足の場合はNone
    """
    # キャッシュチェック
    cache_key = f"perf_avg_{process}_{product_name}_{date.today()}"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    # データ取得
    cutoff_date = timezone.now() - timedelta(days=period_days)

    tasks = WorkProgress.objects.filter(
        production_plan__product_name=product_name,
        process_type=process,
        is_cancelled=False,
        end_datetime__gte=cutoff_date,
        start_datetime__isnull=False,
        end_datetime__isnull=False,
        quantity_completed__gt=0
    ).select_related('production_plan')

    # データ不足チェック
    if tasks.count() < 5:
        cache.set(cache_key, None, 86400)  # 1日キャッシュ
        return None

    # 単位時間計算
    unit_times = []
    for task in tasks:
        duration = (task.end_datetime - task.start_datetime).total_seconds() / 60
        if duration <= 0:
            continue  # 時間計算エラーをスキップ

        unit_time = duration / task.quantity_completed
        unit_times.append(unit_time)

    # 有効タスクチェック
    if len(unit_times) < 5:
        cache.set(cache_key, None, 86400)
        return None

    # 平均計算
    average = sum(unit_times) / len(unit_times)

    # キャッシュ保存
    cache.set(cache_key, average, 86400)

    return average


def determine_skill_level(score):
    """
    スコアから技能レベルを判定

    Args:
        score (float): スコア

    Returns:
        tuple: (レベルコード, 表示名)
    """
    for threshold, level_code, level_display in SKILL_LEVELS:
        if score >= threshold:
            return level_code, level_display

    # フォールバック（理論上ここには到達しない）
    return 'FOUNDATIONAL', '基礎訓練段階'


def calculate_worker_score(worker, process, period_days=30):
    """
    作業者の工程別スコアを計算

    Args:
        worker (User): 作業者
        process (str): 工程名
        period_days (int): 評価期間（日数）

    Returns:
        dict | None: スコア情報、データ不足の場合はNone
    """
    cutoff_date = timezone.now() - timedelta(days=period_days)

    # 作業者のタスク取得
    worker_tasks = WorkProgress.objects.filter(
        operator=worker,
        process_type=process,
        is_cancelled=False,
        end_datetime__gte=cutoff_date,
        start_datetime__isnull=False,
        end_datetime__isnull=False,
        quantity_completed__gt=0
    ).select_related('production_plan')

    # データ不足チェック
    if worker_tasks.count() < 5:
        return None

    # 各タスクのスコア計算
    task_scores = []
    task_details = []

    for task in worker_tasks:
        product_name = task.production_plan.product_name

        # この製品の平均取得
        avg_unit_time = get_product_process_average(
            product_name, process, period_days
        )

        if avg_unit_time is None:
            continue  # この製品はデータ不足

        # 個人の単位時間
        duration = (task.end_datetime - task.start_datetime).total_seconds() / 60
        if duration <= 0:
            continue  # 時間計算エラー

        personal_unit_time = duration / task.quantity_completed

        if personal_unit_time <= 0:
            continue  # ゼロ除算防止

        # スコア計算: 平均 / 個人 × 100
        # 平均より速い → 100点超、平均より遅い → 100点未満
        score = (avg_unit_time / personal_unit_time) * 100

        # 上限設定（極端な値を防ぐ）
        score = min(score, 200)

        task_scores.append(score)
        task_details.append({
            'product_name': product_name,
            'quantity': task.quantity_completed,
            'personal_unit_time': round(personal_unit_time, 2),
            'average_unit_time': round(avg_unit_time, 2),
            'score': round(score, 2),
            'date': task.end_datetime.date().isoformat()
        })

    # 有効タスクチェック
    if len(task_scores) < 5:
        return None

    # 平均スコア
    overall_score = sum(task_scores) / len(task_scores)
    skill_level, level_display = determine_skill_level(overall_score)

    return {
        'score': round(overall_score, 2),
        'skill_level': skill_level,
        'skill_level_display': level_display,
        'task_count': len(task_scores),
        'task_details': task_details
    }


def get_skill_trend(worker, process, months=6):
    """
    月次推移を取得

    Args:
        worker (User): 作業者
        process (str): 工程名
        months (int): 取得する月数

    Returns:
        list: 月次スコアリスト
    """
    trends = []

    for i in range(months):
        # 各月の期間設定
        month_end = timezone.now() - timedelta(days=30*i)
        month_start = timezone.now() - timedelta(days=30*(i+1))

        # その月のタスク取得
        monthly_tasks = WorkProgress.objects.filter(
            operator=worker,
            process_type=process,
            is_cancelled=False,
            end_datetime__gte=month_start,
            end_datetime__lt=month_end,
            start_datetime__isnull=False,
            end_datetime__isnull=False,
            quantity_completed__gt=0
        ).select_related('production_plan')

        # データ不足チェック
        if monthly_tasks.count() < 5:
            continue  # この月はスキップ

        # 月次スコア計算
        task_scores = []
        for task in monthly_tasks:
            product_name = task.production_plan.product_name

            # その月の製品平均を取得（30日固定）
            avg_unit_time = get_product_process_average(
                product_name, process, period_days=30
            )

            if avg_unit_time is None:
                continue

            duration = (task.end_datetime - task.start_datetime).total_seconds() / 60
            if duration <= 0:
                continue

            personal_unit_time = duration / task.quantity_completed
            if personal_unit_time <= 0:
                continue

            score = (avg_unit_time / personal_unit_time) * 100
            score = min(score, 200)
            task_scores.append(score)

        if len(task_scores) >= 5:
            monthly_score = sum(task_scores) / len(task_scores)
            trends.append({
                'month': month_start.strftime('%Y年%m月'),
                'score': round(monthly_score, 2),
                'task_count': len(task_scores)
            })

    # 古い順に並べ替え
    return list(reversed(trends))


def get_worker_all_process_scores(worker, period_days=30):
    """
    全工程のスコアを取得

    Args:
        worker (User): 作業者
        period_days (int): 評価期間（日数）

    Returns:
        list: 工程別スコアリスト
    """
    process_scores = []

    # 工程表示名マッピング
    process_display_names = {
        'slit': 'スリット',
        'cut': 'カット',
        'base_material_cut': '基材カット',
        'molder': 'モルダー',
        'v_cut_lapping': 'Vカットラッピング',
        'post_processing': '後加工',
        'packing': '梱包',
        'decorative_board': '化粧板貼',
        'decorative_board_cut': 'カット化粧板',
    }

    for process in VALID_PROCESSES:
        score_data = calculate_worker_score(worker, process, period_days)

        if score_data:
            process_scores.append({
                'process': process,
                'process_display': process_display_names.get(process, process),
                **score_data
            })

    return process_scores
