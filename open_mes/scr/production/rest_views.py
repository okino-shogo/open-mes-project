from rest_framework import viewsets
# from rest_framework import permissions # Uncomment if you want to add permissions
from rest_framework import status # HTTPステータスコードをインポート
from rest_framework.decorators import action # actionデコレータをインポート
from rest_framework.response import Response # Responseをインポート
from .models import ProductionPlan, PartsUsed, MaterialAllocation # Add MaterialAllocation
from .serializers import ProductionPlanSerializer, PartsUsedSerializer, RequiredPartSerializer
from inventory.rest_views import StandardResultsSetPagination # inventoryアプリのページネーションクラスをインポート # noqa: E501
from django.db.models import Q # Qオブジェクトをインポート
from inventory.models import Inventory, StockMovement, SalesOrder # Add StockMovement and SalesOrder
from django.db import transaction # トランザクションのためにインポート
from django.shortcuts import get_object_or_404 # オブジェクト取得のためにインポート
# from .models import Product, BillOfMaterialItem # BOMに関連するモデル (仮のインポート、実際には適切なモデルを定義・インポートしてください)
# from .serializers import RequiredPartSerializer # BOM部品用のシリアライザ (仮のインポート)

class ProductionPlanViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows Production Plans to be viewed or created.
    """
    queryset = ProductionPlan.objects.all().order_by('-planned_start_datetime')
    serializer_class = ProductionPlanSerializer
    pagination_class = StandardResultsSetPagination # ページネーションクラスを指定
    # permission_classes = [permissions.IsAuthenticated] # Example: Add authentication

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

            data_for_serializer.append({
                "part_code": part_code,
                "part_name": f"{part_code} (名称は別途マスタ参照)", # Placeholder for part_name
                "required_quantity": part_used_item.quantity_used, # Using quantity_used from PartsUsed
                "unit": "個",  # Placeholder for unit, e.g., '個' (pieces)
                "inventory_quantity": current_inventory_quantity,
                "warehouse": part_specific_warehouse
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

class PartsUsedViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows PartsUsed records to be viewed or created.
    """
    queryset = PartsUsed.objects.all().order_by('-used_datetime')
    serializer_class = PartsUsedSerializer
    pagination_class = StandardResultsSetPagination # ページネーションクラスを指定
    # permission_classes = [permissions.IsAuthenticated] # Example: Add authentication