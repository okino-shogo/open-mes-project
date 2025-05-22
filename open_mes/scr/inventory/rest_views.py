from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated # 必要に応じて認証を追加
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from .serializers import PurchaseOrderSerializer, InventorySerializer, AllocateInventoryForSalesOrderRequestSerializer
from .models import PurchaseOrder, Inventory, StockMovement # PurchaseOrder, Inventory, StockMovementモデルをインポート
from django.http import JsonResponse
from django.db import transaction # トランザクションのためにインポート
from django.db.models import Q # Qオブジェクトをインポートして複雑なクエリを構築
from django.shortcuts import get_object_or_404 # オブジェクト取得のためにインポート
from master.models import Item, Warehouse # masterアプリケーションからItem, Warehouseをインポート (現在は文字列として使用)
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
# @api_view(['GET']) # JsonResponse を使う場合は不要
def get_schedule_data(request):
    """
    入庫予定データを取得し、JSON形式で返却するビュー (ページネーション対応)
    """
    if request.method == 'GET':
        from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

        # ページネーション設定
        # クライアントはクエリパラメータ 'page' と 'page_size' で制御できます
        page = request.GET.get('page', 1)
        page_size = request.GET.get('page_size', 25) # デフォルト件数

        try:
            page_size = int(page_size)
            # ページサイズの最小・最大を制限 (例: 1件以上、1000件以下)
            if page_size <= 0 or page_size > 1000:
                page_size = 25 # 無効な場合はデフォルトに戻す
        except (ValueError, TypeError):
            page_size = 25 # 無効な場合はデフォルトに戻す




        # 未完了の入庫予定を取得 (ステータスが 'pending' のもの)
        # 必要に応じて 'partially_received' など他のステータスも考慮に入れることができます。
        # PurchaseOrder モデルの status choices: ('pending', 'Pending'), ('received', 'Received'), ('canceled', 'Canceled')
        schedule_items_query = PurchaseOrder.objects.filter(
            status='pending'  # 'pending' 状態のものを取得
        )

        # 検索パラメータを取得してフィルタリング
        search_term = request.GET.get('search', None)
        if search_term:
            query_filter = (
                Q(order_number__icontains=search_term) |
                Q(supplier__icontains=search_term) |
                Q(item__icontains=search_term) |  # 品目コード/旧名称など
                Q(product_name__icontains=search_term) | # 品名
                Q(part_number__icontains=search_term) | # 品番 (追加)
                Q(shipment_number__icontains=search_term) # 便番号も検索対象に含める例
            )
            schedule_items_query = schedule_items_query.filter(query_filter)

        schedule_items = schedule_items_query.order_by('expected_arrival', 'order_number')

        # Paginator オブジェクトを作成
        paginator = Paginator(schedule_items, page_size)

        try:
            schedule_items_page = paginator.page(page)
        except PageNotAnInteger:
            schedule_items_page = paginator.page(1) # ページ番号が整数でない場合は1ページ目
        except EmptyPage:
            schedule_items_page = paginator.page(paginator.num_pages) # ページが空の場合は最終ページ

        data = []
        for item in schedule_items_page: # ページングされたオブジェクトをループ
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
                'part_number': item.part_number if item.part_number else '',
                'shipment_number': item.shipment_number if item.shipment_number else '',
                # The 'barcode' and 'serial_number' fields are handled in JS if item.barcode/item.serial_number exist.
                # They are not standard fields on the PurchaseOrder model itself.
                # If they need to be populated from the backend, ensure they are added to the PurchaseOrder model
                # or derived from related models and included here.
            })

        # ページネーション情報をレスポンスに含める
        response_data = {
            'count': paginator.count, # 総件数
            'num_pages': paginator.num_pages, # 総ページ数
            'current_page': schedule_items_page.number, # 現在のページ番号
            'next': schedule_items_page.next_page_number() if schedule_items_page.has_next() else None, # 次のページ番号 (なければ None)
            'previous': schedule_items_page.previous_page_number() if schedule_items_page.has_previous() else None, # 前のページ番号 (なければ None)
            'results': data # ページングされたデータ
        }
        return JsonResponse(response_data, safe=False)
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
                part_number=purchase_order.part_number, # PurchaseOrder の part_number を使用
                warehouse=purchase_order.warehouse, # PurchaseOrder の warehouse 文字列
                defaults={'quantity': 0, 'location': location} # 新規作成時のデフォルト値を設定 (quantity:0 はモデル定義にもあるが明示)
            ) # location はリクエストから取得
            inventory_item.quantity += actual_received_quantity
 
            # 既存レコードの場合で、かつリクエストに location が指定されていれば更新
            if not created and location is not None:
                inventory_item.location = location
            inventory_item.save()

            # 5. StockMovement レコードを作成 (入庫履歴)
            StockMovement.objects.create(
                part_number=purchase_order.part_number, # PurchaseOrder の part_number を使用
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


# DRFのページネーションクラスを定義 (共通で利用可能)
class StandardResultsSetPagination(PageNumberPagination):
    page_size = 100  # 1ページあたりのデフォルト件数
    page_size_query_param = 'page_size' # クライアントが1ページあたりの件数を指定するためのクエリパラメータ
    max_page_size = 1000 # クライアントが指定できる1ページあたりの最大件数


# @login_required # ログインユーザーのみアクセス可能にする場合 (必要に応じてコメント解除)
# @permission_classes([IsAuthenticated]) # 必要に応じて認証を追加
@api_view(['GET']) # DRFの Response を使うため @api_view デコレータを使用
def get_inventory_data(request):
    """
    在庫情報を取得し、JSON形式で返却するビュー (DRFページネーション対応)
    """
    if request.method == 'GET':
        # DRFページネーションを適用
        # クライアントはクエリパラメータ 'page' と 'page_size' で制御できます
        paginator = StandardResultsSetPagination()

        # クエリセットを取得し、ページネーションを適用
        inventories = Inventory.objects.all().order_by('part_number', 'warehouse', 'location')
        paginated_inventories = paginator.paginate_queryset(inventories, request)

        # ページングされたクエリセットをシリアライズ
        serializer = InventorySerializer(paginated_inventories, many=True)
        # DRF標準のページネーション形式でレスポンスを構築して返却
        return paginator.get_paginated_response(serializer.data)
    else:
        # DRFの Response を使う場合、エラーレスポンスも Response で統一するのが良い
        return Response({'error': 'Invalid request method'}, status=status.HTTP_405_METHOD_NOT_ALLOWED)


@api_view(['POST'])
# @permission_classes([IsAuthenticated]) # Uncomment if authentication is required
def allocate_inventory_for_sales_order_api(request):
    """
    Allocates inventory for a sales order.
    This endpoint reserves quantities for specified part numbers in given warehouses.
    The operation is atomic: all allocations succeed, or none are applied.

    Request Body:
    {
      "sales_order_reference": "SO12345",
      "allocations": [
        {"part_number": "PN001", "warehouse": "WH-A", "quantity_to_reserve": 10},
        {"part_number": "PN002", "warehouse": "WH-B", "quantity_to_reserve": 5}
      ]
    }
    """
    serializer = AllocateInventoryForSalesOrderRequestSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    validated_data = serializer.validated_data
    sales_order_ref = validated_data['sales_order_reference'] # Renamed for clarity and consistency
    allocations_data = validated_data['allocations'] # This will be a list of allocation items

    from .models import SalesOrder, Inventory # Import SalesOrder and Inventory models

    processed_allocations_summary = []

    try:
        with transaction.atomic():
            # Iterate over the list of allocations provided in the request
            for alloc_item_data in allocations_data:
                part_number = alloc_item_data['part_number']
                warehouse = alloc_item_data['warehouse']
                quantity_to_reserve = alloc_item_data['quantity_to_reserve']

                try:
                    # Lock the inventory row for the duration of the transaction
                    inventory_item = Inventory.objects.select_for_update().get(
                        part_number=part_number,
                        warehouse=warehouse
                    )
                except Inventory.DoesNotExist:
                    raise ValueError(f"Inventory record not found for part '{part_number}' in warehouse '{warehouse}'.")

                if not inventory_item.is_active or not inventory_item.is_allocatable:
                    raise ValueError(f"Inventory for part '{part_number}' in warehouse '{warehouse}' is not active or not allocatable.")

                if inventory_item.available_quantity < quantity_to_reserve:
                    raise ValueError(
                        f"Insufficient available stock for part '{part_number}' in warehouse '{warehouse}'. "
                        f"Required: {quantity_to_reserve}, Available: {inventory_item.available_quantity}"
                    )

                inventory_item.reserved += quantity_to_reserve
                inventory_item.save()

                # Create SalesOrder if it doesn't exist for this sales_order_ref,
                # or verify consistency if it does.
                # The sales_order_ref is assumed to uniquely identify the sales order line.
                sales_order, so_created = SalesOrder.objects.get_or_create(
                    order_number=sales_order_ref,
                    defaults={
                        'item': part_number,
                        'quantity': quantity_to_reserve, # SalesOrder.quantity set by the first reservation's amount
                        'warehouse': warehouse,
                        'status': 'pending'
                    }
                )

                if not so_created:
                    # SalesOrder already existed. Verify consistency with the current allocation.
                    mismatch = False
                    if sales_order.item != part_number:
                        mismatch = True
                    # Compare warehouse, handling None carefully
                    if warehouse is None and sales_order.warehouse is not None:
                        mismatch = True
                    elif warehouse is not None and sales_order.warehouse != warehouse:
                        mismatch = True
                    
                    if mismatch:
                        raise ValueError(
                            f"Sales Order '{sales_order_ref}' (ID: {sales_order.id}) already exists but with conflicting item/warehouse. "
                            f"Existing: item='{sales_order.item}', warehouse='{sales_order.warehouse}'. "
                            f"Current allocation request: item='{part_number}', warehouse='{warehouse}'."
                        )

                processed_allocations_summary.append({
                    "part_number": part_number,
                    "warehouse": warehouse,
                    "reserved_quantity": quantity_to_reserve,
                    "sales_order_created": so_created,
                    "new_total_reserved": inventory_item.reserved,
                    "new_available_quantity": inventory_item.available_quantity  # Property will recalculate
                })
            
            return Response({
                "message": "Inventory allocated successfully.",
                "sales_order_reference": sales_order_ref,
                "sales_order_id": sales_order.id, # Include SalesOrder ID in response
                "allocations_summary": processed_allocations_summary
            }, status=status.HTTP_200_OK)

    except ValueError as e: # Handles custom errors like DoesNotExist, not active/allocatable, insufficient stock
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e: # Catch-all for other unexpected errors
        # It's good practice to log the exception 'e' here for debugging purposes
        return Response({"error": "An unexpected error occurred during allocation.", "detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)