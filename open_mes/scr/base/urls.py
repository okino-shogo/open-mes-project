"""
URL configuration for base project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import include, path, reverse_lazy
from .views import top
from inventory.views import menu as inventory_menu
from inventory import rest_views as inventory_rest_views # noqa: F401
from production.views import menu as production_menu_views # Renamed to avoid conflict if other menu views exist
from production import rest_views as production_rest_views # Import production rest_views
from users.views import login, logout, rest
from django.contrib.auth import views as auth_views  # 追記：認証ビューをインポート
from rest_framework.routers import DefaultRouter # Import DefaultRouter
from rest_framework.authtoken import views as authtoken_views # authtoken の views をインポート
from machine import views as machine_views
from quality import views as quality_views # quality.viewsをインポート


production_router = DefaultRouter()
production_router.register(r'plans', production_rest_views.ProductionPlanViewSet, basename='production_plan')
production_router.register(r'parts-used', production_rest_views.PartsUsedViewSet, basename='parts_used') # PartsUsedViewSetを登録


urlpatterns = [
    path('admin/', admin.site.urls),  # Django管理サイトへのURL
    path('', top.TopView.as_view(), name="main"),  # メインページへのURL

    # 在庫関係
    # path('inventory/menu/', inventory_menu.InventoryMenuView.as_view(), name="inventory_menu"),  # 在庫管理メニューページへのURL (削除)
    path('inventory/inquiry/', inventory_menu.InquiryView.as_view(), name="inventory_inquiry"),  # 在庫照会ページへのURL (在庫照会)
    path('inventory/schedule/', inventory_menu.ScheduleView.as_view(), name="inventory_schedule"),  # 入庫予定ページへのURL (入庫予定)
    path('inventory/shipment/', inventory_menu.ShipmentView.as_view(), name="inventory_shipment"),  # 出庫予定ページへのURL (出庫予定)
    path('inventory/purchase/', inventory_menu.PurchaseView.as_view(), name="inventory_purchase"),  # 入庫処理ページへのURL (入庫処置)
    path('inventory/issue/', inventory_menu.IssueView.as_view(), name="inventory_issue"),  # 出庫処理ページへのURL (出庫処理)    

    # 生産関係
    # path('production/menu/', production_menu_views.ProductionMenuView.as_view(), name="production_menu"),  # 生産管理メニューページへのURL (削除)
    path('production/plan/', production_menu_views.ProductionPlanView.as_view(), name="production_plan"),  # 生産計画ページへのURL
    path('production/parts_used/', production_menu_views.PartsUsedView.as_view(), name="production_parts_used"),  # 使用部品ページへのURL
    path('production/material_allocation/', production_menu_views.MaterialAllocationView.as_view(), name="production_material_allocation"),  # 材料引当ページへのURL
    path('production/work_progress/', production_menu_views.WorkProgressView.as_view(), name="production_work_progress"),  # 作業進捗ページへのURL

    # 設備関係
    path('machine/menu/', machine_views.MachineMenuView.as_view(), name="machine_menu"),  # メインページへのURL
    path('machine/start_inspection/', machine_views.StartInspectionView.as_view(), name="machine_start_inspection"),
    path('machine/inspection_history/', machine_views.InspectionHistoryView.as_view(), name="machine_inspection_history"),
    path('machine/master_creation/', machine_views.MasterCreationView.as_view(), name="machine_master_creation"),

    # 品質関係
    path('quality/menu/', quality_views.QualityMenuView.as_view(), name="quality_menu"),
    path('quality/process_inspection/', quality_views.ProcessInspectionView.as_view(), name="quality_process_inspection"),
    path('quality/acceptance_inspection/', quality_views.AcceptanceInspectionView.as_view(), name="quality_acceptance_inspection"),
    path('quality/master_creation/', quality_views.MasterCreationView.as_view(), name="quality_master_creation"),

    path('users/login/', login.CustomLoginView.as_view(), name='users_login'),  # 追記：ログインURL
    path('users/logout/', logout.CustomLogoutView.as_view(), name='users_logout'),  # 追記：ログアウトURL
        # --- Django標準のパスワード変更ビューのURLを追加 ---
    path('users/password_change/',
         auth_views.PasswordChangeView.as_view(
             template_name='registration/password_change_form.html', # 使用するテンプレートを指定
             success_url=reverse_lazy('password_change_done') # 変更成功後のリダイレクト先
         ),
         name='password_change'), # ミドルウェアで指定した名前と同じにする
    path('users/password_change/done/',
         auth_views.PasswordChangeDoneView.as_view(
             template_name='registration/password_change_done.html' # 使用するテンプレートを指定
         ),
         name='password_change_done'),
    # --- ここまで ---

    # API Endpoints
    path('api/token-auth/', authtoken_views.obtain_auth_token, name='api_token_auth'),
    path('users/api-register/', rest.register_user, name='users_api_register'),
    # Production API paths (using the router)
    path('api/production/', include(production_router.urls)),
    # Inventory API paths
    path('api/inventory/', include('inventory.urls', namespace='inventory_api')),

    path("__debug__/", include("debug_toolbar.urls")),
]
