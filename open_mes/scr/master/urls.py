from django.urls import path
from . import views

app_name = 'master'

urlpatterns = [
    path('data-import/', views.DataImportView.as_view(), name='data_import'),
    path('master-creation/', views.MasterCreationView.as_view(), name='master_creation'), # Note: This view seems separate
    path('item/create/', views.ItemCreateAjaxView.as_view(), name='item_create_ajax'),
    path('supplier/create/', views.SupplierCreateAjaxView.as_view(), name='supplier_create_ajax'),
    path('warehouse/create/', views.WarehouseCreateAjaxView.as_view(), name='warehouse_create_ajax'),
]