from django.shortcuts import render, get_object_or_404
from django.views import generic, View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse, HttpResponse
from django.db.models import Q, Prefetch, Sum, F, Case, When, Value, IntegerField, CharField
from django.db import transaction, IntegrityError
from ..models import ProductionPlan, PartsUsed, MaterialAllocation # Changed PartsUsedRecord to PartsUsed
from ..forms import ProductionPlanDataEntryForm, PartsUsedDataEntryForm # Ensure these forms exist
from master.models import Item, Warehouse # If needed for lookups, etc.

# Placeholder for existing views if this file is new or being significantly modified.
# For example, ProductionPlanCreateAjaxView, PartsUsedCreateAjaxView, etc.
# would be here.

# Example of how existing views might look (ensure they are present)
class ProductionPlanCreateAjaxView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        # Simplified existing view logic
        form = ProductionPlanDataEntryForm(request.POST)
        if form.is_valid():
            form.save()
            return JsonResponse({'status': 'success', 'message': 'Production plan created.'})
        return JsonResponse({'status': 'error', 'errors': form.errors}, status=400)

class PartsUsedCreateAjaxView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        # Simplified existing view logic
        form = PartsUsedDataEntryForm(request.POST)
        if form.is_valid():
            form.save()
            return JsonResponse({'status': 'success', 'message': 'Parts used record created.'})
        return JsonResponse({'status': 'error', 'errors': form.errors}, status=400)

class ProductionPlanListAjaxView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        # Simplified existing view logic
        plans = ProductionPlan.objects.all().values('id', 'plan_name', 'product_code', 'planned_quantity', 'planned_start_datetime', 'status')
        return JsonResponse({'data': list(plans)})

class ProductionPlanDetailAjaxView(LoginRequiredMixin, View):
    def get(self, request, pk, *args, **kwargs):
        try:
            plan = ProductionPlan.objects.get(pk=pk)
            data = {
                'id': plan.id, 'plan_name': plan.plan_name, 'product_code': plan.product_code,
                'planned_quantity': plan.planned_quantity,
                'planned_start_datetime': plan.planned_start_datetime.isoformat() if plan.planned_start_datetime else None,
                'status': plan.status
            }
            return JsonResponse({'status': 'success', 'data': data})
        except ProductionPlan.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Production Plan not found'}, status=404)

class ProductionPlanDeleteAjaxView(LoginRequiredMixin, View):
    def post(self, request, pk, *args, **kwargs):
        try:
            plan = ProductionPlan.objects.get(pk=pk)
            plan.delete()
            return JsonResponse({'status': 'success', 'message': 'Production plan deleted.'})
        except ProductionPlan.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Production Plan not found'}, status=404)

class PartsUsedListAjaxView(LoginRequiredMixin, View):
     def get(self, request, *args, **kwargs):
        records = PartsUsed.objects.all().values('id', 'production_plan', 'part_code', 'warehouse', 'quantity_used', 'used_datetime')
        data = [{'production_plan': r['production_plan__plan_name'], 'part_code': r['part_code'], 'warehouse': r['warehouse__name'], 'quantity_used': r['quantity_used'], 'used_datetime': r['used_datetime'].isoformat() if r['used_datetime'] else None, 'id': r['id']} for r in records]
        return JsonResponse({'data': data})

class PartsUsedDetailAjaxView(LoginRequiredMixin, View):
    def get(self, request, pk, *args, **kwargs):
        # Simplified
        return JsonResponse({'status': 'error', 'message': 'Not implemented'}, status=501)

class PartsUsedDeleteAjaxView(LoginRequiredMixin, View):
    def post(self, request, pk, *args, **kwargs):
        # Simplified
        return JsonResponse({'status': 'error', 'message': 'Not implemented'}, status=501)

# --- CSV Template and Import Views (Stubs) ---
class ProductionPlanCSVTemplateView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        # TODO: Implement actual CSV template generation
        response = HttpResponse("計画名,製品コード,計画数量,計画開始日時(YYYY-MM-DD HH:MM),計画終了日時(YYYY-MM-DD HH:MM),備考,親計画ID(任意)\n計画A,PROD-001,100,2023-01-01 09:00,2023-01-01 17:00,特記事項, (空白または親計画のID)", content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="production_plan_template.csv"'
        return response

class ProductionPlanImportCSVView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        # TODO: Implement actual CSV import logic
        return JsonResponse({'status': 'success', 'message': '生産計画CSVがインポートされました (スタブ)。'})

class PartsUsedCSVTemplateView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        # TODO: Implement actual CSV template generation
        response = HttpResponse("生産計画ID,部品コード,倉庫番号,使用数量,使用日時(YYYY-MM-DD HH:MM)\n1,PART-001,WH-001,10,2023-01-01 10:00", content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="parts_used_template.csv"'
        return response

class PartsUsedImportCSVView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        # TODO: Implement actual CSV import logic
        return JsonResponse({'status': 'success', 'message': '使用部品CSVがインポートされました (スタブ)。'})