from django.urls import path
from . import rest_views # inventory/rest_views.py をインポート

app_name = 'inventory_api'  # このURL設定の名前空間

urlpatterns = [
    # 問題のあった材料引当APIエンドポイント
    path('allocate-for-sales-order/', rest_views.allocate_inventory_for_sales_order_api, name='api_allocate_inventory_for_sales_order'),

    # その他の在庫関連APIエンドポイント
    path('purchase-orders/create/', rest_views.create_purchase_order_api, name='api_create_purchase_order'),
    path('stock-movements/data/', rest_views.get_stock_movement_data, name='api_get_stock_movement_data'), # APIパスを変更
    path('purchase-receipts/process/', rest_views.process_purchase_receipt_api, name='api_process_purchase_receipt'),
    path('data/', rest_views.get_inventory_data, name='api_get_inventory_data'),
    path('issue-single-order/', rest_views.process_single_sales_order_issue_api, name='api_process_single_sales_order_issue'),
    path('update/', rest_views.update_inventory_api, name='api_update_inventory'),

    # Endpoint for the purchase.html page to fetch purchase order data
    path('schedules/data/', rest_views.get_purchase_orders_api, name='api_get_purchase_schedules_data'),
]