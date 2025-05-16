from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated # 必要に応じて認証を追加
from rest_framework.response import Response
from .serializers import PurchaseOrderSerializer
from .models import PurchaseOrder # PurchaseOrderモデルをインポート
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required # 認証が必要な場合

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

# @login_required # ログインユーザーのみアクセス可能にする場合 (必要に応じてコメント解除)
def get_schedule_data(request):
    """
    入庫予定データを取得し、JSON形式で返却するビュー
    """
    if request.method == 'GET':
        # 未完了の入庫予定を取得 (ステータスが 'pending' のもの)
        # 必要に応じて 'partially_received' など他のステータスも考慮に入れることができます。
        # PurchaseOrder モデルの status choices: ('pending', 'Pending'), ('received', 'Received'), ('canceled', 'Canceled')
        schedule_items = PurchaseOrder.objects.filter(
            status='pending'  # 'pending' 状態のものを取得
        ).order_by('expected_arrival', 'order_number')

        data = []
        for item in schedule_items:
            data.append({
                'order_number': item.order_number,
                'supplier': item.supplier,
                # 'item' フィールドには product_name を優先し、なければ item を使用
                'item': item.product_name if item.product_name else item.item,
                'quantity': item.quantity if item.quantity is not None else 0,
                'received_quantity': item.received_quantity if item.received_quantity is not None else 0,
                'order_date': item.order_date.strftime('%Y-%m-%d %H:%M:%S') if item.order_date else '', # 日時まで表示
                'expected_arrival': item.expected_arrival.strftime('%Y-%m-%d %H:%M:%S') if item.expected_arrival else '', # 日時まで表示
                'warehouse': item.warehouse,
                'status': item.get_status_display(), # 選択肢の表示名を取得
            })
        return JsonResponse(data, safe=False)
    else:
        return JsonResponse({'error': 'Invalid request method'}, status=405)