from rest_framework import serializers
from .models import ProductionPlan, PartsUsed, MaterialAllocation, WorkProgress

class ProductionPlanSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source='get_status_display', read_only=True) # 表示名用
    # status フィールドはモデルの定義に従い、内部キーを返します。

    # 工程別ステータスフィールド（WorkProgressから計算）
    slit_status = serializers.SerializerMethodField()
    cut_status = serializers.SerializerMethodField()
    base_material_cut_status = serializers.SerializerMethodField()
    molder_status = serializers.SerializerMethodField()
    v_cut_lapping_status = serializers.SerializerMethodField()
    post_processing_status = serializers.SerializerMethodField()
    packing_status = serializers.SerializerMethodField()
    decorative_board_status = serializers.SerializerMethodField()
    decorative_board_cut_status = serializers.SerializerMethodField()

    class Meta:
        model = ProductionPlan
        fields = [
            'id',
            'plan_name',
            'product_code',
            'production_plan', # FK to another ProductionPlan (referenced plan)
            'planned_quantity',
            'planned_start_datetime',
            'planned_end_datetime',
            'actual_start_datetime',
            'actual_end_datetime',
            'status', # ステータスの内部キー (例: 'PENDING', 'IN_PROGRESS')
            'status_display', # ステータスの表示名 (例: '未着手', '進行中')
            'remarks',
            'created_at',
            'updated_at',
            # Extended fields for Gantt chart (18 additional fields)
            'qr_code',
            'reception_no',
            'additional_no',
            'customer_name',
            'site_name',
            'additional_content',
            'planned_shipment_date',
            'process',
            'product_name',
            'manufacturing_scheduled_date',
            'slit_scheduled_date',
            'cut_scheduled_date',
            'base_material_cut_scheduled_date',
            'molder_scheduled_date',
            'vcut_wrapping_scheduled_date',
            'post_processing_scheduled_date',
            'packing_scheduled_date',
            'delivery_date',
            'veneer_scheduled_date',
            'cut_veneer_scheduled_date',
            # 工程別ステータス (9 fields)
            'slit_status',
            'cut_status',
            'base_material_cut_status',
            'molder_status',
            'v_cut_lapping_status',
            'post_processing_status',
            'packing_status',
            'decorative_board_status',
            'decorative_board_cut_status',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'status_display',
                           'slit_status', 'cut_status', 'base_material_cut_status',
                           'molder_status', 'v_cut_lapping_status', 'post_processing_status',
                           'packing_status', 'decorative_board_status', 'decorative_board_cut_status']

    def _get_process_status(self, obj, process_name):
        """
        WorkProgressから指定工程の最新ステータスを取得
        """
        try:
            work_progress = WorkProgress.objects.filter(
                production_plan=obj,
                process_step=process_name
            ).order_by('-start_datetime').first()

            if not work_progress:
                return '未着手'

            status_map = {
                'PENDING': '未着手',
                'IN_PROGRESS': '着手中',
                'COMPLETED': '完了',
                'DELAYED': '遅延',
                'ON_HOLD': '保留',
                'CANCELLED': '中止'
            }
            return status_map.get(work_progress.status, '未着手')
        except Exception:
            return '未着手'

    def get_slit_status(self, obj):
        return self._get_process_status(obj, 'スリット')

    def get_cut_status(self, obj):
        return self._get_process_status(obj, 'カット')

    def get_base_material_cut_status(self, obj):
        return self._get_process_status(obj, '基材カット')

    def get_molder_status(self, obj):
        return self._get_process_status(obj, 'モルダー')

    def get_v_cut_lapping_status(self, obj):
        return self._get_process_status(obj, 'Vカットラッピング')

    def get_post_processing_status(self, obj):
        return self._get_process_status(obj, '後加工')

    def get_packing_status(self, obj):
        return self._get_process_status(obj, '梱包')

    def get_decorative_board_status(self, obj):
        return self._get_process_status(obj, '化粧板貼付')

    def get_decorative_board_cut_status(self, obj):
        return self._get_process_status(obj, '化粧板カット')

    def validate(self, data):
        """
        Check that planned_start_datetime is before planned_end_datetime.
        Handles both create (POST) and partial update (PATCH) scenarios.
        """
        # On updates (PATCH), self.instance will be populated.
        # On creates (POST), self.instance will be None.

        # Determine the start and end datetimes to validate.
        # Use the incoming data if present, otherwise fall back to the existing instance's value (for PATCH).
        if self.instance:  # This is an update
            planned_start = data.get('planned_start_datetime', self.instance.planned_start_datetime)
            planned_end = data.get('planned_end_datetime', self.instance.planned_end_datetime)
        else:  # This is a create
            # For create, model fields planned_start_datetime and planned_end_datetime are required.
            # DRF would have raised a "this field is required" error already if not present.
            planned_start = data.get('planned_start_datetime')
            planned_end = data.get('planned_end_datetime')

        # Only proceed with validation if both dates are available.
        # This check is mostly for safety; for create, they are required by the model,
        # and for update, we've fetched them from data or instance.
        if planned_start is not None and planned_end is not None:
            if planned_start >= planned_end:
                # The error message points to 'planned_end_datetime'.
                # A more general message could be:
                # "Planned start datetime must be before planned end datetime."
                raise serializers.ValidationError({
                    "planned_end_datetime": "Planned end datetime must be after planned start datetime."
                })
        return data

