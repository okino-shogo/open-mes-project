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
from inventory import rest_views as inventory_rest_views
from users.views import login, logout, rest
from django.contrib.auth import views as auth_views  # 追記：認証ビューをインポート
from rest_framework.authtoken import views as authtoken_views # authtoken の views をインポート


app_name = "base"



urlpatterns = [
    path('admin/', admin.site.urls),  # Django管理サイトへのURL
    path('', top.TopView.as_view(), name="main"),  # メインページへのURL
    path('inventory/menu/', inventory_menu.InventoryMenuView.as_view(), name="inventory_menu"),  # 在庫管理メニューページへのURL
    path('inventory/inquiry/', inventory_menu.InquiryView.as_view(), name="inventory_inquiry"),  # 在庫照会ページへのURL (在庫照会)
    path('inventory/schedule/', inventory_menu.ScheduleView.as_view(), name="inventory_schedule"),  # 入庫予定ページへのURL (入庫予定)
    path('inventory/shipment/', inventory_menu.ShipmentView.as_view(), name="inventory_shipment"),  # 出庫予定ページへのURL (出庫予定)
    path('inventory/purchase/', inventory_menu.PurchaseView.as_view(), name="inventory_purchase"),  # 入庫処理ページへのURL (入庫処置)
    path('inventory/issue/', inventory_menu.IssueView.as_view(), name="inventory_issue"),  # 出庫処理ページへのURL (出庫処理)    
    path('inventory/schedule/data/', inventory_rest_views.get_schedule_data, name='get_schedule_data'), # 入庫予定データ取得API
    path('api/inventory/', inventory_rest_views.create_purchase_order_api, name='api_create_purchase_order'), 
    # 入庫処理ページで使用されるAPIエンドポイントを追加
    path('inventory/purchase/data/', inventory_rest_views.get_schedule_data, name='inventory_purchase_data'), # 入庫処理対象データ取得API (scheduleと同じビューを使用)
    path('inventory/purchase/scan/', inventory_rest_views.process_purchase_receipt_api, name='inventory_purchase_scan'), # 入庫処理実行API (processビューを使用)

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
    path('users/api-register/', rest.register_user, name='users_api_register'), # カンマを追加
    path('api-token-auth/', authtoken_views.obtain_auth_token), # トークン取得エンドポイント。念のためここにもカンマを追加
    path("__debug__/", include("debug_toolbar.urls")),
]
