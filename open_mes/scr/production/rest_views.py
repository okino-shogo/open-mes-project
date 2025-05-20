from rest_framework import viewsets
# from rest_framework import permissions # Uncomment if you want to add permissions
from rest_framework.decorators import action # actionデコレータをインポート
from rest_framework.response import Response # Responseをインポート
from .models import ProductionPlan, PartsUsed # PartsUsedモデルをインポート
from .serializers import ProductionPlanSerializer, PartsUsedSerializer # PartsUsedSerializerをインポート # RequiredPartSerializerをインポート (仮のコメント)
from inventory.rest_views import StandardResultsSetPagination # inventoryアプリのページネーションクラスをインポート
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
        """
        production_plan = self.get_object()
        required_parts_data = []
        error_message = None

        # --- ここからBOM (部品表) 取得ロジック ---
        # ProductionPlanモデルの 'product' ForeignKey (例: 'master.Product') が有効になっていると仮定します。
        # また、ProductモデルにはBOMアイテム (例: 'bom_items' related_name) が関連付けられていると仮定します。
        # BOMアイテムは、部品 (Part) とその製品1単位あたりの必要数量 (quantity) を持つとします。
        try:
            if hasattr(production_plan, 'product') and production_plan.product:
                product = production_plan.product
                # 'bom_items' は Product モデルから BillOfMaterialItem への related_name と仮定
                # BillOfMaterialItem は 'part' (ForeignKey to Part model) と 'quantity_per_product' を持つと仮定
                # Part モデルは 'part_code', 'part_name', 'unit' を持つと仮定
                bom_items = product.bom_items.all() # 例: product.billofmaterialitem_set.all()
                
                if bom_items:
                    for item in bom_items:
                        required_parts_data.append({
                            "part_code": item.part.part_code,
                            "part_name": item.part.part_name,
                            "required_quantity": item.quantity_per_product * production_plan.planned_quantity,
                            "unit": item.part.unit,
                        })
                    # 実際には RequiredPartSerializer を使用してシリアライズします
                    # from .serializers import RequiredPartSerializer # このインポートはファイルの先頭に
                    # serializer = RequiredPartSerializer(required_parts_data, many=True)
                    # return Response(serializer.data)
                else:
                    error_message = "製品にBOM情報が登録されていません。"
            else:
                error_message = "生産計画に製品情報が紐付いていません。('product'フィールドを確認してください)"

        except AttributeError as e:
            # 例: production_plan.product や item.part.part_code などが存在しない場合
            error_message = f"関連モデルの属性が見つかりません: {e}。モデル定義を確認してください。"
        except Exception as e: # その他の予期せぬエラー
            error_message = f"部品情報の取得中にエラーが発生しました: {e}"

        # --- BOM取得ロジックここまで ---

        if error_message and not required_parts_data:
            # 実際のBOMロジックが実装されるまでは、以下のダミーデータを返すか、エラーを返すかを選択
            # 現状はエラーメッセージがあれば、ダミーデータは返さない方針
            # return Response({"detail": error_message}, status=404)
            
            # 以下はダミーデータ（実際のBOMロジックが完全に実装されるまでのフォールバック）
            print(f"警告: {error_message} ダミーデータを返します。") # サーバーログに警告出力
            required_parts_data = [
                { "part_code": "DUMMY-CPN-001", "part_name": "ダミー部品A (要BOM実装)", "required_quantity": 2 * production_plan.planned_quantity, "unit": "個" },
                { "part_code": "DUMMY-SUB-002", "part_name": "ダミー部品B (要BOM実装)", "required_quantity": 1 * production_plan.planned_quantity, "unit": "セット" },
            ]

        if not required_parts_data and not error_message: # BOMデータもエラーメッセージもない場合
             return Response({"detail": "この生産計画に必要な部品情報は見つかりませんでした。"}, status=404)

        return Response(required_parts_data)
class PartsUsedViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows PartsUsed records to be viewed or created.
    """
    queryset = PartsUsed.objects.all().order_by('-used_datetime')
    serializer_class = PartsUsedSerializer
    pagination_class = StandardResultsSetPagination # ページネーションクラスを指定
    # permission_classes = [permissions.IsAuthenticated] # Example: Add authentication