class PartsUsedSerializer(serializers.ModelSerializer):
    """
    使用部品モデルのためのシリアライザ
    """
    class Meta:
        model = PartsUsed
        fields = [
            'id',
            'production_plan', # 生産計画へのForeignKey
            'part_code',
            'warehouse', # 追加
            'quantity_used',
            'used_datetime',
            'remarks',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

class RequiredPartSerializer(serializers.Serializer):
    """
    必要部品情報を表現するためのシリアライザ。
    特定のモデルに直接紐づかないため、serializers.Serializerを継承します。
    """
    part_code = serializers.CharField(max_length=100)
    part_name = serializers.CharField(max_length=255, help_text="部品名")
    # required_quantity の型 (DecimalField, IntegerField など) は、
    # PartsUsed.quantity_used is PositiveIntegerField, MaterialAllocation.allocated_quantity is PositiveIntegerField.
    required_quantity = serializers.IntegerField(help_text="必要数量")
    unit = serializers.CharField(max_length=50, help_text="単位")
    inventory_quantity = serializers.IntegerField(help_text="現在の在庫数量")
    already_allocated_quantity = serializers.IntegerField(help_text="既にこの生産計画に引当済の数量", default=0)
    warehouse = serializers.CharField(max_length=255, required=False, allow_blank=True, allow_null=True, help_text="部品が使用される倉庫")

    # このシリアライザは読み取り専用のデータを想定しています。
    # ビュー側で `data_for_serializer` を構築する際に、これらのフィールドに合致するデータを提供します。

class MaterialAllocationSerializer(serializers.ModelSerializer):
    """
    材料引当モデルのためのシリアライザ
    """
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    production_plan_name = serializers.CharField(source='production_plan.plan_name', read_only=True)

    class Meta:
        model = MaterialAllocation
        fields = [
            'id',
            'production_plan',
            'production_plan_name',
            'material_code',
            'allocated_quantity',
            'allocation_datetime',
            'status',
            'status_display',
            'remarks',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'status_display', 'production_plan_name']


class WorkProgressSerializer(serializers.ModelSerializer):
    """
    作業進捗モデルのためのシリアライザ
    """
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    production_plan_name = serializers.CharField(source='production_plan.plan_name', read_only=True)
    operator_username = serializers.CharField(source='operator.username', read_only=True, allow_null=True)

    class Meta:
        model = WorkProgress
        fields = [
            'id', 'production_plan', 'production_plan_name', 'process_step',
            'operator', 'operator_username', 'start_datetime', 'end_datetime',
            'quantity_completed', 'actual_reported_quantity',
            'defective_reported_quantity', 'status', 'status_display', 'remarks',
            'created_at', 'updated_at',
        ]
        read_only_fields = [
            'id', 'created_at', 'updated_at', 'status_display',
            'production_plan_name', 'operator_username'
        ]

    def validate(self, data):
        """
        Check that start_datetime is before end_datetime.
        Handles both create (POST) and partial update (PATCH) scenarios.
        """
        if self.instance:  # This is an update
            start = data.get('start_datetime', self.instance.start_datetime)
            end = data.get('end_datetime', self.instance.end_datetime)
        else:  # This is a create
            start = data.get('start_datetime')
            end = data.get('end_datetime')

        if start and end:
            if start >= end:
                raise serializers.ValidationError({
                    "end_datetime": "End datetime must be after start datetime."
                })
        return data