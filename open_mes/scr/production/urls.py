# /home/ubuntu/git/open-mes-project/open_mes/scr/production/urls.py
from django.urls import path
from .views import views # Or directly import the view class
from .views import menu as production_menu_views

app_name = 'production'

urlpatterns = [
    # ... other production urls ...
    path('ajax/plan/create/', views.ProductionPlanCreateAjaxView.as_view(), name='production_plan_create_ajax'),
    path('ajax/parts-used/create/', views.PartsUsedCreateAjaxView.as_view(), name='parts_used_create_ajax'),

    # Production Menu URLs
    path('plan/', production_menu_views.ProductionPlanView.as_view(), name="production_plan"),
    path('parts_used/', production_menu_views.PartsUsedView.as_view(), name="production_parts_used"),
    path('material_allocation/', production_menu_views.MaterialAllocationView.as_view(), name="production_material_allocation"),
    path('work_progress/', production_menu_views.WorkProgressView.as_view(), name="production_work_progress"),
]