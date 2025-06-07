from django.urls import path
from . import views

app_name = 'master'

urlpatterns = [
    path('data-import/', views.DataImportView.as_view(), name='data_import'),
    path('master-creation/', views.MasterCreationView.as_view(), name='master_creation'), # Note: This view seems separate
    path('item/create/', views.ItemCreateAjaxView.as_view(), name='item_create_ajax'),
    path('supplier/create/', views.SupplierCreateAjaxView.as_view(), name='supplier_create_ajax'),
    path('warehouse/create/', views.WarehouseCreateAjaxView.as_view(), name='warehouse_create_ajax'),
    path('item/list/ajax/', views.ItemListAjaxView.as_view(), name='item_list_ajax'),
    path('supplier/list/ajax/', views.SupplierListAjaxView.as_view(), name='supplier_list_ajax'),
    path('warehouse/list/ajax/', views.WarehouseListAjaxView.as_view(), name='warehouse_list_ajax'),
    path('item/<int:pk>/detail/ajax/', views.ItemDetailAjaxView.as_view(), name='item_detail_ajax'),
    path('supplier/<int:pk>/detail/ajax/', views.SupplierDetailAjaxView.as_view(), name='supplier_detail_ajax'),
    path('warehouse/<uuid:pk>/detail/ajax/', views.WarehouseDetailAjaxView.as_view(), name='warehouse_detail_ajax'),
    path('item/<int:pk>/delete/ajax/', views.ItemDeleteAjaxView.as_view(), name='item_delete_ajax'),
    path('supplier/<int:pk>/delete/ajax/', views.SupplierDeleteAjaxView.as_view(), name='supplier_delete_ajax'),
    path('warehouse/<uuid:pk>/delete/ajax/', views.WarehouseDeleteAjaxView.as_view(), name='warehouse_delete_ajax'),

    # CSV Template Download URLs
    path('item/csv-template/', views.ItemCSVTemplateView.as_view(), name='item_csv_template'),
    path('supplier/csv-template/', views.SupplierCSVTemplateView.as_view(), name='supplier_csv_template'),
    path('warehouse/csv-template/', views.WarehouseCSVTemplateView.as_view(), name='warehouse_csv_template'),
    # CSV Import URLs
    path('item/import-csv/', views.ItemImportCSVView.as_view(), name='item_import_csv'),
    path('supplier/import-csv/', views.SupplierImportCSVView.as_view(), name='supplier_import_csv'),
    path('warehouse/import-csv/', views.WarehouseImportCSVView.as_view(), name='warehouse_import_csv'),
]