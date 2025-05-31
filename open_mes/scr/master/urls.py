from django.urls import path
from . import views

app_name = 'master'

urlpatterns = [
    path('data-import/', views.DataImportView.as_view(), name='data_import'),
]