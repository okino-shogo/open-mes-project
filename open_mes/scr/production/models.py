from django.db import models
from django.utils import timezone
from django.conf import settings
import uuid
from uuid6 import uuid7

# Create your models here.

class ProductionPlan(models.Model):
    """
    生産計画モデル
    """
    id = models.UUIDField(primary_key=True, default=uuid7, editable=False) # UUIDv7を使用
    STATUS_CHOICES = [
        ('PENDING', '未着手'),
        ('IN_PROGRESS', '進行中'),
        ('COMPLETED', '完了'),
        ('ON_HOLD', '保留'),
        ('CANCELLED', '中止'),
    ]
    
    # 詳細なステータス選択肢
    DETAILED_STATUS_CHOICES = [
        ('未着手', '未着手'),
        ('着手中', '着手中'),
        ('完了', '完了'),
        ('遅延', '遅延'),
        ('保留', '保留'),
        ('中止', '中止'),
    ]

    plan_name = models.CharField(max_length=255, verbose_name="計画名")
    # TODO: master.Productモデルが定義されたらForeignKeyに変更する
    # product = models.ForeignKey('master.Product', on_delete=models.PROTECT, verbose_name="製品")
    product_code = models.CharField(max_length=100, verbose_name="製品コード (仮)")
    production_plan = models.CharField(
        max_length=255, # 参照する計画名などを想定
        null=True,
        blank=True,
        verbose_name="参照生産計画",
        help_text="参照する生産計画の名前や識別子を文字列で記録します。"
    )
    planned_quantity = models.PositiveIntegerField(verbose_name="計画数量")
    planned_start_datetime = models.DateTimeField(verbose_name="計画開始日時")
    planned_end_datetime = models.DateTimeField(verbose_name="計画終了日時")
    actual_start_datetime = models.DateTimeField(null=True, blank=True, verbose_name="実績開始日時")
    actual_end_datetime = models.DateTimeField(null=True, blank=True, verbose_name="実績終了日時")
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='PENDING',
        verbose_name="ステータス"
    )
    
    # CSV対応のフィールド
    qr_code = models.CharField(max_length=100, null=True, blank=True, verbose_name="QRコード")
    reception_no = models.CharField(max_length=100, null=True, blank=True, verbose_name="受付No")
    additional_no = models.CharField(max_length=100, null=True, blank=True, verbose_name="追加No")
    client_name = models.CharField(max_length=200, null=True, blank=True, verbose_name="得意先名")
    site_name = models.CharField(max_length=200, null=True, blank=True, verbose_name="現場名")
    additional_content = models.TextField(null=True, blank=True, verbose_name="追加内容")
    manufacturing_scheduled_date = models.DateTimeField(null=True, blank=True, verbose_name="製造予定日")
    shipping_scheduled_date = models.DateTimeField(null=True, blank=True, verbose_name="出荷予定日")
    product_name = models.CharField(max_length=200, null=True, blank=True, verbose_name="品名")
    process_type = models.CharField(max_length=100, null=True, blank=True, verbose_name="工程")
    
    # 納期目標
    delivery_target_date = models.DateTimeField(null=True, blank=True, verbose_name="納期目標日")
    delivery_target_note = models.CharField(max_length=200, null=True, blank=True, verbose_name="納期目標備考")
    
    # 各工程の予定日
    slit_scheduled_date = models.DateTimeField(null=True, blank=True, verbose_name="スリット予定日")
    cut_scheduled_date = models.DateTimeField(null=True, blank=True, verbose_name="カット予定日")
    base_material_cut_scheduled_date = models.DateTimeField(null=True, blank=True, verbose_name="基材カット予定日")
    molder_scheduled_date = models.DateTimeField(null=True, blank=True, verbose_name="モルダー予定日")
    v_cut_lapping_scheduled_date = models.DateTimeField(null=True, blank=True, verbose_name="Vカットラッピング予定日")
    post_processing_scheduled_date = models.DateTimeField(null=True, blank=True, verbose_name="後加工予定日")
    packing_scheduled_date = models.DateTimeField(null=True, blank=True, verbose_name="梱包予定日")
    decorative_board_scheduled_date = models.DateTimeField(null=True, blank=True, verbose_name="化粧板貼付予定日")
    decorative_board_cut_scheduled_date = models.DateTimeField(null=True, blank=True, verbose_name="化粧板カット予定日")
    
    # 各工程の着手時間
    slit_start_time = models.DateTimeField(null=True, blank=True, verbose_name="スリット着手時間")
    cut_start_time = models.DateTimeField(null=True, blank=True, verbose_name="カット着手時間")
    base_material_cut_start_time = models.DateTimeField(null=True, blank=True, verbose_name="基材カット着手時間")
    molder_start_time = models.DateTimeField(null=True, blank=True, verbose_name="モルダー着手時間")
    v_cut_lapping_start_time = models.DateTimeField(null=True, blank=True, verbose_name="Vカットラッピング着手時間")
    post_processing_start_time = models.DateTimeField(null=True, blank=True, verbose_name="後加工着手時間")
    packing_start_time = models.DateTimeField(null=True, blank=True, verbose_name="梱包着手時間")
    decorative_board_start_time = models.DateTimeField(null=True, blank=True, verbose_name="化粧板貼付着手時間")
    decorative_board_cut_start_time = models.DateTimeField(null=True, blank=True, verbose_name="化粧板カット着手時間")
    
    # 各工程の完了時間
    slit_completion_time = models.DateTimeField(null=True, blank=True, verbose_name="スリット完了時間")
    cut_completion_time = models.DateTimeField(null=True, blank=True, verbose_name="カット完了時間")
    base_material_cut_completion_time = models.DateTimeField(null=True, blank=True, verbose_name="基材カット完了時間")
    molder_completion_time = models.DateTimeField(null=True, blank=True, verbose_name="モルダー完了時間")
    v_cut_lapping_completion_time = models.DateTimeField(null=True, blank=True, verbose_name="Vカットラッピング完了時間")
    post_processing_completion_time = models.DateTimeField(null=True, blank=True, verbose_name="後加工完了時間")
    packing_completion_time = models.DateTimeField(null=True, blank=True, verbose_name="梱包完了時間")
    decorative_board_completion_time = models.DateTimeField(null=True, blank=True, verbose_name="化粧板貼付完了時間")
    decorative_board_cut_completion_time = models.DateTimeField(null=True, blank=True, verbose_name="化粧板カット完了時間")
    
    # 各工程の所要時間（分単位）
    slit_duration_minutes = models.PositiveIntegerField(null=True, blank=True, verbose_name="スリット所要時間（分）")
    cut_duration_minutes = models.PositiveIntegerField(null=True, blank=True, verbose_name="カット所要時間（分）")
    base_material_cut_duration_minutes = models.PositiveIntegerField(null=True, blank=True, verbose_name="基材カット所要時間（分）")
    molder_duration_minutes = models.PositiveIntegerField(null=True, blank=True, verbose_name="モルダー所要時間（分）")
    v_cut_lapping_duration_minutes = models.PositiveIntegerField(null=True, blank=True, verbose_name="Vカットラッピング所要時間（分）")
    post_processing_duration_minutes = models.PositiveIntegerField(null=True, blank=True, verbose_name="後加工所要時間（分）")
    packing_duration_minutes = models.PositiveIntegerField(null=True, blank=True, verbose_name="梱包所要時間（分）")
    decorative_board_duration_minutes = models.PositiveIntegerField(null=True, blank=True, verbose_name="化粧板貼付所要時間（分）")
    decorative_board_cut_duration_minutes = models.PositiveIntegerField(null=True, blank=True, verbose_name="化粧板カット所要時間（分）")
    
    # 各工程のステータス
    slit_status = models.CharField(max_length=20, choices=DETAILED_STATUS_CHOICES, default='未着手', verbose_name="スリットステータス")
    cut_status = models.CharField(max_length=20, choices=DETAILED_STATUS_CHOICES, default='未着手', verbose_name="カットステータス")
    base_material_cut_status = models.CharField(max_length=20, choices=DETAILED_STATUS_CHOICES, default='未着手', verbose_name="基材カットステータス")
    molder_status = models.CharField(max_length=20, choices=DETAILED_STATUS_CHOICES, default='未着手', verbose_name="モルダーステータス")
    v_cut_lapping_status = models.CharField(max_length=20, choices=DETAILED_STATUS_CHOICES, default='未着手', verbose_name="Vカットラッピングステータス")
    post_processing_status = models.CharField(max_length=20, choices=DETAILED_STATUS_CHOICES, default='未着手', verbose_name="後加工ステータス")
    packing_status = models.CharField(max_length=20, choices=DETAILED_STATUS_CHOICES, default='未着手', verbose_name="梱包ステータス")
    decorative_board_status = models.CharField(max_length=20, choices=DETAILED_STATUS_CHOICES, default='未着手', verbose_name="化粧板貼付ステータス")
    decorative_board_cut_status = models.CharField(max_length=20, choices=DETAILED_STATUS_CHOICES, default='未着手', verbose_name="化粧板カットステータス")
    
    # 各工程の作業者ID（作業者インターフェースで入力されたID）
    slit_worker_id = models.CharField(max_length=100, null=True, blank=True, verbose_name="スリット作業者ID")
    cut_worker_id = models.CharField(max_length=100, null=True, blank=True, verbose_name="カット作業者ID")
    base_material_cut_worker_id = models.CharField(max_length=100, null=True, blank=True, verbose_name="基材カット作業者ID")
    molder_worker_id = models.CharField(max_length=100, null=True, blank=True, verbose_name="モルダー作業者ID")
    v_cut_lapping_worker_id = models.CharField(max_length=100, null=True, blank=True, verbose_name="Vカットラッピング作業者ID")
    post_processing_worker_id = models.CharField(max_length=100, null=True, blank=True, verbose_name="後加工作業者ID")
    packing_worker_id = models.CharField(max_length=100, null=True, blank=True, verbose_name="梱包作業者ID")
    decorative_board_worker_id = models.CharField(max_length=100, null=True, blank=True, verbose_name="化粧板貼付作業者ID")
    decorative_board_cut_worker_id = models.CharField(max_length=100, null=True, blank=True, verbose_name="化粧板カット作業者ID")
    
    remarks = models.TextField(blank=True, null=True, verbose_name="備考")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="作成日時")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新日時")

    def __str__(self):
        return f"{self.plan_name} ({self.product_code})"

    class Meta:
        verbose_name = "生産計画"
        verbose_name_plural = "生産計画"
        ordering = ['-planned_start_datetime']

