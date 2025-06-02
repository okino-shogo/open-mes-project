from django.shortcuts import render
from django.views import View
from django.http import JsonResponse
from django.contrib.auth.mixins import LoginRequiredMixin
from production.forms import ProductionPlanDataEntryForm, PartsUsedDataEntryForm

# Create your views here.

class ProductionPlanCreateAjaxView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        form = ProductionPlanDataEntryForm(request.POST)
        if form.is_valid():
            form.save()
            return JsonResponse({'status': 'success', 'message': '生産計画を登録しました。'})
        else:
            # Add form.errors to the response for debugging or displaying errors
            return JsonResponse({'status': 'error', 'errors': form.errors, 'message': '入力内容にエラーがあります。'}, status=400)

class PartsUsedCreateAjaxView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        form = PartsUsedDataEntryForm(request.POST)
        if form.is_valid():
            form.save()
            # used_datetime はモデルの default=timezone.now で自動設定されます
            return JsonResponse({'status': 'success', 'message': '使用部品を登録しました。'})
        else:
            return JsonResponse({'status': 'error', 'errors': form.errors, 'message': '入力内容にエラーがあります。'}, status=400)
