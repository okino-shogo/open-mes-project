from rest_framework import viewsets
# from rest_framework import permissions # Uncomment if you want to add permissions
from rest_framework.pagination import PageNumberPagination # Import PageNumberPagination
from rest_framework import status # HTTPステータスコードをインポート
from rest_framework.decorators import action # actionデコレータをインポート
from rest_framework.response import Response # Responseをインポート
from .models import ProductionPlan, PartsUsed, MaterialAllocation # Add MaterialAllocation
from .models import WorkProgress # Import WorkProgress
from .serializers import ProductionPlanSerializer, PartsUsedSerializer, RequiredPartSerializer
from inventory.rest_views import StandardResultsSetPagination # inventoryアプリのページネーションクラスをインポート
from django.db.models import Q # Qオブジェクトをインポート
from inventory.models import Inventory, StockMovement, SalesOrder # Add StockMovement and SalesOrder
from rest_framework.filters import OrderingFilter # OrderingFilterをインポート
from django.utils.dateparse import parse_datetime # 日時文字列のパース用
from django.utils import timezone # timezoneをインポート
from django.db import transaction # トランザクションのためにインポート
from django.shortcuts import get_object_or_404 # オブジェクト取得のためにインポート
# from .models import Product, BillOfMaterialItem # BOMに関連するモデル (仮のインポート、実際には適切なモデルを定義・インポートしてください)
# from .serializers import RequiredPartSerializer # BOM部品用のシリアライザ (仮のインポート)

# Define a constant for the default finished goods warehouse
DEFAULT_FINISHED_GOODS_WAREHOUSE = "FG-MAIN" # TODO: Make this configurable

# Define a pagination class specifically for Production Plans API
class ProductionPlanApiPagination(PageNumberPagination):
    page_size = 100  # Default number of items per page
    page_size_query_param = 'page_size'  # Allow client to override page_size via query param
    max_page_size = 200  # Maximum page size allowed

class ProductionPlanViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows Production Plans to be viewed or created.
    """
    serializer_class = ProductionPlanSerializer
    pagination_class = ProductionPlanApiPagination # Use the custom pagination class for Production Plans
    # permission_classes = [permissions.IsAuthenticated] # Example: Add authentication
    filter_backends = [OrderingFilter] # OrderingFilterを追加 (他のフィルターがあればそれもリストに含める)
    ordering_fields = [
        'plan_name', 'product_code', 'planned_quantity', 
        'planned_start_datetime', 'status'
    ] # ソート可能なフィールドを指定
    ordering = ['-planned_start_datetime'] # デフォルトのソート順

    def get_queryset(self):
        queryset = ProductionPlan.objects.all() # Start with all objects

        # Get query parameters for filtering
        plan_name = self.request.query_params.get('plan_name')
        product_code = self.request.query_params.get('product_code')
        # status = self.request.query_params.get('status') # Keep for single status, or remove if status__in is primary
        statuses_in_str = self.request.query_params.get('status__in') # New: for multiple statuses
        production_plan_ref = self.request.query_params.get('production_plan_ref') # For parent plan ID search
        planned_start_after = self.request.query_params.get('planned_start_datetime_after')
        planned_start_before = self.request.query_params.get('planned_start_datetime_before')

        filters = Q()
        if plan_name:
            filters &= Q(plan_name__icontains=plan_name)
        if product_code:
            filters &= Q(product_code__icontains=product_code)
        
        # Handle status__in for multiple statuses
        if statuses_in_str:
            status_list = [status.strip() for status in statuses_in_str.split(',') if status.strip()]
            if status_list:
                filters &= Q(status__in=status_list)
        # else: # Optional: handle single 'status' param if still needed and status__in is not present
        #     single_status = self.request.query_params.get('status')
        #     if single_status:
        #         filters &= Q(status=single_status)

        if production_plan_ref:
            # 'production_plan' is the CharField in the model storing the reference
            filters &= Q(production_plan__icontains=production_plan_ref)
        
        if planned_start_after:
            dt_after = parse_datetime(planned_start_after)
            if dt_after:
                filters &= Q(planned_start_datetime__gte=dt_after)
        
        if planned_start_before:
            dt_before = parse_datetime(planned_start_before)
            if dt_before:
                filters &= Q(planned_start_datetime__lte=dt_before)
            
        # Apply filters if any
        if filters:
            queryset = queryset.filter(filters)
            
        # OrderingFilterが 'ordering' クエリパラメータとViewSetの 'ordering'/'ordering_fields' 属性に基づいて
        # ソートを処理するため、ここでの明示的な .order_by() は不要です。
        return queryset

    @action(detail=True, methods=['get'], url_path='required-parts')
    def required_parts(self, request, pk=None):
        """
        特定の生産計画に必要な部品リストを返します。
        このリストは PartsUsed モデルから取得されます。
        """
        production_plan_instance = self.get_object() # Gets ProductionPlan by its ID (pk)

        # PartsUsed.production_plan (CharField) links to ProductionPlan.production_plan (CharField).
        plan_identifier_for_parts = production_plan_instance.production_plan # This is the CharField on ProductionPlan model

        if not plan_identifier_for_parts:
            return Response({
                "detail": f"生産計画 '{production_plan_instance.plan_name}' (ID: {production_plan_instance.id}) には、部品リストを特定するための参照識別子（production_planフィールド）が設定されていません。"
            }, status=404)

        # Query PartsUsed based on this string identifier
        parts_used_queryset = PartsUsed.objects.filter(production_plan=plan_identifier_for_parts)

        if not parts_used_queryset.exists():
            return Response({
                "detail": f"生産計画 '{production_plan_instance.plan_name}' (ID: {production_plan_instance.id}) の参照識別子 '{plan_identifier_for_parts}' に紐づく使用部品情報は見つかりませんでした。"
            }, status=404)

        # Prepare data for the RequiredPartSerializer
        data_for_serializer = []
        from django.db.models import Sum # Ensure Sum is imported
        for part_used_item in parts_used_queryset:
            part_code = part_used_item.part_code
            part_specific_warehouse = part_used_item.warehouse # Warehouse from PartsUsed
            current_inventory_quantity = 0

            if part_specific_warehouse:
                # If a specific warehouse is designated for the part, get inventory from that warehouse.
                try:
                    inventory_item = Inventory.objects.get(
                        part_number=part_code,
                        warehouse=part_specific_warehouse,
                        is_active=True,
                        is_allocatable=True
                    )
                    current_inventory_quantity = inventory_item.available_quantity
                except Inventory.DoesNotExist:
                    current_inventory_quantity = 0
                except Inventory.MultipleObjectsReturned:
                    # This case implies multiple inventory entries for the same part in the same warehouse.
                    # Summing them up is a safe approach.
                    inventory_items = Inventory.objects.filter(
                        part_number=part_code,
                        warehouse=part_specific_warehouse,
                        is_active=True,
                        is_allocatable=True
                    )
                    for inv_item in inventory_items:
                        current_inventory_quantity += inv_item.available_quantity
                    if inventory_items.count() > 1:
                        print(f"Warning: Multiple inventory records found for part {part_code} in warehouse {part_specific_warehouse}. Summing quantities.")
            else:
                # If no specific warehouse is designated for the part in PartsUsed,
                # sum available inventory from all warehouses for that part.
                inventory_items = Inventory.objects.filter(
                    part_number=part_code,
                    is_active=True,
                    is_allocatable=True
                )
                for inv_item in inventory_items:
                    current_inventory_quantity += inv_item.available_quantity

            # Calculate already allocated quantity for this part for the current production plan
            already_allocated_for_part = MaterialAllocation.objects.filter(
                production_plan=production_plan_instance, # The specific plan instance for the popup
                material_code=part_code
            ).aggregate(total_allocated=Sum('allocated_quantity'))['total_allocated'] or 0


            data_for_serializer.append({
                "part_code": part_code,
                "part_name": f"{part_code} (名称は別途マスタ参照)", # Placeholder for part_name
                "required_quantity": part_used_item.quantity_used, # Using quantity_used from PartsUsed
                "unit": "個",  # Placeholder for unit, e.g., '個' (pieces)
                "inventory_quantity": current_inventory_quantity,
                "warehouse": part_specific_warehouse,
                "already_allocated_quantity": already_allocated_for_part
            })

        serializer = RequiredPartSerializer(data=data_for_serializer, many=True)
        serializer.is_valid(raise_exception=True) # Ensure data conforms to serializer structure
        return Response(serializer.data)

    @action(detail=True, methods=['post'], url_path='allocate-materials')
    def allocate_materials(self, request, pk=None):
        """
        Allocates materials for a specific production plan.
        Updates inventory reservations and creates MaterialAllocation records.
        """
        production_plan = self.get_object() # Get the ProductionPlan instance

        allocations_data = request.data.get('allocations')

        if not isinstance(allocations_data, list):
            return Response({"error": "Allocations data must be a list."}, status=status.HTTP_400_BAD_REQUEST)
        if not allocations_data:
            return Response({"error": "Allocations list cannot be empty."}, status=status.HTTP_400_BAD_REQUEST)

        processed_allocations_summary = []
        errors = []

        try:
            with transaction.atomic():
                for alloc_item_data in allocations_data:
                    part_number = alloc_item_data.get('part_number')
                    warehouse = alloc_item_data.get('warehouse')
                    quantity_to_allocate = alloc_item_data.get('quantity_to_allocate')

                    if not all([part_number, warehouse, quantity_to_allocate is not None]):
                        errors.append(f"Missing data for allocation item (part_number, warehouse, or quantity_to_allocate): {alloc_item_data}")
                        continue
                    
                    try:
                        quantity_to_allocate = int(quantity_to_allocate)
                        if quantity_to_allocate <= 0:
                            # Allow 0 for cases where user explicitly sets it, but skip processing
                            if quantity_to_allocate < 0:
                                errors.append(f"Quantity to allocate must be non-negative for {part_number}.")
                            continue # Skip if 0 or negative after explicit error for < 0
                    except ValueError:
                        errors.append(f"Invalid quantity for {part_number}.")
                        continue

                    try:
                        inventory_item = Inventory.objects.select_for_update().get(
                            part_number=part_number,
                            warehouse=warehouse
                        )
                    except Inventory.DoesNotExist:
                        errors.append(f"Inventory not found for part '{part_number}' in warehouse '{warehouse}'.")
                        continue
                    
                    if not inventory_item.is_active or not inventory_item.is_allocatable:
                        errors.append(f"Inventory for part '{part_number}' in warehouse '{warehouse}' is not active or allocatable.")
                        continue

                    if inventory_item.available_quantity < quantity_to_allocate:
                        errors.append(
                            f"Insufficient available stock for part '{part_number}' in warehouse '{warehouse}'. "
                            f"Required: {quantity_to_allocate}, Available: {inventory_item.available_quantity}"
                        )
                        continue

                    # Reserve inventory
                    inventory_item.reserved += quantity_to_allocate
                    inventory_item.save()

                    # Create MaterialAllocation record
                    material_allocation = MaterialAllocation.objects.create(
                        production_plan=production_plan,
                        material_code=part_number, 
                        allocated_quantity=quantity_to_allocate,
                        status='ALLOCATED' 
                    )

                    # Create SalesOrder for this material allocation to put it on the shipment schedule
                    so_order_number = f"INT-{material_allocation.id.hex[:15]}"

                    sales_order, so_created = SalesOrder.objects.get_or_create(
                        order_number=so_order_number,
                        defaults={
                            'item': material_allocation.material_code, # This is part_number
                            'quantity': material_allocation.allocated_quantity,
                            'warehouse': warehouse, # Warehouse from the allocation request
                            'expected_shipment': production_plan.planned_start_datetime,
                            'status': 'pending'
                        }
                    )

                    if not so_created:
                        # This case should ideally not happen if so_order_number is truly unique
                        # based on material_allocation.id.hex.
                        # If it occurs, it might indicate an issue with the uniqueness strategy
                        # or a retry of a partially failed previous operation.
                        # For now, log a warning. If updates are needed, logic would go here.
                        print(f"Warning: SalesOrder with order_number {so_order_number} already existed. Item: {sales_order.item}, Qty: {sales_order.quantity}") # noqa: E501
                        # Potentially update if logic requires:
                        # sales_order.quantity = material_allocation.allocated_quantity
                        # sales_order.item = material_allocation.material_code # etc.
                        # sales_order.save()

                    processed_allocations_summary.append({
                        "part_number": part_number,
                        "warehouse": warehouse,
                        "allocated_quantity": quantity_to_allocate,
                        "material_allocation_id": material_allocation.id,
                        "new_inventory_reserved": inventory_item.reserved, # noqa: E501
                        "new_inventory_available": inventory_item.available_quantity, # noqa: E501
                        "sales_order_id": sales_order.id,
                        "sales_order_number": sales_order.order_number
                    })

                if errors:
                    raise ValueError("Errors occurred during allocation process. Transaction rolled back.")

            return Response({
                "message": "Materials allocated successfully for production plan.",
                "production_plan_id": production_plan.id,
                "allocations_summary": processed_allocations_summary
            }, status=status.HTTP_200_OK)

        except ValueError as e:
            return Response({"error": str(e), "details": errors}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": "An unexpected error occurred during material allocation.", "detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['post'], url_path='update-progress')
    def update_progress(self, request, pk=None):
        """
        Updates the progress of a specific production plan.
        This includes updating the plan's status, actual start/end times,
        and creating/updating a WorkProgress record.
        """
        plan = self.get_object()
        data = request.data

        new_status = data.get('status')
        if not new_status:
            return Response({"error": "New status is required."}, status=status.HTTP_400_BAD_REQUEST)

        now = timezone.now()
        
        # Use a consistent process_step for overall plan progress updates
        PROCESS_STEP_OVERALL = "Overall Plan Progress"

        work_progress, wp_created = WorkProgress.objects.get_or_create(
            production_plan=plan,
            process_step=PROCESS_STEP_OVERALL,
            defaults={
                'operator': request.user if request.user.is_authenticated else None,
                'status': 'NOT_STARTED' # Default status if created
            }
        )
        # Store the completed quantity from WorkProgress *before* it's potentially updated by new 'COMPLETED' status logic
        previous_wp_completed_quantity = work_progress.quantity_completed

        old_plan_status = plan.status
        plan.status = new_status

        # Logic for updating plan and work_progress based on new status
        if new_status == 'IN_PROGRESS':
            if old_plan_status == 'PENDING' or old_plan_status == 'ON_HOLD':
                if not plan.actual_start_datetime:
                    plan.actual_start_datetime = now
            
            work_progress.status = 'IN_PROGRESS'
            if not work_progress.start_datetime:
                work_progress.start_datetime = now
            work_progress.end_datetime = None # Ensure end_datetime is cleared if resuming

        elif new_status == 'COMPLETED':
            if not plan.actual_start_datetime: # If jumping from PENDING/ON_HOLD to COMPLETED
                plan.actual_start_datetime = now
            plan.actual_end_datetime = now

            work_progress.status = 'COMPLETED'
            if not work_progress.start_datetime: # Should ideally be set if it went through IN_PROGRESS
                work_progress.start_datetime = now
            work_progress.end_datetime = now
            
            # Validate and set quantities for WorkProgress
            good_quantity_str = data.get('good_quantity')
            if good_quantity_str is None:
                return Response({"error": "good_quantity is required when status is 'COMPLETED'."}, status=status.HTTP_400_BAD_REQUEST)
            try:
                val = int(good_quantity_str)
                if val < 0: raise ValueError("must be non-negative.")
                work_progress.quantity_completed = val
            except (ValueError, TypeError):
                return Response({"error": "Invalid value for good_quantity. Must be a non-negative integer."}, status=status.HTTP_400_BAD_REQUEST)

            actual_quantity_str = data.get('actual_quantity')
            if actual_quantity_str is not None:
                try:
                    val = int(actual_quantity_str)
                    if val < 0: raise ValueError("must be non-negative.")
                    work_progress.actual_reported_quantity = val
                except (ValueError, TypeError):
                    return Response({"error": "Invalid value for actual_quantity. Must be a non-negative integer."}, status=status.HTTP_400_BAD_REQUEST)
            else:
                # Field is nullable, so if not provided, can be set to None or retain existing if that's desired.
                # Explicitly setting to None if key is absent and value was not None previously.
                work_progress.actual_reported_quantity = None

            defective_quantity_str = data.get('defective_quantity')
            if defective_quantity_str is not None:
                try:
                    val = int(defective_quantity_str)
                    if val < 0: raise ValueError("must be non-negative.")
                    work_progress.defective_reported_quantity = val
                except (ValueError, TypeError):
                    return Response({"error": "Invalid value for defective_quantity. Must be a non-negative integer."}, status=status.HTTP_400_BAD_REQUEST)
            else:
                work_progress.defective_reported_quantity = None
        elif new_status == 'ON_HOLD':
            work_progress.status = 'PAUSED'
            # Optionally, set work_progress.end_datetime = now if you want to mark the exact pause time.
            # For simplicity, we'll let start_datetime persist and status indicate PAUSED.

        elif new_status == 'CANCELLED':
            if plan.actual_start_datetime and not plan.actual_end_datetime:
                plan.actual_end_datetime = now # Mark end time if it was in progress
            
            # For WorkProgress, if it was IN_PROGRESS, mark it as PAUSED or set end_datetime
            if work_progress.status == 'IN_PROGRESS' or work_progress.status == 'NOT_STARTED':
                work_progress.status = 'PAUSED' # Or another appropriate terminal status
                if work_progress.start_datetime and not work_progress.end_datetime:
                    work_progress.end_datetime = now
        
        elif new_status == 'PENDING': # e.g. reverting from ON_HOLD
            work_progress.status = 'NOT_STARTED'
            # Consider if actual_start/end datetimes on plan should be reset.
            # For now, we only update status.

        try:
            with transaction.atomic():
                # Handle inventory and WorkProgress quantity reversal if status changes FROM 'COMPLETED'
                if old_plan_status == 'COMPLETED' and new_status != 'COMPLETED':
                    if previous_wp_completed_quantity > 0: # Check if there was a completed quantity to reverse
                        product_code_to_reverse = plan.product_code
                        quantity_to_reverse = previous_wp_completed_quantity # This is the good quantity previously completed
                        warehouse_to_reverse_from = DEFAULT_FINISHED_GOODS_WAREHOUSE

                        try:
                            inventory_item_to_reverse = Inventory.objects.select_for_update().get(
                                part_number=product_code_to_reverse,
                                warehouse=warehouse_to_reverse_from
                            )

                            if inventory_item_to_reverse.quantity < quantity_to_reverse:
                                raise ValueError(
                                    f"Cannot reverse production for {product_code_to_reverse} in {warehouse_to_reverse_from}. "
                                    f"Required to deduct: {quantity_to_reverse}, Current stock: {inventory_item_to_reverse.quantity}."
                                )
                            
                            inventory_item_to_reverse.quantity -= quantity_to_reverse
                            inventory_item_to_reverse.save()

                            StockMovement.objects.create(
                                part_number=product_code_to_reverse,
                                quantity=quantity_to_reverse, 
                                warehouse=warehouse_to_reverse_from,
                                movement_type='PRODUCTION_REVERSAL', # New movement type
                                movement_date=now,
                                reference_document=f"Reversal for PPlan-{plan.id}",
                                description=f"Prod. completion reversed for plan {plan.id} (status: {old_plan_status} -> {new_status}).",
                                operator=request.user if request.user.is_authenticated else None
                            )
                            print(f"Inventory reversed for {product_code_to_reverse} in {warehouse_to_reverse_from}. Deducted: {quantity_to_reverse}. New QOH: {inventory_item_to_reverse.quantity}")

                            # Reset WorkProgress quantities as the completion is undone
                            work_progress.quantity_completed = 0
                            work_progress.actual_reported_quantity = None # Or 0, depending on desired behavior
                            work_progress.defective_reported_quantity = None # Or 0

                        except Inventory.DoesNotExist:
                            raise ValueError(
                                f"Inventory for product {product_code_to_reverse} in warehouse {warehouse_to_reverse_from} not found for reversal."
                            )
                
                plan.save()
                work_progress.save() # Save work_progress after potential quantity resets or updates

                # If the plan is completed, adjust inventory based on the change in completed quantity
                if new_status == 'COMPLETED':
                    product_code = plan.product_code
                    newly_reported_completed_quantity = work_progress.quantity_completed # New total from request, saved in work_progress

                    quantity_to_adjust_inventory_by = 0
                    if old_plan_status != 'COMPLETED':
                        # Transitioning from non-completed to completed.
                        quantity_to_adjust_inventory_by = newly_reported_completed_quantity
                    else: # old_plan_status == 'COMPLETED'
                        # Already completed, now updating the completed quantity. Adjust by the difference.
                        quantity_to_adjust_inventory_by = newly_reported_completed_quantity - previous_wp_completed_quantity
                    
                    if quantity_to_adjust_inventory_by != 0:
                        target_warehouse = DEFAULT_FINISHED_GOODS_WAREHOUSE
                        
                        # Get or create inventory item, ensuring row lock for update
                        try:
                            inventory_item = Inventory.objects.select_for_update().get(
                                part_number=product_code,
                                warehouse=target_warehouse
                            )
                        except Inventory.DoesNotExist:
                            # If it doesn't exist, create it.
                            inventory_item = Inventory.objects.create(
                                part_number=product_code,
                                warehouse=target_warehouse,
                                quantity=0, # Initial quantity before adjustment
                                reserved=0,
                                is_active=True,
                                is_allocatable=True
                            )
                        
                        # Check for sufficient stock if reducing
                        if quantity_to_adjust_inventory_by < 0:
                            if inventory_item.quantity < abs(quantity_to_adjust_inventory_by):
                                raise ValueError(
                                    f"Cannot reduce completed quantity for {product_code} in {target_warehouse}. "
                                    f"Attempting to deduct: {abs(quantity_to_adjust_inventory_by)}, Current stock: {inventory_item.quantity}."
                                )
                        
                        inventory_item.quantity += quantity_to_adjust_inventory_by
                        inventory_item.save()

                        # Create a stock movement record
                        movement_quantity_log = abs(quantity_to_adjust_inventory_by)
                        movement_type_log = 'PRODUCTION_OUTPUT' if quantity_to_adjust_inventory_by > 0 else 'PRODUCTION_REVERSAL'
                        
                        StockMovement.objects.create(
                            part_number=product_code,
                            quantity=movement_quantity_log,
                            warehouse=target_warehouse,
                            movement_type=movement_type_log,
                            movement_date=now,
                            reference_document=f"ProductionPlan-{plan.id}",
                            description=f"Plan {plan.id} completion. Qty changed by: {quantity_to_adjust_inventory_by}. New total completed: {newly_reported_completed_quantity}.",
                            operator=request.user if request.user.is_authenticated else None
                        )
                        print(f"Inventory for {product_code} in {target_warehouse} changed by: {quantity_to_adjust_inventory_by}. New QOH: {inventory_item.quantity}")
                    else:
                        print(f"No inventory change for {product_code} as calculated adjustment is zero for plan {plan.id}.")

        except ValueError as ve:
            # Catch specific ValueErrors from our logic (e.g., insufficient stock for reversal)
            return Response({"error": f"Failed to save progress: {str(ve)}"}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            # Log the detailed error for debugging
            import traceback
            print(f"Error during progress update transaction: {str(e)}")
            print(traceback.format_exc())
            return Response({"error": f"Failed to save progress due to an unexpected error. Please check logs."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response({
            "message": "Production plan progress updated successfully.",
            "plan_id": plan.id,
            "new_status": plan.get_status_display()
        }, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'], url_path='update-process-status')
    def update_process_status(self, request):
        """
        作業者インターフェースから工程の開始・完了状態を更新するためのAPIエンドポイント
        """
        data = request.data
        plan_id = data.get('plan_id')
        process_type = data.get('process_type')
        action = data.get('action')  # 'start' または 'complete'
        worker_id = data.get('worker_id')
        timestamp = data.get('timestamp')
        
        # 必須パラメータの検証
        if not all([plan_id, process_type, action, worker_id]):
            return Response({
                'success': False,
                'error': '必須パラメータが不足しています (plan_id, process_type, action, worker_id)'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # アクションの検証
        if action not in ['start', 'complete']:
            return Response({
                'success': False,
                'error': 'actionは"start"または"complete"である必要があります'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # 生産計画の取得
            production_plan = get_object_or_404(ProductionPlan, id=plan_id)
            
            # 工程フィールドのマッピング
            process_field_mapping = {
                'slit': {
                    'status': 'slit_status',
                    'start_time': 'slit_start_time',
                    'completion_time': 'slit_completion_time',
                    'duration': 'slit_duration_minutes',
                    'worker_id': 'slit_worker_id'
                },
                'cut': {
                    'status': 'cut_status',
                    'start_time': 'cut_start_time',
                    'completion_time': 'cut_completion_time',
                    'duration': 'cut_duration_minutes',
                    'worker_id': 'cut_worker_id'
                },
                'base_material_cut': {
                    'status': 'base_material_cut_status',
                    'start_time': 'base_material_cut_start_time',
                    'completion_time': 'base_material_cut_completion_time',
                    'duration': 'base_material_cut_duration_minutes',
                    'worker_id': 'base_material_cut_worker_id'
                },
                'molder': {
                    'status': 'molder_status',
                    'start_time': 'molder_start_time',
                    'completion_time': 'molder_completion_time',
                    'duration': 'molder_duration_minutes',
                    'worker_id': 'molder_worker_id'
                },
                'v_cut_lapping': {
                    'status': 'v_cut_lapping_status',
                    'start_time': 'v_cut_lapping_start_time',
                    'completion_time': 'v_cut_lapping_completion_time',
                    'duration': 'v_cut_lapping_duration_minutes',
                    'worker_id': 'v_cut_lapping_worker_id'
                },
                'post_processing': {
                    'status': 'post_processing_status',
                    'start_time': 'post_processing_start_time',
                    'completion_time': 'post_processing_completion_time',
                    'duration': 'post_processing_duration_minutes',
                    'worker_id': 'post_processing_worker_id'
                },
                'packing': {
                    'status': 'packing_status',
                    'start_time': 'packing_start_time',
                    'completion_time': 'packing_completion_time',
                    'duration': 'packing_duration_minutes',
                    'worker_id': 'packing_worker_id'
                },
                'decorative_board': {
                    'status': 'decorative_board_status',
                    'start_time': 'decorative_board_start_time',
                    'completion_time': 'decorative_board_completion_time',
                    'duration': 'decorative_board_duration_minutes',
                    'worker_id': 'decorative_board_worker_id'
                },
                'decorative_board_cut': {
                    'status': 'decorative_board_cut_status',
                    'start_time': 'decorative_board_cut_start_time',
                    'completion_time': 'decorative_board_cut_completion_time',
                    'duration': 'decorative_board_cut_duration_minutes',
                    'worker_id': 'decorative_board_cut_worker_id'
                }
            }
            
            if process_type not in process_field_mapping:
                return Response({
                    'success': False,
                    'error': f'無効な工程タイプ: {process_type}'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            fields = process_field_mapping[process_type]
            current_status = getattr(production_plan, fields['status'])
            
            # 時刻文字列をdatetimeオブジェクトに変換
            if timestamp:
                try:
                    parsed_timestamp = parse_datetime(timestamp)
                    if not parsed_timestamp:
                        parsed_timestamp = timezone.now()
                except:
                    parsed_timestamp = timezone.now()
            else:
                parsed_timestamp = timezone.now()
            
            with transaction.atomic():
                if action == 'start':
                    # 工程開始処理
                    if current_status != '未着手':
                        return Response({
                            'success': False,
                            'error': f'この工程は既に{current_status}状態です。開始できません。'
                        }, status=status.HTTP_400_BAD_REQUEST)
                    
                    # ステータス、開始時刻、作業者IDを更新
                    setattr(production_plan, fields['status'], '着手中')
                    setattr(production_plan, fields['start_time'], parsed_timestamp)
                    setattr(production_plan, fields['worker_id'], worker_id)
                    
                    message = f'工程 {process_type} を開始しました'
                    
                elif action == 'complete':
                    # 工程完了処理
                    if current_status != '着手中':
                        return Response({
                            'success': False,
                            'error': f'この工程は{current_status}状態です。完了できません。'
                        }, status=status.HTTP_400_BAD_REQUEST)
                    
                    # 開始時刻を取得
                    start_time = getattr(production_plan, fields['start_time'])
                    
                    # ステータスと完了時刻を更新
                    setattr(production_plan, fields['status'], '完了')
                    setattr(production_plan, fields['completion_time'], parsed_timestamp)
                    
                    # 所要時間を計算（開始時刻がある場合）
                    if start_time:
                        duration_seconds = (parsed_timestamp - start_time).total_seconds()
                        duration_minutes = duration_seconds / 60
                        
                        # 負の値を防ぐため、最小値を0に設定
                        if duration_minutes < 0:
                            print(f"警告: 工程 {process_type} の所要時間が負の値になりました。開始時刻: {start_time}, 完了時刻: {parsed_timestamp}")
                            duration_minutes = 0
                        
                        setattr(production_plan, fields['duration'], int(duration_minutes))
                    
                    message = f'工程 {process_type} を完了しました'
                
                # 生産計画を保存
                production_plan.save()
                
                # 作業履歴の記録（WorkProgressモデルがある場合）
                if hasattr(production_plan, 'workprogress_set'):
                    WorkProgress.objects.create(
                        production_plan=production_plan,
                        process_step=process_type,
                        operator_id=worker_id,
                        status='IN_PROGRESS' if action == 'start' else 'COMPLETED',
                        start_datetime=parsed_timestamp if action == 'start' else None,
                        end_datetime=parsed_timestamp if action == 'complete' else None,
                        quantity_completed=production_plan.planned_quantity if action == 'complete' else 0
                    )
                
                return Response({
                    'success': True,
                    'message': message,
                    'plan_id': plan_id,
                    'process_type': process_type,
                    'action': action,
                    'worker_id': worker_id,
                    'timestamp': parsed_timestamp.isoformat(),
                    'new_status': getattr(production_plan, fields['status'])
                }, status=status.HTTP_200_OK)
                
        except ProductionPlan.DoesNotExist:
            return Response({
                'success': False,
                'error': f'生産計画ID {plan_id} が見つかりません'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            import traceback
            print(f"工程状態更新エラー: {str(e)}")
            print(traceback.format_exc())
            return Response({
                'success': False,
                'error': f'工程状態の更新中にエラーが発生しました: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class PartsUsedViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows PartsUsed records to be viewed or created.
    """
    queryset = PartsUsed.objects.all().order_by('-used_datetime')
    serializer_class = PartsUsedSerializer
    pagination_class = StandardResultsSetPagination # ページネーションクラスを指定
    # permission_classes = [permissions.IsAuthenticated] # Example: Add authentication