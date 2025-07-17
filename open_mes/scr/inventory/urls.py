from django.urls import path
from . import rest_views # inventory/rest_views.py をインポート
from . import views      # views.py をインポート (CSV関連ビューのため)
from .views import menu as inventory_menu

app_name = 'inventory'  # このURL設定の名前空間を変更

urlpatterns = [
    # メニュー関連URL
    path('', inventory_menu.InquiryView.as_view(), name='inquiry'),  # ルートは在庫照会へ
    path('inquiry/', inventory_menu.InquiryView.as_view(), name='inventory_inquiry'),
    path('stock-movement-history/', inventory_menu.StockMovementHistoryView.as_view(), name='inventory_stock_movement_history'),
    path('shipment/', inventory_menu.ShipmentView.as_view(), name='inventory_shipment'),
    path('purchase/', inventory_menu.PurchaseView.as_view(), name='inventory_purchase'),
    path('issue/', inventory_menu.IssueView.as_view(), name='inventory_issue'),

    # API エンドポイント
    path('api/allocate-for-sales-order/', rest_views.allocate_inventory_for_sales_order_api, name='api_allocate_inventory_for_sales_order'),
    path('api/purchase-orders/create/', rest_views.create_purchase_order_api, name='api_create_purchase_order'),
    path('api/stock-movements/data/', rest_views.get_stock_movement_data, name='api_get_stock_movement_data'),
    path('api/purchase-receipts/process/', rest_views.process_purchase_receipt_api, name='api_process_purchase_receipt'),
    path('api/data/', rest_views.get_inventory_data, name='api_get_inventory_data'),
    path('api/issue-single-order/', rest_views.process_single_sales_order_issue_api, name='api_process_single_sales_order_issue'),
    path('api/update/', rest_views.update_inventory_api, name='api_update_inventory'),
    path('api/move/', rest_views.move_inventory_api, name='api_move_inventory'),
    path('api/by-location/', rest_views.get_inventory_by_location_api, name='api_get_inventory_by_location'),
    path('api/location-transfer/', rest_views.location_transfer_api, name='api_location_transfer'),
    path('api/schedules/data/', rest_views.get_purchase_orders_api, name='api_get_purchase_schedules_data'),
    path('api/purchase-order/create-ajax/', rest_views.PurchaseOrderCreateAjaxAPIView.as_view(), name='purchase_order_create_ajax'),
    path('api/purchase-order/list/ajax/', rest_views.PurchaseOrderListAjaxAPIView.as_view(), name='purchase_order_list_ajax'),
    path('api/purchase-order/<uuid:pk>/detail/ajax/', rest_views.PurchaseOrderDetailAjaxAPIView.as_view(), name='purchase_order_detail_ajax'),
    path('api/sales-orders/data/', rest_views.get_sales_orders_for_issue_api, name='api_get_sales_orders_for_issue'),
    path('api/purchase-order/<uuid:pk>/delete/ajax/', rest_views.PurchaseOrderDeleteAjaxAPIView.as_view(), name='purchase_order_delete_ajax'),

    # CSV Template and Import URLs for Purchase Orders
    path('purchase-order/csv-template/', views.PurchaseOrderCSVTemplateView.as_view(), name='purchase_order_csv_template'),
    path('purchase-order/import-csv/', views.PurchaseOrderImportCSVView.as_view(), name='purchase_order_import_csv'),
]