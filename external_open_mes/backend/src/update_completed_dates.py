"""
既存の完了済み工程に完了日を設定し、着手中工程に開始日時を設定するスクリプト
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'base.settings')
django.setup()

from production.models import ProductionPlan
from django.utils import timezone

# 完了ステータスフィールドと完了日フィールドのマッピング
STATUS_TO_COMPLETED_DATE_MAP = {
    'slit_status': 'slit_completed_date',
    'cut_status': 'cut_completed_date',
    'base_material_cut_status': 'base_material_cut_completed_date',
    'molder_status': 'molder_completed_date',
    'v_cut_lapping_status': 'vcut_wrapping_completed_date',
    'post_processing_status': 'post_processing_completed_date',
    'packing_status': 'packing_completed_date',
    'decorative_board_status': 'veneer_completed_date',
    'decorative_board_cut_status': 'cut_veneer_completed_date',
}

# ステータスフィールドと開始日時フィールドのマッピング
STATUS_TO_STARTED_DATETIME_MAP = {
    'slit_status': 'slit_started_datetime',
    'cut_status': 'cut_started_datetime',
    'base_material_cut_status': 'base_material_cut_started_datetime',
    'molder_status': 'molder_started_datetime',
    'v_cut_lapping_status': 'vcut_wrapping_started_datetime',
    'post_processing_status': 'post_processing_started_datetime',
    'packing_status': 'packing_started_datetime',
    'decorative_board_status': 'veneer_started_datetime',
    'decorative_board_cut_status': 'cut_veneer_started_datetime',
}

# 全ての生産計画を取得
all_plans = ProductionPlan.objects.all()
updated_count = 0
now = timezone.now()

for plan in all_plans:
    update_fields = []

    # 完了済み工程の完了日を設定
    for status_field, date_field in STATUS_TO_COMPLETED_DATE_MAP.items():
        status_value = getattr(plan, status_field, None)
        date_value = getattr(plan, date_field, None)

        if status_value == 'COMPLETED' and date_value is None:
            # 今日の日付を設定(実際の完了日が不明なため)
            setattr(plan, date_field, now.date())
            update_fields.append(date_field)

    # 着手中工程の開始日時を設定
    for status_field, datetime_field in STATUS_TO_STARTED_DATETIME_MAP.items():
        status_value = getattr(plan, status_field, None)
        datetime_value = getattr(plan, datetime_field, None)

        if status_value == 'IN_PROGRESS' and datetime_value is None:
            # 現在の日時を設定(実際の開始日時が不明なため)
            setattr(plan, datetime_field, now)
            update_fields.append(datetime_field)

    if update_fields:
        plan.save(update_fields=update_fields)
        updated_count += 1
        print(f"Updated plan {plan.reception_no}: {', '.join(update_fields)}")

print(f"\n完了: {updated_count}件の生産計画を更新しました")
