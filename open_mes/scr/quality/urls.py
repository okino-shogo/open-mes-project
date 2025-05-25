from django.urls import path
from . import views

app_name = 'quality'

urlpatterns = [
    # Existing URLs
    path('menu/', views.QualityMenuView.as_view(), name="quality_menu"),
    path('process_inspection/', views.ProcessInspectionView.as_view(), name="quality_process_inspection"),
    path('acceptance_inspection/', views.AcceptanceInspectionView.as_view(), name="quality_acceptance_inspection"),

    # Inspection Item Master URLs
    path('master_creation/', views.InspectionItemMasterView.as_view(), name='inspection_item_master_list'),
    path('master_creation/create/', views.inspection_item_create, name='inspection_item_create'),
    path('master_creation/update/<uuid:pk>/', views.inspection_item_update, name='inspection_item_update'),
    path('master_creation/delete/<uuid:pk>/', views.inspection_item_delete, name='inspection_item_delete'),
]