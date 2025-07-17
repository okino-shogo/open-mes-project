"""
URL configuration for Vercel deployment.
Modified to use demo-friendly views without login requirements.
"""
from django.contrib import admin
from django.urls import include, path, reverse_lazy
from .views import top_vercel
from users.views import login, logout, rest
from django.contrib.auth import views as auth_views
from rest_framework.authtoken import views as authtoken_views
from machine import views as machine_views
from django.http import HttpResponse

# Simple test view
def test_view(request):
    return HttpResponse("Vercel Django App is working!")

urlpatterns = [
    path('test/', test_view, name="test"),  # Simple test endpoint
    path('admin/', admin.site.urls),
    path('', top_vercel.TopView.as_view(), name="main"),  # Vercel demo top view

    # 在庫関係
    path('inventory/', include('inventory.urls', namespace='inventory')),    

    # Production URLs (Menu and AJAX)
    path('production/', include('production.urls', namespace='production')),

    # 設備関係
    path('machine/menu/', machine_views.MachineMenuView.as_view(), name="machine_menu"),
    path('machine/start_inspection/', machine_views.StartInspectionView.as_view(), name="machine_start_inspection"),
    path('machine/inspection_history/', machine_views.InspectionHistoryView.as_view(), name="machine_inspection_history"),
    path('machine/master_creation/', machine_views.MasterCreationView.as_view(), name="machine_master_creation"),

    # 品質関係
    path('quality/', include('quality.urls', namespace='quality')),
    path('master/', include('master.urls', namespace='master')),

    # Mobile App URLs
    path('mobile/', include('mobile.urls', namespace='mobile')),

    path('users/', include('users.urls', namespace='users')),

    # API Endpoints
    path('api/token-auth/', authtoken_views.obtain_auth_token, name='api_token_auth'),
    path('users/api-register/', rest.register_user, name='users_api_register'),
    # Production API paths
    path('api/production/', include('production.api_urls', namespace='production_api')),
]