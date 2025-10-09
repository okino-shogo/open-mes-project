"""
生産計画のCSVマッピング設定を作成するmanagement command

使用方法:
    docker compose exec backend python3 manage.py setup_production_plan_csv_mapping
"""
from django.core.management.base import BaseCommand
from base.models import CsvColumnMapping


class Command(BaseCommand):
    help = '生産計画のCSVマッピング設定を作成（画像カラム順序に対応）'

    def handle(self, *args, **kwargs):
        """
        画像で示されたカラム順序に基づいてCSVマッピングを作成

        カラム順序:
        1. QRコード, 2. 受付No, 3. 追加No, 4. 得意先名, 5. 現場名, 6. 追加内容,
        7. 製造予定日, 8. 出荷予定日, 9. 品名, 10. 工程, 11. 数量,
        12. スリット予定日, 13. カット予定日, 14. モルダー予定日,
        15. Vカットマッピング・後加工予定日, 16. 梱包予定日, 17. 納品日,
        18. 化粧板貼予定日, 19. カット化粧板予定日
        """

        # 画像カラム順序に基づくCSVマッピング設定
        csv_mappings = [
            # 順序 | モデルフィールド | CSVヘッダー | 順序 | 有効 | 上書きキー
            {'field': 'qr_code', 'csv_header': 'QRコード', 'order': 10, 'active': True, 'update_key': True},
            {'field': 'reception_no', 'csv_header': '受付No', 'order': 20, 'active': True, 'update_key': False},
            {'field': 'additional_no', 'csv_header': '追加No', 'order': 30, 'active': True, 'update_key': False},
            {'field': 'customer_name', 'csv_header': '得意先名', 'order': 40, 'active': True, 'update_key': False},
            {'field': 'site_name', 'csv_header': '現場名', 'order': 50, 'active': True, 'update_key': False},
            {'field': 'additional_content', 'csv_header': '追加内容', 'order': 60, 'active': True, 'update_key': False},
            {'field': 'planned_start_datetime', 'csv_header': '製造予定日', 'order': 70, 'active': True, 'update_key': False},
            {'field': 'planned_shipment_date', 'csv_header': '出荷予定日', 'order': 80, 'active': True, 'update_key': False},
            {'field': 'product_code', 'csv_header': '品名', 'order': 90, 'active': True, 'update_key': False},
            {'field': 'process', 'csv_header': '工程', 'order': 100, 'active': True, 'update_key': False},
            {'field': 'planned_quantity', 'csv_header': '数量', 'order': 110, 'active': True, 'update_key': False},
            {'field': 'slit_scheduled_date', 'csv_header': 'スリット予定日', 'order': 120, 'active': True, 'update_key': False},
            {'field': 'cut_scheduled_date', 'csv_header': 'カット予定日', 'order': 130, 'active': True, 'update_key': False},
            {'field': 'molder_scheduled_date', 'csv_header': 'モルダー予定日', 'order': 140, 'active': True, 'update_key': False},
            {'field': 'vcut_wrapping_scheduled_date', 'csv_header': 'Vカットラッピング予定日', 'order': 150, 'active': True, 'update_key': False},
            {'field': 'post_processing_scheduled_date', 'csv_header': '後加工予定日', 'order': 160, 'active': True, 'update_key': False},
            {'field': 'packing_scheduled_date', 'csv_header': '梱包予定日', 'order': 170, 'active': True, 'update_key': False},
            {'field': 'delivery_date', 'csv_header': '納品日', 'order': 180, 'active': True, 'update_key': False},
            {'field': 'veneer_scheduled_date', 'csv_header': '化粧板貼予定日', 'order': 190, 'active': True, 'update_key': False},
            {'field': 'cut_veneer_scheduled_date', 'csv_header': 'カット化粧板予定日', 'order': 200, 'active': True, 'update_key': False},

            # その他のフィールド（非アクティブ）
            {'field': 'plan_name', 'csv_header': '計画名', 'order': 210, 'active': False, 'update_key': False},
            {'field': 'production_plan', 'csv_header': '参照生産計画', 'order': 220, 'active': False, 'update_key': False},
            {'field': 'planned_end_datetime', 'csv_header': '計画終了日時', 'order': 230, 'active': False, 'update_key': False},
            {'field': 'actual_start_datetime', 'csv_header': '実績開始日時', 'order': 240, 'active': False, 'update_key': False},
            {'field': 'actual_end_datetime', 'csv_header': '実績終了日時', 'order': 250, 'active': False, 'update_key': False},
            {'field': 'status', 'csv_header': 'ステータス', 'order': 260, 'active': False, 'update_key': False},
            {'field': 'remarks', 'csv_header': '備考', 'order': 270, 'active': False, 'update_key': False},
        ]

        created_count = 0
        updated_count = 0

        for item in csv_mappings:
            obj, created = CsvColumnMapping.objects.update_or_create(
                data_type='production_plan',
                model_field_name=item['field'],
                defaults={
                    'csv_header': item['csv_header'],
                    'order': item['order'],
                    'is_update_key': item.get('update_key', False),
                    'is_active': item.get('active', True),
                }
            )
            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f"  ✓ 作成: {item['csv_header']} ({item['field']})"))
            else:
                updated_count += 1
                self.stdout.write(f"  → 更新: {item['csv_header']} ({item['field']})")

        self.stdout.write(self.style.SUCCESS(f'\n完了: {created_count}件作成, {updated_count}件更新'))
        self.stdout.write(self.style.SUCCESS('生産計画のCSVマッピング設定を画像通りに構成しました'))

        # CSVテンプレートの生成確認
        active_count = sum(1 for item in csv_mappings if item.get('active', True))
        self.stdout.write(self.style.SUCCESS(f'\nアクティブなマッピング: {active_count}件'))
        self.stdout.write('\nCSVテンプレートは以下のURLからダウンロードできます:')
        self.stdout.write('  /api/base/csv-column-mappings/csv-template/?data_type=production_plan')
