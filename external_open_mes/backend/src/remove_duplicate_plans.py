"""
重複した生産計画レコードを削除するスクリプト
同じ受付No、追加No、工程の組み合わせで複数のレコードがある場合、
最も進んでいるステータスと最新の更新日時を持つレコードを保持し、他を削除する
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'base.settings')
django.setup()

from production.models import ProductionPlan
from django.db.models import Count

# ステータスの優先順位(数値が大きいほど優先)
STATUS_PRIORITY = {
    'COMPLETED': 4,
    'IN_PROGRESS': 3,
    'DELAYED': 2,
    'ON_HOLD': 1,
    'PENDING': 0,
}

# 重複レコードを検出
duplicates = ProductionPlan.objects.values('reception_no', 'additional_no', 'process').annotate(
    count=Count('id')
).filter(count__gt=1)

deleted_count = 0
kept_count = 0

print(f'重複レコード組: {duplicates.count()}件\n')

for dup in duplicates:
    reception_no = dup['reception_no']
    additional_no = dup['additional_no']
    process = dup['process']

    # 該当する全レコードを取得
    records = ProductionPlan.objects.filter(
        reception_no=reception_no,
        additional_no=additional_no,
        process=process
    ).order_by('-updated_at')

    if records.count() <= 1:
        continue

    print(f'\n受付No: {reception_no}, 追加No: {additional_no}, 工程: {process}')
    print(f'  レコード数: {records.count()}件')

    # 最も進んでいるレコードを見つける
    best_record = None
    best_priority = -1
    best_updated_at = None

    for record in records:
        priority = STATUS_PRIORITY.get(record.status, 0)

        # 工程ステータスも考慮(どれか1つでもIN_PROGRESS/COMPLETEDなら優先)
        process_statuses = [
            record.slit_status,
            record.cut_status,
            record.base_material_cut_status,
            record.molder_status,
            record.v_cut_lapping_status,
            record.post_processing_status,
            record.packing_status,
            record.decorative_board_status,
            record.decorative_board_cut_status,
        ]

        # IN_PROGRESSまたはCOMPLETEDの工程数
        in_progress_count = process_statuses.count('IN_PROGRESS')
        completed_count = process_statuses.count('COMPLETED')

        # 優先度を計算
        total_priority = (priority * 100) + (completed_count * 10) + in_progress_count

        if (best_record is None or
            total_priority > best_priority or
            (total_priority == best_priority and record.updated_at > best_updated_at)):
            best_record = record
            best_priority = total_priority
            best_updated_at = record.updated_at

    print(f'  保持するレコード: ID={best_record.id}, status={best_record.status}, updated_at={best_record.updated_at}')

    # 保持するレコード以外を削除
    for record in records:
        if record.id != best_record.id:
            print(f'  削除: ID={record.id}, status={record.status}, updated_at={record.updated_at}')
            record.delete()
            deleted_count += 1
        else:
            kept_count += 1

print(f'\n\n完了:')
print(f'  保持: {kept_count}件')
print(f'  削除: {deleted_count}件')
