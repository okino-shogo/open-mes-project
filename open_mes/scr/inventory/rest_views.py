from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated # 必要に応じて認証を追加
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination # PageNumberPagination は StandardResultsSetPagination で使用
from .serializers import PurchaseOrderSerializer, InventorySerializer, StockMovementSerializer, AllocateInventoryForSalesOrderRequestSerializer # StockMovementSerializer をインポート
from .models import PurchaseOrder, Inventory, StockMovement, SalesOrder # SalesOrderモデルをインポート
from django.http import JsonResponse # JsonResponse をインポート
from django.db import transaction # トランザクションのためにインポート # Qオブジェクトをインポートして複雑なクエリを構築
from django.db.models import Q, F # Fオブジェクトをインポート
from django.shortcuts import get_object_or_404 # オブジェクト取得のためにインポート
from master.models import Item, Warehouse # masterアプリケーションからItem, Warehouseをインポート (現在は文字列として使用)
from django.contrib.auth.decorators import login_required # 認証が必要な場合 (関数ビュー用)
from django.views import View # クラスベースビュー用
from django.utils.decorators import method_decorator # クラスベースビューでデコレータ使用
from .forms import PurchaseOrderEntryForm # 新しいフォームをインポート

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
def get_stock_movement_data(request): # 関数名を変更
    """
    入出庫履歴データを取得し、JSON形式で返却するビュー (ページネーション対応)
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

        # StockMovement データを取得
        history_items_query = StockMovement.objects.all()

        # 詳細検索フィルタリング
        filters = Q()

        # テキストベースの検索フィールド (icontains)
        text_search_params = {
            'search_part_number': 'part_number__icontains',
            'search_warehouse': 'warehouse__icontains',
            'search_reference_document': 'reference_document__icontains',
            'search_description': 'description__icontains',
            'search_operator': 'operator__username__icontains', # 記録者ユーザー名で検索
        }
        for param, field_lookup in text_search_params.items():
            value = request.GET.get(param)
            if value:
                filters &= Q(**{field_lookup: value})

        # 移動タイプ検索 (OR条件)
        search_movement_types = request.GET.getlist('search_movement_type') # Get a list of types
        if search_movement_types: # If the list is not empty
            # Filter for records where movement_type is one of the selected types
            filters &= Q(movement_type__in=search_movement_types)

        # 数量検索 (完全一致)
        search_quantity = request.GET.get('search_quantity')
        if search_quantity:
            try:
                filters &= Q(quantity=int(search_quantity))
            except ValueError:
                pass # 無効な数値の場合は無視

        # 日付フィールド (範囲検索) - movement_date
        date_search_params = {
            'movement_date': 'movement_date',
        }
        for base_param, field_prefix in date_search_params.items(): # ループは残すが、実際には movement_date のみ
            value = request.GET.get(param)
            date_from = request.GET.get(f'search_{base_param}_from')
            date_to = request.GET.get(f'search_{base_param}_to')
            if date_from:
                filters &= Q(**{f'{field_prefix}__date__gte': date_from})
            if date_to:
                filters &= Q(**{f'{field_prefix}__date__lte': date_to})
        

        if filters: # filtersがQ()のまま（空）でない場合のみ適用
            history_items_query = history_items_query.filter(filters)

        # デフォルトのソート順を移動日時の降順に変更
        history_items = history_items_query.order_by('-movement_date', 'part_number')

        paginator = Paginator(history_items, page_size)

        try:
            history_items_page = paginator.page(page)
        except PageNotAnInteger:
            history_items_page = paginator.page(1) # ページ番号が整数でない場合は1ページ目
        except EmptyPage:
            history_items_page = paginator.page(paginator.num_pages) # ページが空の場合は最終ページ

        # StockMovementSerializer を使用してデータをシリアライズ
        serializer = StockMovementSerializer(history_items_page, many=True)
        data = serializer.data

        # ページネーション情報をレスポンスに含める
        response_data = {
            'count': paginator.count, # 総件数
            'num_pages': paginator.num_pages, # 総ページ数
            'current_page': history_items_page.number, # 現在のページ番号
            'next': history_items_page.next_page_number() if history_items_page.has_next() else None, # 次のページ番号 (なければ None)
            'previous': history_items_page.previous_page_number() if history_items_page.has_previous() else None, # 前のページ番号 (なければ None)
            'results': data # ページングされたデータ
        }
        return JsonResponse(response_data, safe=False)
    else:
        return JsonResponse({'error': 'Invalid request method'}, status=status.HTTP_405_METHOD_NOT_ALLOWED)


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
    requested_warehouse = request.data.get('warehouse') # 新しくリクエストから倉庫情報も取得
    location = request.data.get('location') # 場所情報

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

            # 実際に入庫する倉庫を決定 (リクエストで指定があればそれを優先、なければPOの倉庫)
            target_warehouse = requested_warehouse if requested_warehouse is not None else purchase_order.warehouse
            if not target_warehouse: # POにも設定がなく、リクエストからも来なかった場合
                return Response(
                    {"error": "入庫先の倉庫情報が不明です。発注情報に倉庫を設定するか、処理時に指定してください。"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # 4. 対応する Inventory レコードを検索または新規作成し、数量を更新
            #    Inventory の item と warehouse は PurchaseOrder からの文字列を直接使用
            inventory_item, created = Inventory.objects.get_or_create(
                part_number=purchase_order.part_number, # PurchaseOrder の part_number を使用
                warehouse=target_warehouse, # 実際に入庫する倉庫を使用
                defaults={'quantity': 0, 'location': location} # 新規作成時のデフォルト値を設定 (quantity:0 はモデル定義にもあるが明示)
            ) # location はリクエストから取得
            inventory_item.quantity += actual_received_quantity
 
            # 既存レコードの場合で、かつリクエストに location が指定されていれば更新
            # また、もしget_or_createで取得したInventoryのwarehouseがtarget_warehouseと異なる場合(通常はありえないが)、更新する
            inventory_item.warehouse = target_warehouse # 念のため、取得/作成された在庫の倉庫をターゲットに合わせる
            if not created and location is not None:
                inventory_item.location = location
            inventory_item.save()

            # 5. StockMovement レコードを作成 (入庫履歴)
            StockMovement.objects.create(
                part_number=purchase_order.part_number, # PurchaseOrder の part_number を使用
                warehouse=target_warehouse, # 実際に入庫した倉庫
                movement_type='incoming',
                quantity=actual_received_quantity,
                description=f"PO {purchase_order.order_number} による入庫 (倉庫: {target_warehouse}" + (f", 場所: {location})" if location else ")"),
                operator=request.user if request.user.is_authenticated else None,
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
    page_size = 25  # 1ページあたりのデフォルト件数を25に変更（適宜調整してください）
    page_size_query_param = 'page_size' # クライアントが1ページあたりの件数を指定するためのクエリパラメータ
    max_page_size = 1000 # クライアントが指定できる1ページあたりの最大件数

    def get_paginated_response(self, data):
        return Response({
            'next': self.get_next_link(),
            'previous': self.get_previous_link(),
            'count': self.page.paginator.count,
            'total_pages': self.page.paginator.num_pages,
            'current_page': self.page.number,
            'page_size': self.get_page_size(self.request),
            'results': data
        })


# @login_required # ログインユーザーのみアクセス可能にする場合 (必要に応じてコメント解除)
# @permission_classes([IsAuthenticated]) # 必要に応じて認証を追加
@api_view(['GET']) # DRFの Response を使うため @api_view デコレータを使用
def get_inventory_data(request):
    """
    在庫情報を取得し、JSON形式で返却するビュー (DRFページネーション対応)
    """
    if request.method == 'GET':
        # DRFページネーションを適用
        paginator = StandardResultsSetPagination()

        # フィルタリングのためのクエリパラメータを取得
        part_number_query = request.query_params.get('part_number_query', None)
        warehouse_query = request.query_params.get('warehouse_query', None)
        location_query = request.query_params.get('location_query', None)
        hide_zero_stock_query = request.query_params.get('hide_zero_stock_query', 'false').lower() == 'true'

        filters = Q()
        if part_number_query:
            filters &= Q(part_number__icontains=part_number_query)
        if warehouse_query:
            filters &= Q(warehouse__icontains=warehouse_query)
        if location_query:
            filters &= Q(location__icontains=location_query)

        inventories_qs = Inventory.objects.filter(filters)

        if hide_zero_stock_query:
            # 利用可能在庫が0より大きいものをフィルタリング
            # available_quantity のロジック: is_active=True, is_allocatable=True, quantity > reserved
            inventories_qs = inventories_qs.filter(
                is_active=True,
                is_allocatable=True,
                quantity__gt=F('reserved')
            )

        paginated_inventories = paginator.paginate_queryset(inventories_qs.order_by('part_number', 'warehouse', 'location'), request)

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


@api_view(['POST'])
# @permission_classes([IsAuthenticated]) # Uncomment if authentication is required
def process_single_sales_order_issue_api(request):
    """
    Processes the issuing of items for a single sales order based on provided quantity.

    Request Body (JSON):
    {
      "order_id": "uuid_of_sales_order",
      "quantity_to_ship": 10
    }
    """
    try:
        order_id = request.data.get('order_id')
        quantity_to_ship_str = request.data.get('quantity_to_ship')

        if not order_id or quantity_to_ship_str is None:
            return JsonResponse({'success': False, 'error': 'order_id と quantity_to_ship は必須です。'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            quantity_to_ship = int(quantity_to_ship_str)
            if quantity_to_ship <= 0:
                return JsonResponse({'success': False, 'error': '出庫数量は0より大きい必要があります。'}, status=status.HTTP_400_BAD_REQUEST)
        except ValueError:
            return JsonResponse({'success': False, 'error': '出庫数量は有効な数値である必要があります。'}, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            sales_order = get_object_or_404(SalesOrder.objects.select_for_update(), id=order_id)

            if sales_order.status == 'shipped':
                return JsonResponse({'success': False, 'error': f"受注 {sales_order.order_number} は既に出庫済みです。"}, status=status.HTTP_400_BAD_REQUEST)
            if sales_order.status == 'canceled':
                return JsonResponse({'success': False, 'error': f"受注 {sales_order.order_number} はキャンセルされています。"}, status=status.HTTP_400_BAD_REQUEST)

            if not sales_order.item or not sales_order.warehouse:
                return JsonResponse({'success': False, 'error': f"受注 {sales_order.order_number} に品目または倉庫が指定されていません。"}, status=status.HTTP_400_BAD_REQUEST)

            if quantity_to_ship > sales_order.remaining_quantity:
                return JsonResponse({
                    'success': False,
                    'error': f"出庫数量 ({quantity_to_ship}) が残数量 ({sales_order.remaining_quantity}) を超えています。"
                }, status=status.HTTP_400_BAD_REQUEST)

            try:
                inventory_item = Inventory.objects.select_for_update().get(
                    part_number=sales_order.item,
                    warehouse=sales_order.warehouse
                )
            except Inventory.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'error': f"在庫記録が見つかりません: 品目 {sales_order.item}、倉庫 {sales_order.warehouse} (受注: {sales_order.order_number})"
                }, status=status.HTTP_404_NOT_FOUND)

            if not inventory_item.is_active:
                return JsonResponse({
                    'success': False,
                    'error': f"在庫品目 {sales_order.item} (倉庫: {sales_order.warehouse}) は有効ではありません。"
                }, status=status.HTTP_400_BAD_REQUEST)

            if inventory_item.quantity < quantity_to_ship:
                return JsonResponse({
                    'success': False,
                    'error': f"在庫不足: {sales_order.item} (倉庫: {sales_order.warehouse})。実在庫: {inventory_item.quantity}, 要求: {quantity_to_ship}。"
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Optional: Check reserved quantity consistency, though primary check is on available quantity.
            if inventory_item.reserved < quantity_to_ship:
                 # This might be a warning or an error depending on business logic.
                 # For now, we proceed if total quantity is sufficient, and consume reservation.
                 print(f"Warning for SO {sales_order.order_number}: Reserved quantity ({inventory_item.reserved}) is less than shipping quantity ({quantity_to_ship}). Shipping based on total available stock.")


            # Update Inventory
            inventory_item.quantity -= quantity_to_ship
            inventory_item.reserved -= min(inventory_item.reserved, quantity_to_ship) # Consume reservation
            inventory_item.save()

            # Update SalesOrder
            sales_order.shipped_quantity += quantity_to_ship
            if sales_order.remaining_quantity <= 0:
                sales_order.status = 'shipped'
            sales_order.save()

            # Create StockMovement record
            StockMovement.objects.create(
                part_number=sales_order.item,
                movement_type='outgoing',
                quantity=quantity_to_ship,
                description=f"SO {sales_order.order_number} による出庫 (倉庫: {sales_order.warehouse})",
                operator=request.user if request.user.is_authenticated else None,
            )

            return JsonResponse({'success': True, 'message': f"受注 {sales_order.order_number} から {quantity_to_ship} 個の {sales_order.item} を出庫しました。"})

    except SalesOrder.DoesNotExist:
        return JsonResponse({'success': False, 'error': f"受注ID {order_id} が見つかりません。"}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        # Log the exception e for server-side debugging
        print(f"Error processing single sales order issue: {e}")
        return JsonResponse({'success': False, 'error': f"出庫処理中に予期せぬエラーが発生しました: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
# @permission_classes([IsAuthenticated]) # Ensure user is authenticated
def update_inventory_api(request):
    """
    Updates the quantity of a specific inventory item and records the movement.

    Request Body (JSON):
    {
      "inventory_id": "uuid_of_inventory_item",
      "quantity": 100
    }
    """
    try:
        inventory_id = request.data.get('inventory_id')
        new_quantity_str = request.data.get('quantity')

        if not inventory_id or new_quantity_str is None:
            return Response({'success': False, 'error': 'inventory_id と quantity は必須です。'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            new_quantity = int(new_quantity_str)
            if new_quantity < 0: # 在庫数がマイナスになることは通常許可しない
                return Response({'success': False, 'error': '数量は0以上である必要があります。'}, status=status.HTTP_400_BAD_REQUEST)
        except ValueError:
            return Response({'success': False, 'error': '数量は有効な数値である必要があります。'}, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            inventory_item = get_object_or_404(Inventory.objects.select_for_update(), id=inventory_id)
            
            old_quantity = inventory_item.quantity
            quantity_diff = new_quantity - old_quantity

            if quantity_diff == 0:
                return Response({'success': True, 'message': '在庫数量に変更はありませんでした。', 'data': InventorySerializer(inventory_item).data}, status=status.HTTP_200_OK)

            inventory_item.quantity = new_quantity
            inventory_item.save()

            # Create StockMovement record for the adjustment
            StockMovement.objects.create(
                part_number=inventory_item.part_number,
                warehouse=inventory_item.warehouse,
                movement_type='adjustment', # New movement type
                quantity=abs(quantity_diff), # Movement quantity is always positive
                description=f"在庫修正: {old_quantity} -> {new_quantity} (差分: {quantity_diff})",
                operator=request.user if request.user.is_authenticated else None
            )

            return Response({'success': True, 'message': '在庫数量を更新しました。', 'data': InventorySerializer(inventory_item).data}, status=status.HTTP_200_OK)

    except Inventory.DoesNotExist:
        return Response({'success': False, 'error': f"在庫ID {inventory_id} が見つかりません。"}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        print(f"Error updating inventory: {e}") # Log for server-side debugging
        return Response({'success': False, 'error': f"在庫更新中に予期せぬエラーが発生しました: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
# @permission_classes([IsAuthenticated]) # Uncomment if authentication is required
def get_purchase_orders_api(request):
    """
    Retrieves a paginated list of purchase orders with filtering capabilities.
    This endpoint is used by the purchase receipt page.
    """
    paginator = StandardResultsSetPagination()
    
    filters = Q()

    # Text-based search fields
    search_params_text = {
        'search_order_number': 'order_number__icontains',
        'search_shipment_number': 'shipment_number__icontains',
        'search_supplier': 'supplier__icontains', # Assuming supplier is stored as CharField
        'search_part_number': 'part_number__icontains',
        'search_warehouse': 'warehouse__icontains', # Assuming warehouse is stored as CharField
    }
    for param, field_lookup in search_params_text.items():
        value = request.query_params.get(param)
        if value:
            filters &= Q(**{field_lookup: value})

    # Special search for item/product name
    search_item_product_name = request.query_params.get('search_item_product_name')
    if search_item_product_name:
        filters &= (Q(item__icontains=search_item_product_name) | 
                    Q(product_name__icontains=search_item_product_name))

    # Status filter (exact match)
    search_status = request.query_params.get('search_status')
    if search_status:
        filters &= Q(status=search_status)

    # Date range filters
    date_filters_map = {
        'search_order_date_from': 'order_date__date__gte',
        'search_order_date_to': 'order_date__date__lte',
        'search_expected_arrival_from': 'expected_arrival__date__gte',
        'search_expected_arrival_to': 'expected_arrival__date__lte',
    }
    for param, field_lookup in date_filters_map.items():
        value = request.query_params.get(param)
        if value:
            filters &= Q(**{field_lookup: value})

    # order_by の指定: expected_arrival の昇順、次に order_number の昇順
    # expected_arrival が NULL の場合は最後に表示されるように調整 (Fオブジェクトとasc/desc(nulls_last=True)を使用)
    # Django 3.2以降では F().asc(nulls_last=True) や F().desc(nulls_first=True) が使えますが、
    # それ以前のバージョンやDBによっては annotate と Case/When を使う必要があるかもしれません。
    # ここではシンプルに order_by を使用します。DBによってはNULLの扱いはデフォルトで最後になることがあります。
    # 必要に応じて、より複雑なソートロジックを検討してください。
    purchase_orders_qs = PurchaseOrder.objects.filter(filters).order_by(
        F('expected_arrival').asc(nulls_last=True), 
        'order_number'
    )

    paginated_purchase_orders = paginator.paginate_queryset(purchase_orders_qs, request)
    serializer = PurchaseOrderSerializer(paginated_purchase_orders, many=True)
    
    # DRFのStandardResultsSetPaginationはget_paginated_responseメソッドで
    # 'count', 'next', 'previous', 'results' を含むレスポンスを返します。
    # 'total_pages' や 'current_page' も含めるようにStandardResultsSetPaginationをカスタマイズ済みなので、
    # そのまま paginator.get_paginated_response を使用します。
    return paginator.get_paginated_response(serializer.data)


@method_decorator(login_required, name='dispatch')
class PurchaseOrderCreateAjaxView(View):
    def post(self, request, *args, **kwargs):
        instance_id = request.POST.get('id')
        instance = None
        message_verb = "登録" # Default for new

        if instance_id:
            try:
                instance = PurchaseOrder.objects.get(pk=instance_id)
                message_verb = "更新"
            except PurchaseOrder.DoesNotExist:
                return JsonResponse({'status': 'error', 'message': '指定された入庫予定が見つかりません。'}, status=404)
        
        # Initialize form with instance if updating, otherwise instance is None for new
        form = PurchaseOrderEntryForm(request.POST, instance=instance) 

        if form.is_valid():
            try:
                purchase_order = form.save()
                return JsonResponse({
                    'status': 'success', 
                    'message': f'入庫予定を{message_verb}しました。', 
                    'purchase_order_id': purchase_order.id
                })
            except Exception as e:
                # Log the error e for server-side debugging
                print(f"Error saving PurchaseOrder: {str(e)}") 
                return JsonResponse({'status': 'error', 'message': f'保存中にエラーが発生しました: {str(e)}'}, status=500)
        else:
            return JsonResponse({'status': 'error', 'errors': form.errors, 'message': '入力内容にエラーがあります。'}, status=400)


class PurchaseOrderListAjaxView(View): # No LoginRequiredMixin as it's in rest_views, adjust if needed
    def get(self, request, *args, **kwargs):
        # Using existing get_purchase_orders_api logic might be complex due to pagination differences.
        # For simplicity, a direct query similar to master list views.
        # Note: This doesn't use DRF pagination like get_purchase_orders_api.
        # Consider if the full features of get_purchase_orders_api are needed for this modal.
        # For now, a simpler list for the modal.
        orders = PurchaseOrder.objects.all().order_by('-order_date')[:200] # Limit for performance
        data = [{
            'id': order.id,
            'order_number': order.order_number,
            'supplier': order.supplier,
            'item': order.item,
            'part_number': order.part_number,
            'product_name': order.product_name, # Add product_name for display
            'shipment_number': order.shipment_number or '', # Add shipment_number for display
            'quantity': order.quantity,
            'expected_arrival': order.expected_arrival.strftime('%Y-%m-%d %H:%M') if order.expected_arrival else '',
            'status': order.get_status_display(),
        } for order in orders]
        return JsonResponse({'data': data})

class PurchaseOrderDetailAjaxView(View):
    def get(self, request, pk, *args, **kwargs):
        try:
            order = PurchaseOrder.objects.get(pk=pk)
            # Map all relevant fields from PurchaseOrderEntryForm
            data = {
                'id': order.id,
                'order_number': order.order_number,
                'supplier': order.supplier,
                'item': order.item,
                'part_number': order.part_number,
                'product_name': order.product_name,
                'quantity': order.quantity,
                'expected_arrival': order.expected_arrival.isoformat() if order.expected_arrival else None,
                'warehouse': order.warehouse,
                'parent_part_number': order.parent_part_number,
                'instruction_document': order.instruction_document,
                'shipment_number': order.shipment_number,
                'model_type': order.model_type,
                'is_first_time': order.is_first_time,
                'color_info': order.color_info,
                'delivery_destination': order.delivery_destination,
                'delivery_source': order.delivery_source,
                'remarks1': order.remarks1,
            }
            return JsonResponse({'status': 'success', 'data': data})
        except PurchaseOrder.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Purchase Order not found'}, status=404)

class PurchaseOrderDeleteAjaxView(View):
    def post(self, request, pk, *args, **kwargs):
        try:
            order = PurchaseOrder.objects.get(pk=pk)
            order_number = order.order_number
            order.delete()
            return JsonResponse({'status': 'success', 'message': f'入庫予定「{order_number}」を削除しました。'})
        except PurchaseOrder.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': '指定された入庫予定が見つかりません。'}, status=404)
        except ProtectedError: # If PurchaseOrder is protected by other models
            return JsonResponse({'status': 'error', 'message': 'この入庫予定は他で使用されているため削除できません。'}, status=400)