class PartsUsed(models.Model):
    """
    使用部品モデル
    """
    id = models.UUIDField(primary_key=True, default=uuid7, editable=False) # UUIDv7を使用
    # production_plan = models.ForeignKey(ProductionPlan, on_delete=models.CASCADE, related_name='parts_used', verbose_name="生産計画")
    # TODO: master.Partモデルが定義されたらForeignKeyに変更する
    # part = models.ForeignKey('master.Part', on_delete=models.PROTECT, verbose_name="部品")
    production_plan = models.CharField(
        max_length=255, # 生産計画の名前やIDを文字列として保存
        verbose_name="生産計画識別子",
        help_text="関連する生産計画の名前やIDなどの識別子を文字列で記録します。"
    )
    part_code = models.CharField(max_length=100, verbose_name="部品コード (仮)")
    warehouse = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        verbose_name="使用倉庫"
    ) # 部品がどの倉庫から使用されるか
    quantity_used = models.PositiveIntegerField(verbose_name="使用数量")
    used_datetime = models.DateTimeField(default=timezone.now, verbose_name="使用日時")
    remarks = models.TextField(blank=True, null=True, verbose_name="備考")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="作成日時")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新日時")

    def __str__(self):
        # production_plan は文字列フィールドになったため、直接参照します。
        # 以前のように .plan_name でアクセスすることはできません。
        # 表示する文字列が生産計画のIDや名前を直接含むことを想定しています。
        warehouse_display = f" from Warehouse: {self.warehouse}" if self.warehouse else ""
        return f"{self.part_code} - {self.quantity_used} units for P.Plan: {self.production_plan}{warehouse_display}"

    class Meta:
        verbose_name = "使用部品"
        verbose_name_plural = "使用部品"
        ordering = ['-used_datetime']

