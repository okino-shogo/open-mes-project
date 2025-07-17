# /home/ubuntu/git/open-mes-project/open_mes/scr/production/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import views # Or directly import the view class
from .views import menu as production_menu_views
from .views.analytics import ProductionAnalyticsViewSet
from .views.ai_optimization import AIOptimizationViewSet

# REST API Router
router = DefaultRouter()
router.register(r'analytics', ProductionAnalyticsViewSet, basename='analytics')
router.register(r'ai-optimization', AIOptimizationViewSet, basename='ai-optimization')

app_name = 'production'

urlpatterns = [
    # ... other production urls ...
    path('ajax/plan/create/', views.ProductionPlanCreateAjaxView.as_view(), name='production_plan_create_ajax'),
    path('ajax/parts-used/create/', views.PartsUsedCreateAjaxView.as_view(), name='parts_used_create_ajax'),
    path('ajax/plan/list/', views.ProductionPlanListAjaxView.as_view(), name='production_plan_list_ajax'),
    path('ajax/plan/<uuid:pk>/detail/', views.ProductionPlanDetailAjaxView.as_view(), name='production_plan_detail_ajax'),
    path('ajax/plan/<uuid:pk>/delete/', views.ProductionPlanDeleteAjaxView.as_view(), name='production_plan_delete_ajax'),
    path('ajax/parts-used/list/', views.PartsUsedListAjaxView.as_view(), name='parts_used_list_ajax'),
    path('ajax/parts-used/<uuid:pk>/detail/', views.PartsUsedDetailAjaxView.as_view(), name='parts_used_detail_ajax'),
    path('ajax/parts-used/<uuid:pk>/delete/', views.PartsUsedDeleteAjaxView.as_view(), name='parts_used_delete_ajax'),


    # Production Menu URLs
    path('plan/', production_menu_views.ProductionPlanView.as_view(), name="production_plan"),
    path('parts_used/', production_menu_views.PartsUsedView.as_view(), name="production_parts_used"),
    path('material_allocation/', production_menu_views.MaterialAllocationView.as_view(), name="production_material_allocation"),
    path('work_progress/', production_menu_views.WorkProgressView.as_view(), name="production_work_progress"),
    path('gantt_chart/', production_menu_views.GanttChartView.as_view(), name="gantt_chart"),
    path('kaizen/', production_menu_views.KaizenView.as_view(), name="kaizen"),

    # CSV Template and Import URLs
    path('plan/csv-template/', views.ProductionPlanCSVTemplateView.as_view(), name='production_plan_csv_template'),
    path('plan/import-csv/', views.ProductionPlanImportCSVView.as_view(), name='production_plan_import_csv'),
    path('parts-used/csv-template/', views.PartsUsedCSVTemplateView.as_view(), name='parts_used_csv_template'),
    path('parts-used/import-csv/', views.PartsUsedImportCSVView.as_view(), name='parts_used_import_csv'),
    path('csv-upload/', views.CSVUploadView.as_view(), name='csv_upload'),
    
    # Worker Interface URLs
    path('worker-interface/', production_menu_views.WorkerInterfaceView.as_view(), name='worker_interface'),
    path('worker-interface-list/', production_menu_views.WorkerInterfaceListView.as_view(), name='worker_interface_list'),
    
    # Analytics URLs
    path('analytics/', production_menu_views.AnalyticsView.as_view(), name='analytics'),
    path('ai-worker-analysis/', production_menu_views.AIWorkerAnalysisView.as_view(), name='ai_worker_analysis'),
    
    # API URLs
    path('api/', include(router.urls)),
]