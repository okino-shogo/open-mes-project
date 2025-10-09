"""
生産計画のModelDisplaySetting初期データを作成するmanagement command

使用方法:
    docker compose exec backend python3 manage.py setup_production_plan_display
"""
from django.core.management.base import BaseCommand
from base.models import ModelDisplaySetting


class Command(BaseCommand):
    help = '生産計画のModelDisplaySetting初期データを作成（画像カラム順序に対応）'

    def handle(self, *args, **kwargs):
        """
        画像で示されたカラム順序に基づいてModelDisplaySettingを作成

        カラム順序:
        1. QRコード, 2. 受付No, 3. 追加No, 4. 得意先名, 5. 現場名, 6. 追加内容,
        7. 製造予定日, 8. 出荷予定日, 9. 品名, 10. 工程, 11. 数量,
        12. スリット予定日, 13. カット予定日, 14. モルダー予定日,
        15. Vカットマッピング・後加工予定日, 16. 梱包予定日, 17. 納品日,
        18. 化粧板貼予定日, 19. カット化粧板予定日
        """

        # 画像カラム順序に基づく表示設定
        display_settings = [
            # 順序 | フィールド名 | 表示名 | 順序 | 一覧 | 検索 | フィルタ
            {'field': 'qr_code', 'name': 'QRコード', 'order': 10, 'list': True, 'search': True, 'filter': False},
            {'field': 'reception_no', 'name': '受付No', 'order': 20, 'list': True, 'search': True, 'filter': False},
            {'field': 'additional_no', 'name': '追加No', 'order': 30, 'list': True, 'search': True, 'filter': False},
            {'field': 'customer_name', 'name': '得意先名', 'order': 40, 'list': True, 'search': True, 'filter': True},
            {'field': 'site_name', 'name': '現場名', 'order': 50, 'list': True, 'search': True, 'filter': False},
            {'field': 'additional_content', 'name': '追加内容', 'order': 60, 'list': True, 'search': True, 'filter': False},
            {'field': 'planned_start_datetime', 'name': '製造予定日', 'order': 70, 'list': True, 'search': False, 'filter': True},
            {'field': 'planned_shipment_date', 'name': '出荷予定日', 'order': 80, 'list': True, 'search': False, 'filter': True},
            {'field': 'product_code', 'name': '品名', 'order': 90, 'list': True, 'search': True, 'filter': False},
            {'field': 'process', 'name': '工程', 'order': 100, 'list': True, 'search': True, 'filter': True},
            {'field': 'planned_quantity', 'name': '数量', 'order': 110, 'list': True, 'search': False, 'filter': False},
            {'field': 'slit_scheduled_date', 'name': 'スリット予定日', 'order': 120, 'list': True, 'search': False, 'filter': False},
            {'field': 'cut_scheduled_date', 'name': 'カット予定日', 'order': 130, 'list': True, 'search': False, 'filter': False},
            {'field': 'molder_scheduled_date', 'name': 'モルダー予定日', 'order': 140, 'list': True, 'search': False, 'filter': False},
            {'field': 'vcut_wrapping_scheduled_date', 'name': 'Vカットラッピング予定日', 'order': 150, 'list': True, 'search': False, 'filter': False},
            {'field': 'post_processing_scheduled_date', 'name': '後加工予定日', 'order': 160, 'list': True, 'search': False, 'filter': False},
            {'field': 'packing_scheduled_date', 'name': '梱包予定日', 'order': 170, 'list': True, 'search': False, 'filter': False},
            {'field': 'delivery_date', 'name': '納品日', 'order': 180, 'list': True, 'search': False, 'filter': True},
            {'field': 'veneer_scheduled_date', 'name': '化粧板貼予定日', 'order': 190, 'list': True, 'search': False, 'filter': False},
            {'field': 'cut_veneer_scheduled_date', 'name': 'カット化粧板予定日', 'order': 200, 'list': True, 'search': False, 'filter': False},

            # その他の既存フィールド（一覧表示はOFF）
            {'field': 'plan_name', 'name': '計画名', 'order': 210, 'list': False, 'search': True, 'filter': False},
            {'field': 'production_plan', 'name': '参照生産計画', 'order': 220, 'list': False, 'search': False, 'filter': False},
            {'field': 'planned_end_datetime', 'name': '計画終了日時', 'order': 230, 'list': False, 'search': False, 'filter': False},
            {'field': 'actual_start_datetime', 'name': '実績開始日時', 'order': 240, 'list': False, 'search': False, 'filter': False},
            {'field': 'actual_end_datetime', 'name': '実績終了日時', 'order': 250, 'list': False, 'search': False, 'filter': False},
            {'field': 'status', 'name': 'ステータス', 'order': 260, 'list': False, 'search': False, 'filter': True},
            {'field': 'remarks', 'name': '備考', 'order': 270, 'list': False, 'search': True, 'filter': False},
            {'field': 'created_at', 'name': '作成日時', 'order': 280, 'list': False, 'search': False, 'filter': False},
            {'field': 'updated_at', 'name': '更新日時', 'order': 290, 'list': False, 'search': False, 'filter': False},
        ]

        created_count = 0
        updated_count = 0

        for item in display_settings:
            obj, created = ModelDisplaySetting.objects.update_or_create(
                data_type='production_plan',
                model_field_name=item['field'],
                defaults={
                    'display_name': item['name'],
                    'display_order': item['order'],
                    'is_list_display': item.get('list', True),
                    'is_search_field': item.get('search', False),
                    'is_list_filter': item.get('filter', False),
                }
            )
            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f"  ✓ 作成: {item['name']} ({item['field']})"))
            else:
                updated_count += 1
                self.stdout.write(f"  → 更新: {item['name']} ({item['field']})")

        self.stdout.write(self.style.SUCCESS(f'\n完了: {created_count}件作成, {updated_count}件更新'))
        self.stdout.write(self.style.SUCCESS('生産計画の表示設定を画像通りに構成しました'))