class MaterialAllocation(models.Model):
    """
    材料引当モデル
    """
    id = models.UUIDField(primary_key=True, default=uuid7, editable=False) # UUIDv7を使用
    STATUS_CHOICES = [
        ('ALLOCATED', '引当済'),
        ('ISSUED', '出庫済'),
        ('RETURNED', '返却済'),
    ]

    production_plan = models.ForeignKey(ProductionPlan, on_delete=models.CASCADE, related_name='material_allocations', verbose_name="生産計画")
    # TODO: master.Materialモデルが定義されたらForeignKeyに変更する
    # material = models.ForeignKey('master.Material', on_delete=models.PROTECT, verbose_name="材料")
    material_code = models.CharField(max_length=100, verbose_name="材料コード (仮)")
    allocated_quantity = models.PositiveIntegerField(verbose_name="引当数量")
    allocation_datetime = models.DateTimeField(default=timezone.now, verbose_name="引当日時")
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='ALLOCATED',
        verbose_name="ステータス"
    )
    remarks = models.TextField(blank=True, null=True, verbose_name="備考")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="作成日時")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新日時")

    def __str__(self):
        return f"{self.material_code} - {self.allocated_quantity} units for {self.production_plan.plan_name}"

    class Meta:
        verbose_name = "材料引当"
        verbose_name_plural = "材料引当"
        ordering = ['-allocation_datetime']

