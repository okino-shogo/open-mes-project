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
]