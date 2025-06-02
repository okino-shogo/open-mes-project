from django.shortcuts import render
from django.views import generic, View # type: ignore
from django.db.models import ProtectedError
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from .forms import ItemForm, SupplierForm, WarehouseForm
from .models import Item, Supplier, Warehouse # Import master models
from production.forms import ProductionPlanDataEntryForm # Import the new form

# Create your views here.

class DataImportView(LoginRequiredMixin, generic.TemplateView):
    template_name = 'master/data_import.html'
    # inventory.formsからPurchaseOrderEntryFormをインポート
    from inventory.forms import PurchaseOrderEntryForm
    from production.forms import PartsUsedDataEntryForm # 使用部品登録フォームをインポート

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'データ投入'
        context['item_form'] = ItemForm()
        context['supplier_form'] = SupplierForm()
        context['warehouse_form'] = WarehouseForm()
        context['inventory_purchase_entry_form'] = self.PurchaseOrderEntryForm() # Add new form to context
        context['parts_used_data_entry_form'] = self.PartsUsedDataEntryForm() # 使用部品登録フォームをコンテキストに追加
        context['production_plan_data_entry_form'] = ProductionPlanDataEntryForm() # Add new form to context
        return context

class MasterCreationView(LoginRequiredMixin, generic.TemplateView):
    template_name = 'master/master_creation.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'マスター作成'
        return context

class ItemCreateAjaxView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        item_id = request.POST.get('id')
        instance = None
        if item_id:
            try:
                instance = Item.objects.get(pk=item_id)
            except Item.DoesNotExist:
                return JsonResponse({'status': 'error', 'message': '指定された品番マスターが見つかりません。'}, status=404)
        
        form = ItemForm(request.POST, instance=instance)
        if form.is_valid():
            form.save()
            message = '品番マスターを更新しました。' if instance else '品番マスターを登録しました。'
            return JsonResponse({'status': 'success', 'message': message})
        else:
            return JsonResponse({'status': 'error', 'errors': form.errors}, status=400)

class SupplierCreateAjaxView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        supplier_id = request.POST.get('id')
        instance = None
        if supplier_id:
            try:
                instance = Supplier.objects.get(pk=supplier_id)
            except Supplier.DoesNotExist:
                return JsonResponse({'status': 'error', 'message': '指定されたサプライヤーマスターが見つかりません。'}, status=404)

        form = SupplierForm(request.POST, instance=instance)
        if form.is_valid():
            form.save()
            message = 'サプライヤーマスターを更新しました。' if instance else 'サプライヤーマスターを登録しました。'
            return JsonResponse({'status': 'success', 'message': message})
        else:
            return JsonResponse({'status': 'error', 'errors': form.errors}, status=400)

class WarehouseCreateAjaxView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        warehouse_id = request.POST.get('id') # UUIDなので注意
        instance = None
        if warehouse_id:
            try:
                instance = Warehouse.objects.get(pk=warehouse_id)
            except Warehouse.DoesNotExist:
                return JsonResponse({'status': 'error', 'message': '指定された倉庫マスターが見つかりません。'}, status=404)
        form = WarehouseForm(request.POST, instance=instance)
        if form.is_valid():
            form.save()
            message = '倉庫マスターを更新しました。' if instance else '倉庫マスターを登録しました。'
            return JsonResponse({'status': 'success', 'message': message})
        else:
            return JsonResponse({'status': 'error', 'errors': form.errors}, status=400)

class ItemListAjaxView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        items = Item.objects.all()
        data = [{
            'id': item.id, # IDを追加
            'code': item.code,
            'name': item.name,
            'item_type': item.get_item_type_display(),
            'unit': item.unit,
            'description': item.description if item.description else ""
        } for item in items]
        return JsonResponse({'data': data})

class SupplierListAjaxView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        suppliers = Supplier.objects.all()
        data = [{
            'id': supplier.id, # IDを追加
            'name': supplier.name,
            'contact_person': supplier.contact_person if supplier.contact_person else "",
            'phone': supplier.phone if supplier.phone else "",
            'email': supplier.email if supplier.email else "",
            'address': supplier.address if supplier.address else ""
        } for supplier in suppliers]
        return JsonResponse({'data': data})

