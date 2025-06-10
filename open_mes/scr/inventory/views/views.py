from django.shortcuts import render
from django.views import View
from django.http import HttpResponse, JsonResponse
from django.contrib.auth.mixins import LoginRequiredMixin

# Create your views here.

# --- CSV Template and Import Views (Stubs) for Purchase Orders ---
class PurchaseOrderCSVTemplateView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        csv_content_str = "発注番号,品番コード,倉庫番号,発注数量,入荷予定日(YYYY-MM-DD),サプライヤー名,便番号\nPO-001,ITEM-001,WH-001,100,2023-01-01,株式会社サンプル,DELIVERY-001"
        # Encode to UTF-8 with BOM
        csv_content_bytes = csv_content_str.encode('utf-8-sig')
        response = HttpResponse(csv_content_bytes, content_type='text/csv; charset=utf-8-sig')
        response['Content-Disposition'] = 'attachment; filename="purchase_order_template.csv"'
        return response

class PurchaseOrderImportCSVView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        # TODO: Implement actual CSV import logic for Purchase Orders
        if request.FILES.get('csv_file'):
            return JsonResponse({'status': 'success', 'message': '入庫予定CSVがアップロードされました (処理はスタブ)。'})
        return JsonResponse({'status': 'error', 'message': 'CSVファイルが見つかりません。'}, status=400)
