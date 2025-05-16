from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated # 必要に応じて認証を追加
from rest_framework.response import Response
from .serializers import PurchaseOrderSerializer, InventorySerializer # InventorySerializer をインポート
from .models import PurchaseOrder, Inventory, StockMovement # PurchaseOrder, Inventory, StockMovementモデルをインポート
from django.http import JsonResponse
from django.db import transaction # トランザクションのためにインポート
from django.shortcuts import get_object_or_404 # オブジェクト取得のためにインポート
from master.models import Item, Warehouse # masterアプリケーションからItem, Warehouseをインポート
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


@api_view(['POST'])
# @permission_classes([IsAuthenticated]) # 認証が必要な場合はこの行のコメントを解除してください
def process_purchase_receipt_api(request):
    """
    入庫処理を実行するAPIエンドポイント。

    指定された入庫予定に対して、実際の入庫数量を記録し、在庫を更新します。

    リクエストボディには以下のフィールドが必要です:
    - 'purchase_order_id' (UUID文字列) または 'order_number' (文字列): 入庫処理を行う入庫予定のIDまたは発注番号。どちらか一方は必須です。'purchase_order_id' が優先されます。
    - 'received_quantity' (整数): 今回入庫する数量
    - 'location' (文字列, オプション): 実際に入庫した倉庫内の場所
    """
    purchase_order_id = request.data.get('purchase_order_id')
    order_number = request.data.get('order_number')
    received_quantity = request.data.get('received_quantity')
    location = request.data.get('location') # オプションの場所情報

    if (not purchase_order_id and not order_number) or received_quantity is None:
        return Response(
            {"error": "purchase_order_id または order_number のいずれかと、received_quantity は必須です。"},
            status=status.HTTP_400_BAD_REQUEST
        )


    try:
        # received_quantity が正の整数であることを検証
        received_quantity = int(received_quantity)
        if received_quantity <= 0:
            return Response(
                {"error": "received_quantity は正の整数である必要があります。"},
                status=status.HTTP_400_BAD_REQUEST
            )
    except (ValueError, TypeError):
        return Response(
            {"error": "received_quantity は有効な整数である必要があります。"},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        # データベース操作の原子性を保証するためにトランザクションを使用
        with transaction.atomic():
            # 1. 入庫予定オブジェクトを取得 (purchase_order_id があれば優先、なければ order_number で検索)
            if purchase_order_id:
                purchase_order = get_object_or_404(PurchaseOrder, id=purchase_order_id)
            elif order_number:
                purchase_order = get_object_or_404(PurchaseOrder, order_number=order_number)
            else: # このケースは上記の必須チェックでカバーされるはずだが念のため
                return Response({"error": "内部エラー: IDまたは発注番号が特定できませんでした。"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            # POが既に完了またはキャンセルされていないかチェック
            if purchase_order.status == 'received':
                 return Response(
                    {"error": f"入庫予定 {purchase_order.order_number} は既に入庫完了しています。"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            if purchase_order.status == 'canceled':
                 return Response(
                    {"error": f"入庫予定 {purchase_order.order_number} はキャンセルされています。"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # 残りの入庫予定数量を計算
            remaining_to_receive = purchase_order.quantity - purchase_order.received_quantity

            # 今回の入庫数量が残り数量を超える場合の処理 (ビジネスロジックによる)
            # 超過分を許可しない場合はエラーを返す
            if received_quantity > remaining_to_receive:
                 # エラーを返す場合:
                 # return Response(
                 #    {"error": f"入庫数量 ({received_quantity}) が入庫予定の残り数量 ({remaining_to_receive}) を超えています。"},
                 #    status=status.HTTP_400_BAD_REQUEST
                 # )
                 # 残り数量のみを処理する場合:
                 print(f"警告: 入庫数量 ({received_quantity}) が入庫予定の残り数量 ({remaining_to_receive}) を超えています。残り数量 ({remaining_to_receive}) のみ処理します。")
                 actual_received_quantity = remaining_to_receive
                 if actual_received_quantity <= 0: # 残り数量が0以下の場合は処理しない
                      return Response(
                         {"error": f"入庫予定 {purchase_order.order_number} には入庫する残り数量がありません。"},
                         status=status.HTTP_400_BAD_REQUEST
                     )
            else:
                actual_received_quantity = received_quantity

            # 2. POの received_quantity を更新
            purchase_order.received_quantity += actual_received_quantity

            # 3. (変更) StockMovement には PurchaseOrder の item 文字列を直接使用するため、
            #    Item オブジェクトの検索は不要になりました。
            # Warehouse オブジェクトの検索は、Inventory が文字列を格納するようになり、
            # StockMovement が倉庫情報を持たないため、不要になりました。

            # 4. 対応する Inventory レコードを検索または新規作成し、数量を更新
            #    Inventory の item と warehouse は PurchaseOrder からの文字列を直接使用
            inventory_item, created = Inventory.objects.get_or_create(
                part_number=purchase_order.item,    # PurchaseOrder の item 文字列を part_number として使用
                warehouse=purchase_order.warehouse, # PurchaseOrder の warehouse 文字列
                defaults={'location': location}     # location は request.data.get('location')
            )
            inventory_item.quantity += actual_received_quantity
 
            # 既存レコードの場合で、かつリクエストに location が指定されていれば更新
            if not created and location is not None:
                inventory_item.location = location
            inventory_item.save()

            # 5. StockMovement レコードを作成 (入庫履歴)
            StockMovement.objects.create(
                part_number=purchase_order.item, # PurchaseOrder の item 文字列を直接使用
                movement_type='incoming',
                quantity=actual_received_quantity,
                description=f"PO {purchase_order.order_number} による入庫" + (f" (場所: {location})" if location else ""),
            )

            # 6. 入庫完了した場合、POのステータスを更新
            if purchase_order.received_quantity >= purchase_order.quantity:
                purchase_order.status = 'received'

            purchase_order.save()

            # 7. 更新されたPOデータをレスポンスとして返却
            serializer = PurchaseOrderSerializer(purchase_order)
            return Response(serializer.data, status=status.HTTP_200_OK)

    except PurchaseOrder.DoesNotExist:
        return Response(
            {"error": f"指定された入庫予定 (ID: {purchase_order_id}, 発注番号: {order_number}) が見つかりませんでした。"},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        # その他の予期しないエラーをキャッチ
        print(f"入庫処理中にエラーが発生しました: {e}")
        return Response(
            {"error": "入庫処理中に内部エラーが発生しました。"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

# @login_required # ログインユーザーのみアクセス可能にする場合 (必要に応じてコメント解除)
def get_inventory_data(request):
    """
    在庫情報を取得し、JSON形式で返却するビュー
    """
    if request.method == 'GET':
        inventories = Inventory.objects.all().order_by('part_number', 'warehouse', 'location')
        serializer = InventorySerializer(inventories, many=True)
        return JsonResponse(serializer.data, safe=False)
    else:
        return JsonResponse({'error': 'Invalid request method'}, status=405)