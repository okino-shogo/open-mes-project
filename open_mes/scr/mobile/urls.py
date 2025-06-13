from django.urls import path
from . import views

app_name = 'mobile'
urlpatterns = [
    path('', views.MobileIndexView.as_view(), name='index'),
    path('login/', views.MobileLoginView.as_view(), name='login'), # モバイル用ログインページのURL
]