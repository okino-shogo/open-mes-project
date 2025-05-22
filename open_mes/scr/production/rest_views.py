from rest_framework import viewsets
# from rest_framework import permissions # Uncomment if you want to add permissions
from rest_framework.decorators import action # actionデコレータをインポート
from rest_framework.response import Response # Responseをインポート
from .models import ProductionPlan, PartsUsed
from .serializers import ProductionPlanSerializer, PartsUsedSerializer, RequiredPartSerializer
from inventory.rest_views import StandardResultsSetPagination # inventoryアプリのページネーションクラスをインポート
from django.db.models import Q # Qオブジェクトをインポート
from inventory.models import Inventory # Inventoryモデルをインポート
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

class PartsUsedViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows PartsUsed records to be viewed or created.
    """
    queryset = PartsUsed.objects.all().order_by('-used_datetime')
    serializer_class = PartsUsedSerializer
    pagination_class = StandardResultsSetPagination # ページネーションクラスを指定
    # permission_classes = [permissions.IsAuthenticated] # Example: Add authentication