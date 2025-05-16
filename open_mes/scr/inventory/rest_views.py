from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated # 必要に応じて認証を追加
from rest_framework.response import Response
from .serializers import PurchaseOrderSerializer

@permission_classes([IsAuthenticated]) # 認証が必要な場合はこの行のコメントを解除してください
@api_view(['POST'])
def create_purchase_order_api(request):
    """
    新しい入庫予定を作成するAPIエンドポイント。

    リクエストボディには以下のフィールドが必要です:
    - 'order_number' (文字列): 発注番号
    - 'supplier' (整数): 仕入先のID
    - 'item' (整数): 品目のID
    - 'quantity' (整数): 発注数量
    - 'warehouse' (整数): 入庫倉庫のID
    オプションフィールド:
    - 'expected_arrival' (日時文字列): 入荷予定日 (例: "YYYY-MM-DDTHH:MM:SSZ")
    """
    serializer = PurchaseOrderSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)