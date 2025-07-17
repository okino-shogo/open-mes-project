from django.test import TestCase
from django.utils import timezone
from django.contrib.auth import get_user_model
from datetime import datetime, timedelta
from .models import ProductionPlan, PartsUsed, MaterialAllocation, WorkProgress
import csv
import io

User = get_user_model()

class ProcessScheduleModelTest(TestCase):
    """ProcessScheduleモデルのテスト"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.production_plan = ProductionPlan.objects.create(
            plan_name='テスト計画',
            product_code='TEST001',
            planned_quantity=100,
            planned_start_datetime=timezone.now(),
            planned_end_datetime=timezone.now() + timedelta(days=10),
            status='PENDING'
        )
    
    def test_process_schedule_creation(self):
        """ProcessScheduleモデルの作成テスト"""
        # ProcessScheduleモデルが実装されたため、このテストは成功する（Green Phase）
        from .models import ProcessSchedule
        process_schedule = ProcessSchedule.objects.create(
            production_plan=self.production_plan,
            process_name='スリット',
            scheduled_start_date=timezone.now().date(),
            scheduled_end_date=(timezone.now() + timedelta(days=2)).date(),
            status='未着手'
        )
        self.assertEqual(process_schedule.process_name, 'スリット')
        self.assertEqual(process_schedule.status, '未着手')
        self.assertEqual(process_schedule.production_plan, self.production_plan)

class ProductionPlanExtensionTest(TestCase):
    """ProductionPlanモデルの拡張テスト"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_production_plan_with_qr_code(self):
        """QRコードフィールドのテスト"""
        # QRコードフィールドが実装されたため、このテストは成功する（Green Phase）
        production_plan = ProductionPlan.objects.create(
            plan_name='テスト計画',
            product_code='TEST001',
            qr_code='QR001',
            reception_no='24112',
            additional_no='205',
            client_name='テスト得意先',
            site_name='テスト現場',
            planned_quantity=100,
            planned_start_datetime=timezone.now(),
            planned_end_datetime=timezone.now() + timedelta(days=10),
            status='PENDING'
        )
        self.assertEqual(production_plan.qr_code, 'QR001')
        self.assertEqual(production_plan.reception_no, '24112')
        self.assertEqual(production_plan.additional_no, '205')
        self.assertEqual(production_plan.client_name, 'テスト得意先')
        self.assertEqual(production_plan.site_name, 'テスト現場')
    
    def test_production_plan_with_process_dates(self):
        """各工程の予定日フィールドのテスト"""
        # 工程予定日フィールドが実装されたため、このテストは成功する（Green Phase）
        production_plan = ProductionPlan.objects.create(
            plan_name='テスト計画',
            product_code='TEST001',
            planned_quantity=100,
            planned_start_datetime=timezone.now(),
            planned_end_datetime=timezone.now() + timedelta(days=10),
            status='PENDING',
            slit_scheduled_date=timezone.now(),
            cut_scheduled_date=timezone.now() + timedelta(days=1),
            molder_scheduled_date=timezone.now() + timedelta(days=2),
            v_cut_lapping_scheduled_date=timezone.now() + timedelta(days=3),
            post_processing_scheduled_date=timezone.now() + timedelta(days=4),
            packing_scheduled_date=timezone.now() + timedelta(days=5),
            decorative_board_scheduled_date=timezone.now() + timedelta(days=6),
            cut_decorative_board_scheduled_date=timezone.now() + timedelta(days=7)
        )
        self.assertIsNotNone(production_plan.slit_scheduled_date)
        self.assertIsNotNone(production_plan.cut_scheduled_date)
        self.assertIsNotNone(production_plan.molder_scheduled_date)
        self.assertIsNotNone(production_plan.v_cut_lapping_scheduled_date)
        self.assertIsNotNone(production_plan.post_processing_scheduled_date)
        self.assertIsNotNone(production_plan.packing_scheduled_date)
        self.assertIsNotNone(production_plan.decorative_board_scheduled_date)
        self.assertIsNotNone(production_plan.cut_decorative_board_scheduled_date)

class CSVImportTest(TestCase):
    """CSVインポート機能のテスト"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.sample_csv_data = """QRコード,受付No,追加No,得意先名,現場名,追加内容,製造予定日,出荷予定日,品名,工程,数量,スリット予定日,カット予定日,モルダー予定日,Vカットラッピング予定日,後加工予定日,梱包予定日,化粧板貼付予定日,カット化粧板貼付予定日
