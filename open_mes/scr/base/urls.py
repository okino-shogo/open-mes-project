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
from users.views import login, logout, rest
from django.contrib.auth import views as auth_views  # 追記：認証ビューをインポート
from rest_framework.authtoken import views as authtoken_views # authtoken の views をインポート
from machine import views as machine_views

urlpatterns = [
    path('admin/', admin.site.urls),  # Django管理サイトへのURL
    path('', top.TopView.as_view(), name="main"),  # メインページへのURL

    # 在庫関係
    path('inventory/', include('inventory.urls', namespace='inventory')),    

    # Production URLs (Menu and AJAX)
    path('production/', include('production.urls', namespace='production')),

    # 設備関係
    path('machine/menu/', machine_views.MachineMenuView.as_view(), name="machine_menu"),  # メインページへのURL
    path('machine/start_inspection/', machine_views.StartInspectionView.as_view(), name="machine_start_inspection"),
    path('machine/inspection_history/', machine_views.InspectionHistoryView.as_view(), name="machine_inspection_history"),
    path('machine/master_creation/', machine_views.MasterCreationView.as_view(), name="machine_master_creation"),

    # 品質関係
    path('quality/', include('quality.urls', namespace='quality')),
    path('master/', include('master.urls', namespace='master')), # master アプリケーションのURLをインクルード

    # Mobile App URLs
    path('mobile/', include('mobile.urls', namespace='mobile')),

    path('users/', include('users.urls', namespace='users')),  # users アプリケーションのURLをインクルード    

    # API Endpoints
    path('api/token-auth/', authtoken_views.obtain_auth_token, name='api_token_auth'),  # Token authentication endpoint
    path('users/api-register/', rest.register_user, name='users_api_register'),
    # Production API paths
    path('api/production/', include('production.api_urls', namespace='production_api')),

    path("__debug__/", include("debug_toolbar.urls")),
]
