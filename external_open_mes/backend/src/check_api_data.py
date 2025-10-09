"""
APIレスポンスデータを確認するスクリプト
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'base.settings')
django.setup()

from production.models import ProductionPlan
from production.serializers import ProductionPlanSerializer

# 着手中の工程を持つ生産計画を取得
from django.db.models import Q

in_progress_plans = ProductionPlan.objects.filter(
    Q(slit_status='IN_PROGRESS') |
    Q(cut_status='IN_PROGRESS') |
    Q(base_material_cut_status='IN_PROGRESS') |
    Q(molder_status='IN_PROGRESS') |
    Q(v_cut_lapping_status='IN_PROGRESS') |
    Q(post_processing_status='IN_PROGRESS') |
    Q(packing_status='IN_PROGRESS') |
    Q(decorative_board_status='IN_PROGRESS') |
    Q(decorative_board_cut_status='IN_PROGRESS')
)[:5]

print(f"着手中の工程を持つ生産計画: {in_progress_plans.count()}件\n")

for plan in in_progress_plans:
    serializer = ProductionPlanSerializer(plan)
    data = serializer.data

    print(f"受付No: {data.get('reception_no')}")

    # 全工程を確認
    processes = [
        ('スリット', 'slit_status', 'slit_started_datetime', 'slit_scheduled_date'),
        ('カット', 'cut_status', 'cut_started_datetime', 'cut_scheduled_date'),
        ('基材カット', 'base_material_cut_status', 'base_material_cut_started_datetime', 'base_material_cut_scheduled_date'),
        ('モルダー', 'molder_status', 'molder_started_datetime', 'molder_scheduled_date'),
    ]

    for name, status_key, started_key, scheduled_key in processes:
        status = data.get(status_key)
        if status == 'IN_PROGRESS':
            started = data.get(started_key)
            scheduled = data.get(scheduled_key)
            print(f"  {name}: {status}")
            print(f"    開始日時: {started}")
            print(f"    予定日: {scheduled}")

    print()