class WarehouseListAjaxView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        warehouses = Warehouse.objects.all()
        data = [{'warehouse_number': wh.warehouse_number, 'name': wh.name, 'location': wh.location if wh.location else ""} for wh in warehouses]
        # WarehouseのIDも追加
        data = [{
            'id': wh.id, # IDを追加
            'warehouse_number': wh.warehouse_number,
            'name': wh.name,
            'location': wh.location if wh.location else ""
        } for wh in warehouses]
        return JsonResponse({'data': data})

# --- ここから単一レコード取得ビューを追加 ---
class ItemDetailAjaxView(LoginRequiredMixin, View):
    def get(self, request, pk, *args, **kwargs):
        try:
            item = Item.objects.get(pk=pk)
            data = {
                'id': item.id, 'name': item.name, 'code': item.code, 
                'item_type': item.item_type, # フォームで選択肢として使うため、表示名ではなく値
                'description': item.description, 'unit': item.unit
            }
            return JsonResponse({'status': 'success', 'data': data})
        except Item.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Item not found'}, status=404)

class SupplierDetailAjaxView(LoginRequiredMixin, View):
    def get(self, request, pk, *args, **kwargs):
        try:
            supplier = Supplier.objects.get(pk=pk)
            data = {
                'id': supplier.id, 'name': supplier.name, 'contact_person': supplier.contact_person,
                'phone': supplier.phone, 'email': supplier.email, 'address': supplier.address
            }
            return JsonResponse({'status': 'success', 'data': data})
        except Supplier.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Supplier not found'}, status=404)

class WarehouseDetailAjaxView(LoginRequiredMixin, View):
    def get(self, request, pk, *args, **kwargs): # pkはUUID
        try:
            warehouse = Warehouse.objects.get(pk=pk)
            data = {'id': warehouse.id, 'warehouse_number': warehouse.warehouse_number, 'name': warehouse.name, 'location': warehouse.location}
            return JsonResponse({'status': 'success', 'data': data})
        except Warehouse.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Warehouse not found'}, status=404)

# --- ここから削除用ビューを追加 ---
class ItemDeleteAjaxView(LoginRequiredMixin, View):
    def post(self, request, pk, *args, **kwargs): # Changed to POST
        try:
            item = Item.objects.get(pk=pk)
            item_name = item.name
            item.delete()
            return JsonResponse({'status': 'success', 'message': f'品番マスター「{item_name}」を削除しました。'})
        except Item.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': '指定された品番マスターが見つかりません。'}, status=404)
        except ProtectedError:
            return JsonResponse({'status': 'error', 'message': 'この品番マスターは他で使用されているため削除できません。関連データを確認してください。'}, status=400)

class SupplierDeleteAjaxView(LoginRequiredMixin, View):
    def post(self, request, pk, *args, **kwargs): # Changed to POST
        try:
            supplier = Supplier.objects.get(pk=pk)
            supplier_name = supplier.name
            supplier.delete()
            return JsonResponse({'status': 'success', 'message': f'サプライヤー「{supplier_name}」を削除しました。'})
        except Supplier.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': '指定されたサプライヤーが見つかりません。'}, status=404)
        except ProtectedError:
            return JsonResponse({'status': 'error', 'message': 'このサプライヤーは他で使用されているため削除できません。関連データを確認してください。'}, status=400)

class WarehouseDeleteAjaxView(LoginRequiredMixin, View):
    def post(self, request, pk, *args, **kwargs): # Changed to POST, pk is UUID
        try:
            warehouse = Warehouse.objects.get(pk=pk)
            warehouse_name = warehouse.name
            warehouse.delete()
            return JsonResponse({'status': 'success', 'message': f'倉庫「{warehouse_name}」を削除しました。'})
        except Warehouse.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': '指定された倉庫が見つかりません。'}, status=404)
        except ProtectedError:
            # WarehouseモデルにForeignKeyで直接関連しているモデルがない場合、このエラーは通常発生しにくい
            # (他のアプリで間接的に参照されている場合は別)
            return JsonResponse({'status': 'error', 'message': 'この倉庫は他で使用されているため削除できません。関連データを確認してください。'}, status=400)