class WorkProgress(models.Model):
    """
    作業進捗モデル
    """
    id = models.UUIDField(primary_key=True, default=uuid7, editable=False) # UUIDv7を使用
    STATUS_CHOICES = [
        ('NOT_STARTED', '未開始'),
        ('IN_PROGRESS', '進行中'),
        ('COMPLETED', '完了'),
        ('PAUSED', '一時停止'),
    ]

    production_plan = models.ForeignKey(ProductionPlan, on_delete=models.CASCADE, related_name='work_progresses', verbose_name="生産計画")
    process_step = models.CharField(max_length=100, verbose_name="工程ステップ") # 例: '組立', '塗装', '検査'
    operator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="作業者"
    )
    start_datetime = models.DateTimeField(null=True, blank=True, verbose_name="開始日時")
    end_datetime = models.DateTimeField(null=True, blank=True, verbose_name="終了日時")
    quantity_completed = models.PositiveIntegerField(default=0, verbose_name="完了数量 (良品数)") # This will store the good quantity
    actual_reported_quantity = models.PositiveIntegerField(null=True, blank=True, verbose_name="実績報告数量 (総生産数)")
    defective_reported_quantity = models.PositiveIntegerField(null=True, blank=True, verbose_name="不良報告数量")
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='NOT_STARTED',
        verbose_name="ステータス"
    )
    remarks = models.TextField(blank=True, null=True, verbose_name="備考")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="作成日時")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新日時")

    def __str__(self):
        return f"{self.production_plan.plan_name} - {self.process_step} ({self.get_status_display()})"

    class Meta:
        verbose_name = "作業進捗"
        verbose_name_plural = "作業進捗"
        ordering = ['production_plan', 'start_datetime']

class ProcessSchedule(models.Model):
    """
    工程スケジュールモデル
    """
    id = models.UUIDField(primary_key=True, default=uuid7, editable=False)
    STATUS_CHOICES = [
        ('未着手', '未着手'),
        ('進行中', '進行中'),
        ('完了', '完了'),
        ('遅延', '遅延'),
    ]
    
    production_plan = models.ForeignKey(ProductionPlan, on_delete=models.CASCADE, related_name='process_schedules', verbose_name="生産計画")
    process_name = models.CharField(max_length=100, verbose_name="工程名")
    scheduled_start_date = models.DateField(verbose_name="予定開始日")
    scheduled_end_date = models.DateField(verbose_name="予定終了日")
    actual_start_date = models.DateField(null=True, blank=True, verbose_name="実績開始日")
    actual_end_date = models.DateField(null=True, blank=True, verbose_name="実績終了日")
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='未着手',
        verbose_name="ステータス"
    )
    remarks = models.TextField(blank=True, null=True, verbose_name="備考")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="作成日時")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新日時")

    def __str__(self):
        return f"{self.production_plan.plan_name} - {self.process_name} ({self.status})"

    class Meta:
        verbose_name = "工程スケジュール"
        verbose_name_plural = "工程スケジュール"
        ordering = ['production_plan', 'scheduled_start_date']

class Kaizen(models.Model):
    """
    改善提案モデル
    """
    id = models.UUIDField(primary_key=True, default=uuid7, editable=False)
    STATUS_CHOICES = [
        ('提案中', '提案中'),
        ('検討中', '検討中'),
        ('実装中', '実装中'),
        ('完了', '完了'),
        ('却下', '却下'),
    ]
    
    PRIORITY_CHOICES = [
        ('高', '高'),
        ('中', '中'),
        ('低', '低'),
    ]
    
    title = models.CharField(max_length=200, verbose_name="改善提案タイトル")
    description = models.TextField(verbose_name="改善提案内容")
    proposer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="提案者"
    )
    production_plan = models.ForeignKey(
        ProductionPlan,
        on_delete=models.CASCADE,
        related_name='kaizen_proposals',
        null=True,
        blank=True,
        verbose_name="関連生産計画"
    )
    process_step = models.CharField(max_length=100, null=True, blank=True, verbose_name="関連工程")
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='提案中',
        verbose_name="ステータス"
    )
    priority = models.CharField(
        max_length=20,
        choices=PRIORITY_CHOICES,
        default='中',
        verbose_name="優先度"
    )
    expected_effect = models.TextField(null=True, blank=True, verbose_name="期待効果")
    actual_effect = models.TextField(null=True, blank=True, verbose_name="実際の効果")
    implementation_date = models.DateField(null=True, blank=True, verbose_name="実装日")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="作成日時")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新日時")

    def __str__(self):
        return f"{self.title} ({self.get_status_display()})"

    class Meta:
        verbose_name = "改善提案"
        verbose_name_plural = "改善提案"
        ordering = ['-created_at']
