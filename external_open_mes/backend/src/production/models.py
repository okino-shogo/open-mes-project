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

    # 各工程のステータス選択肢
    PROCESS_STATUS_CHOICES = [
        ('PENDING', '未着手'),
        ('IN_PROGRESS', '着手中'),
        ('COMPLETED', '完了'),
        ('DELAYED', '遅延'),
        ('ON_HOLD', '保留'),
    ]

    plan_name = models.CharField(max_length=255, null=True, blank=True, verbose_name="計画名")
    # TODO: master.Productモデルが定義されたらForeignKeyに変更する
    # product = models.ForeignKey('master.Product', on_delete=models.PROTECT, verbose_name="製品")
    product_code = models.CharField(max_length=100, null=True, blank=True, verbose_name="製品コード (仮)")
    production_plan = models.CharField(
        max_length=255, # 参照する計画名などを想定
        null=True,
        blank=True,
        verbose_name="参照生産計画",
        help_text="参照する生産計画の名前や識別子を文字列で記録します。"
    )
    planned_quantity = models.PositiveIntegerField(null=True, blank=True, verbose_name="計画数量")
    planned_start_datetime = models.DateTimeField(null=True, blank=True, verbose_name="計画開始日時")
    planned_end_datetime = models.DateTimeField(null=True, blank=True, verbose_name="計画終了日時")
    actual_start_datetime = models.DateTimeField(null=True, blank=True, verbose_name="実績開始日時")
    actual_end_datetime = models.DateTimeField(null=True, blank=True, verbose_name="実績終了日時")
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='PENDING',
        verbose_name="ステータス"
    )
    remarks = models.TextField(blank=True, null=True, verbose_name="備考")

    # === 新規追加フィールド (画像カラム順序対応) ===

    # 基本情報
    qr_code = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name="QRコード",
        help_text="生産計画識別用QRコード"
    )
    reception_no = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="受付No",
        help_text="受付番号"
    )
    additional_no = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="追加No",
        help_text="追加番号"
    )

    # 取引先・現場情報
    customer_name = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name="得意先名",
        help_text="取引先企業名"
    )
    site_name = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name="現場名",
        help_text="作業現場名称"
    )

    # 追加情報
    additional_content = models.TextField(
        blank=True,
        null=True,
        verbose_name="追加内容",
        help_text="追加作業内容や特記事項"
    )

    # 日程情報
    planned_shipment_date = models.DateField(
        null=True,
        blank=True,
        verbose_name="出荷予定日",
        help_text="製品出荷予定日"
    )
    delivery_date = models.DateField(
        null=True,
        blank=True,
        verbose_name="納品日",
        help_text="顧客への納品日"
    )

    # 工程情報
    process = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="工程",
        help_text="製造工程名"
    )

    # 品名
    product_name = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="品名",
        help_text="製品名称（例: WD (V)(ラ)、AW (V)）"
    )

    # 製造予定日
    manufacturing_scheduled_date = models.DateField(
        null=True,
        blank=True,
        verbose_name="製造予定日",
        help_text="製造完了予定日（工程日付計算の基準）"
    )

    # 各工程予定日
    slit_scheduled_date = models.DateField(
        null=True,
        blank=True,
        verbose_name="スリット予定日"
    )
    cut_scheduled_date = models.DateField(
        null=True,
        blank=True,
        verbose_name="カット予定日"
    )
    base_material_cut_scheduled_date = models.DateField(
        null=True,
        blank=True,
        verbose_name="基材カット予定日"
    )
    molder_scheduled_date = models.DateField(
        null=True,
        blank=True,
        verbose_name="モルダー予定日"
    )
    vcut_wrapping_scheduled_date = models.DateField(
        null=True,
        blank=True,
        verbose_name="Vカットラッピング予定日"
    )
    post_processing_scheduled_date = models.DateField(
        null=True,
        blank=True,
        verbose_name="後加工予定日"
    )
    packing_scheduled_date = models.DateField(
        null=True,
        blank=True,
        verbose_name="梱包予定日"
    )
    veneer_scheduled_date = models.DateField(
        null=True,
        blank=True,
        verbose_name="化粧板貼予定日"
    )
    cut_veneer_scheduled_date = models.DateField(
        null=True,
        blank=True,
        verbose_name="カット化粧板予定日"
    )

    # 各工程開始日時
    slit_started_datetime = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="スリット開始日時"
    )
    cut_started_datetime = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="カット開始日時"
    )
    base_material_cut_started_datetime = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="基材カット開始日時"
    )
    molder_started_datetime = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="モルダー開始日時"
    )
    vcut_wrapping_started_datetime = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Vカットラッピング開始日時"
    )
    post_processing_started_datetime = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="後加工開始日時"
    )
    packing_started_datetime = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="梱包開始日時"
    )
    veneer_started_datetime = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="化粧板貼開始日時"
    )
    cut_veneer_started_datetime = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="カット化粧板開始日時"
    )

    # 各工程完了日
    slit_completed_date = models.DateField(
        null=True,
        blank=True,
        verbose_name="スリット完了日"
    )
    cut_completed_date = models.DateField(
        null=True,
        blank=True,
        verbose_name="カット完了日"
    )
    base_material_cut_completed_date = models.DateField(
        null=True,
        blank=True,
        verbose_name="基材カット完了日"
    )
    molder_completed_date = models.DateField(
        null=True,
        blank=True,
        verbose_name="モルダー完了日"
    )
    vcut_wrapping_completed_date = models.DateField(
        null=True,
        blank=True,
        verbose_name="Vカットラッピング完了日"
    )
    post_processing_completed_date = models.DateField(
        null=True,
        blank=True,
        verbose_name="後加工完了日"
    )
    packing_completed_date = models.DateField(
        null=True,
        blank=True,
        verbose_name="梱包完了日"
    )
    veneer_completed_date = models.DateField(
        null=True,
        blank=True,
        verbose_name="化粧板貼完了日"
    )
    cut_veneer_completed_date = models.DateField(
        null=True,
        blank=True,
        verbose_name="カット化粧板完了日"
    )

    # 各工程ステータス (フロントエンドとの整合性のため追加)
    slit_status = models.CharField(
        max_length=20,
        choices=PROCESS_STATUS_CHOICES,
        default='PENDING',
        verbose_name="スリットステータス"
    )
    cut_status = models.CharField(
        max_length=20,
        choices=PROCESS_STATUS_CHOICES,
        default='PENDING',
        verbose_name="カットステータス"
    )
    base_material_cut_status = models.CharField(
        max_length=20,
        choices=PROCESS_STATUS_CHOICES,
        default='PENDING',
        verbose_name="基材カットステータス"
    )
    molder_status = models.CharField(
        max_length=20,
        choices=PROCESS_STATUS_CHOICES,
        default='PENDING',
        verbose_name="モルダーステータス"
    )
    v_cut_lapping_status = models.CharField(
        max_length=20,
        choices=PROCESS_STATUS_CHOICES,
        default='PENDING',
        verbose_name="Vカットラッピングステータス"
    )
    post_processing_status = models.CharField(
        max_length=20,
        choices=PROCESS_STATUS_CHOICES,
        default='PENDING',
        verbose_name="後加工ステータス"
    )
    packing_status = models.CharField(
        max_length=20,
        choices=PROCESS_STATUS_CHOICES,
        default='PENDING',
        verbose_name="梱包ステータス"
    )
    decorative_board_status = models.CharField(
        max_length=20,
        choices=PROCESS_STATUS_CHOICES,
        default='PENDING',
        verbose_name="化粧板貼ステータス"
    )
    decorative_board_cut_status = models.CharField(
        max_length=20,
        choices=PROCESS_STATUS_CHOICES,
        default='PENDING',
        verbose_name="カット化粧板ステータス"
    )

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

    WORK_TYPE_CHOICES = [
        ('start', '開始'),
        ('complete', '完了'),
    ]

    production_plan = models.ForeignKey(ProductionPlan, on_delete=models.CASCADE, related_name='work_progresses', verbose_name="生産計画")
    process_step = models.CharField(max_length=100, verbose_name="工程ステップ") # 例: '組立', '塗装', '検査'
    process_type = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        verbose_name="工程タイプ",
        help_text="例: slit, cut, base_material_cut など"
    )
    work_type = models.CharField(
        max_length=20,
        choices=WORK_TYPE_CHOICES,
        null=True,
        blank=True,
        verbose_name="作業種別",
        help_text="開始操作か完了操作か"
    )
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

    # 取り消し関連フィールド
    is_cancelled = models.BooleanField(
        default=False,
        verbose_name="取り消し済み",
        help_text="この操作が取り消されたかどうか"
    )
    cancelled_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="取り消し日時",
        help_text="操作が取り消された日時"
    )
    cancelled_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='cancelled_work_progresses',
        verbose_name="取り消し実行者"
    )

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="作成日時")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新日時")

    def __str__(self):
        return f"{self.production_plan.plan_name} - {self.process_step} ({self.get_status_display()})"

    class Meta:
        verbose_name = "作業進捗"
        verbose_name_plural = "作業進捗"
        ordering = ['production_plan', 'start_datetime']
