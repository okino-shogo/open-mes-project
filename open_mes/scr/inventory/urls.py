from django.urls import path
from . import rest_views # inventory/rest_views.py をインポート

app_name = 'inventory_api'  # このURL設定の名前空間

urlpatterns = [
    # 問題のあった材料引当APIエンドポイント
    path('allocate-for-sales-order/', rest_views.allocate_inventory_for_sales_order_api, name='api_allocate_inventory_for_sales_order'),

    # その他の在庫関連APIエンドポイント
    path('purchase-orders/create/', rest_views.create_purchase_order_api, name='api_create_purchase_order'),
    path('schedules/data/', rest_views.get_schedule_data, name='api_get_schedule_data'),
    path('purchase-receipts/process/', rest_views.process_purchase_receipt_api, name='api_process_purchase_receipt'),
    path('data/', rest_views.get_inventory_data, name='api_get_inventory_data'),
]