24112050,24112,205,株式会社テスト,東京都テスト区,-16*19*材料加工,2025/05/18 0:00,2025/05/19 0:00,鏡材 (ラ),ラッピング,49,2025/05/14 0:00,2025/05/15 0:00,,2025/06/27 0:00,,,2025/08/03 0:00,
25559001,25559,200,有限会社テスト,西東京市テスト町,-7取り直し,2025/06/27 0:00,2025/06/27 0:00,AW (V),Vカット,3,,,4/26 16:35 検査完了,6/26 16:35 (削げ) 完了,4/25 11:06 (削げ) 完了,6/27 11:31 (削げ) 完了,6/27 11:31 (削げ) 完了,"""
    
    def test_csv_import_function_exists(self):
        """CSVインポート機能が存在するかのテスト"""
        # CSVインポート機能が実装されたため、このテストは成功する（Green Phase）
        from .utils import import_csv_data
        csv_file = io.StringIO(self.sample_csv_data)
        result = import_csv_data(csv_file)
        
        # 結果の構造を確認
        self.assertIn('success', result)
        self.assertIn('errors', result)
        self.assertIn('created_plans', result)
        self.assertIn('created_schedules', result)
        self.assertIsInstance(result['success'], int)
        self.assertIsInstance(result['errors'], list)
        self.assertIsInstance(result['created_plans'], list)
        self.assertIsInstance(result['created_schedules'], list)
    
    def test_csv_data_parsing(self):
        """CSVデータの解析テスト"""
        # CSVデータ解析機能が実装されたため、このテストは成功する（Green Phase）
        from .utils import parse_csv_row
        csv_file = io.StringIO(self.sample_csv_data)
        reader = csv.DictReader(csv_file)
        for row in reader:
            parsed_data = parse_csv_row(row)
            self.assertIn('qr_code', parsed_data)
            self.assertIn('reception_no', parsed_data)
            self.assertIn('additional_no', parsed_data)
            self.assertIn('client_name', parsed_data)
            self.assertIn('site_name', parsed_data)
            self.assertIn('product_name', parsed_data)
            self.assertIn('planned_quantity', parsed_data)
            
            # 1行目のデータをチェック
            self.assertEqual(parsed_data['qr_code'], '24112050')
            self.assertEqual(parsed_data['reception_no'], '24112')
            self.assertEqual(parsed_data['additional_no'], '205')
            self.assertEqual(parsed_data['client_name'], '株式会社テスト')
            self.assertEqual(parsed_data['site_name'], '東京都テスト区')
            self.assertEqual(parsed_data['product_name'], '鏡材 (ラ)')
            self.assertEqual(parsed_data['planned_quantity'], 49)
            break

class GanttChartViewTest(TestCase):
    """ガントチャート表示のテスト"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.production_plan = ProductionPlan.objects.create(
            plan_name='テスト計画',
            product_code='TEST001',
            planned_quantity=100,
            planned_start_datetime=timezone.now(),
            planned_end_datetime=timezone.now() + timedelta(days=10),
            status='PENDING'
        )
    
    def test_gantt_chart_view_exists(self):
        """ガントチャート表示ビューが存在するかのテスト"""
        # ガントチャート表示ビューが実装されたため、このテストは成功する（Green Phase）
        from django.urls import reverse
        url = reverse('production:gantt_chart')
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'ガントチャート')
        self.assertContains(response, 'production_plans')
    
    def test_gantt_chart_data_format(self):
        """ガントチャートデータの形式テスト"""
        # ガントチャートデータ形式が実装されたため、このテストは成功する（Green Phase）
        from .utils import get_gantt_chart_data
        data = get_gantt_chart_data()
        self.assertIn('production_plans', data)
        self.assertIn('process_schedules', data)
        self.assertIn('date_range', data)
        self.assertIn('start', data['date_range'])
        self.assertIn('end', data['date_range'])

class KaizenModelTest(TestCase):
    """改善提案モデルのテスト"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.production_plan = ProductionPlan.objects.create(
            plan_name='テスト計画',
            product_code='TEST001',
            planned_quantity=100,
            planned_start_datetime=timezone.now(),
            planned_end_datetime=timezone.now() + timedelta(days=10),
            status='PENDING'
        )
    
    def test_kaizen_model_creation(self):
        """改善提案モデルの作成テスト"""
        # Kaizenモデルが実装されたため、このテストは成功する（Green Phase）
        from .models import Kaizen
        kaizen = Kaizen.objects.create(
            title='工程改善提案',
            description='スリット工程の効率化',
            proposer=self.user,
            production_plan=self.production_plan,
            process_step='スリット',
            status='提案中',
            priority='高',
            expected_effect='作業時間20%削減'
        )
        self.assertEqual(kaizen.title, '工程改善提案')
        self.assertEqual(kaizen.description, 'スリット工程の効率化')
        self.assertEqual(kaizen.proposer, self.user)
        self.assertEqual(kaizen.production_plan, self.production_plan)
        self.assertEqual(kaizen.process_step, 'スリット')
        self.assertEqual(kaizen.status, '提案中')
        self.assertEqual(kaizen.priority, '高')
        self.assertEqual(kaizen.expected_effect, '作業時間20%削減')
