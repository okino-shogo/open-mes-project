# users/urls.py
from django.urls import path
from .views import views as general_views # UserSettingsView がある views.py
from .views import login, logout # login, logout ビューもインポート

app_name = 'users'

urlpatterns = [
    path('settings/', general_views.UserSettingsView.as_view(), name='users_settings'),
]