from django.shortcuts import render
from django.views import View
from django.http import JsonResponse
from django.db.models import ProtectedError
from django.contrib.auth.mixins import LoginRequiredMixin
from production.forms import ProductionPlanDataEntryForm, PartsUsedDataEntryForm
from ..models import ProductionPlan, PartsUsed # Import models

# Create your views here.

class ProductionPlanCreateAjaxView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        plan_id = request.POST.get('id')
        instance = None
        if plan_id:
            try:
                instance = ProductionPlan.objects.get(pk=plan_id)
            except ProductionPlan.DoesNotExist:
                return JsonResponse({'status': 'error', 'message': '指定された生産計画が見つかりません。'}, status=404)

        form = ProductionPlanDataEntryForm(request.POST, instance=instance)
        if form.is_valid():
            form.save()
            message = '生産計画を更新しました。' if instance else '生産計画を登録しました。'
            return JsonResponse({'status': 'success', 'message': message})
        else:
            # Add form.errors to the response for debugging or displaying errors
            return JsonResponse({'status': 'error', 'errors': form.errors, 'message': '入力内容にエラーがあります。'}, status=400)

class PartsUsedCreateAjaxView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        parts_used_id = request.POST.get('id')
        instance = None
        if parts_used_id:
            try:
                instance = PartsUsed.objects.get(pk=parts_used_id)
            except PartsUsed.DoesNotExist:
                return JsonResponse({'status': 'error', 'message': '指定された使用部品データが見つかりません。'}, status=404)

        form = PartsUsedDataEntryForm(request.POST, instance=instance)
        if form.is_valid():
            form.save()
            # used_datetime はモデルの default=timezone.now で自動設定されます
            message = '使用部品データを更新しました。' if instance else '使用部品を登録しました。'
            return JsonResponse({'status': 'success', 'message': message})
        else:
            return JsonResponse({'status': 'error', 'errors': form.errors, 'message': '入力内容にエラーがあります。'}, status=400)

class ProductionPlanListAjaxView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        plans = ProductionPlan.objects.all().order_by('-created_at')[:200] # Limit for performance
        data = [{
            'id': plan.id,
            'plan_name': plan.plan_name,
            'product_code': plan.product_code,
            'planned_quantity': plan.planned_quantity,
            'planned_start_datetime': plan.planned_start_datetime.strftime('%Y-%m-%d %H:%M') if plan.planned_start_datetime else '',
            'status': plan.get_status_display(),
        } for plan in plans]
        return JsonResponse({'data': data})

class ProductionPlanDetailAjaxView(LoginRequiredMixin, View):
    def get(self, request, pk, *args, **kwargs):
        try:
            plan = ProductionPlan.objects.get(pk=pk)
            data = {
                'id': plan.id,
                'plan_name': plan.plan_name,
                'product_code': plan.product_code,
                'production_plan': plan.production_plan,
                'planned_quantity': plan.planned_quantity,
                'planned_start_datetime': plan.planned_start_datetime.isoformat() if plan.planned_start_datetime else None,
                'planned_end_datetime': plan.planned_end_datetime.isoformat() if plan.planned_end_datetime else None,
                'remarks': plan.remarks,
                # 'status' is not usually part of the entry form, but handled by another process
            }
            return JsonResponse({'status': 'success', 'data': data})
        except ProductionPlan.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Production Plan not found'}, status=404)

class ProductionPlanDeleteAjaxView(LoginRequiredMixin, View):
    def post(self, request, pk, *args, **kwargs):
        try:
            plan = ProductionPlan.objects.get(pk=pk)
            plan_name = plan.plan_name
            plan.delete()
            return JsonResponse({'status': 'success', 'message': f'生産計画「{plan_name}」を削除しました。'})
        except ProductionPlan.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': '指定された生産計画が見つかりません。'}, status=404)
        except ProtectedError:
            return JsonResponse({'status': 'error', 'message': 'この生産計画は他で使用されているため削除できません。'}, status=400)

class PartsUsedListAjaxView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        parts_used_list = PartsUsed.objects.all().order_by('-created_at')[:200] # Limit for performance
        data = [{
            'id': pu.id,
            'production_plan': pu.production_plan, # This is a CharField
            'part_code': pu.part_code,
            'warehouse': pu.warehouse if pu.warehouse else '',
            'quantity_used': pu.quantity_used,
            'used_datetime': pu.used_datetime.strftime('%Y-%m-%d %H:%M') if pu.used_datetime else '',
        } for pu in parts_used_list]
        return JsonResponse({'data': data})

class PartsUsedDetailAjaxView(LoginRequiredMixin, View):
    def get(self, request, pk, *args, **kwargs):
        try:
            pu = PartsUsed.objects.get(pk=pk)
            data = {
                'id': pu.id,
                'production_plan': pu.production_plan,
                'part_code': pu.part_code,
                'warehouse': pu.warehouse,
                'quantity_used': pu.quantity_used,
                'remarks': pu.remarks,
            }
            return JsonResponse({'status': 'success', 'data': data})
        except PartsUsed.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Parts Used record not found'}, status=404)

class PartsUsedDeleteAjaxView(LoginRequiredMixin, View):
    def post(self, request, pk, *args, **kwargs):
        try:
            pu = PartsUsed.objects.get(pk=pk)
            pu_identifier = f"ID: {pu.id}, Plan: {pu.production_plan}, Part: {pu.part_code}"
            pu.delete()
            return JsonResponse({'status': 'success', 'message': f'使用部品データ ({pu_identifier}) を削除しました。'})
        except PartsUsed.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': '指定された使用部品データが見つかりません。'}, status=404)
        except ProtectedError: # Should not happen if PartsUsed is not a FK target for on_delete=PROTECT
            return JsonResponse({'status': 'error', 'message': 'この使用部品データは他で使用されているため削除できません。'}, status=400)
