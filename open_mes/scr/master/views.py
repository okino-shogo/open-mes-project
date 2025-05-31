from django.shortcuts import render
from django.views import generic, View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from .forms import ItemForm, SupplierForm, WarehouseForm


# Create your views here.

class DataImportView(LoginRequiredMixin, generic.TemplateView):
    template_name = 'master/data_import.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'データ投入'
        context['item_form'] = ItemForm()
        context['supplier_form'] = SupplierForm()
        context['warehouse_form'] = WarehouseForm()
        return context

class MasterCreationView(LoginRequiredMixin, generic.TemplateView):
    template_name = 'master/master_creation.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'マスター作成'
        return context

class ItemCreateAjaxView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        form = ItemForm(request.POST)
        if form.is_valid():
            form.save()
            return JsonResponse({'status': 'success', 'message': '品番マスターを登録しました。'})
        else:
            return JsonResponse({'status': 'error', 'errors': form.errors}, status=400)

class SupplierCreateAjaxView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        form = SupplierForm(request.POST)
        if form.is_valid():
            form.save()
            return JsonResponse({'status': 'success', 'message': 'サプライヤーマスターを登録しました。'})
        else:
            return JsonResponse({'status': 'error', 'errors': form.errors}, status=400)

class WarehouseCreateAjaxView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        form = WarehouseForm(request.POST)
        if form.is_valid():
            form.save()
            return JsonResponse({'status': 'success', 'message': '倉庫マスターを登録しました。'})
        else:
            return JsonResponse({'status': 'error', 'errors': form.errors}, status=400)
