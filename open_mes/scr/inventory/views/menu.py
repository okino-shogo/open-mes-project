from django.views import generic
from django.shortcuts import render, redirect
from django.contrib import messages
from django.db import transaction
from ..forms import IssueForm
from ..models import SalesOrder, Inventory, StockMovement

# 在庫メニュー
class InventoryMenuView(generic.TemplateView):
    template_name = 'inventory/menu.html'

    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

# 在庫照会
class InquiryView(generic.TemplateView):
    template_name = 'inventory/inquiry.html'

    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

# 入庫予定
class ScheduleView(generic.TemplateView):
    template_name = 'inventory/schedule.html'

    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

# 出庫予定
class ShipmentView(generic.ListView):
    model = SalesOrder
    template_name = 'inventory/shipment.html'
    context_object_name = 'sales_orders'

    def get_queryset(self):
        """
        Return a list of sales orders that are pending shipment.
        """
        return SalesOrder.objects.filter(status='pending').order_by('expected_shipment', 'order_number')


# 入庫処理
# (PurchaseView remains unchanged for this request)
class PurchaseView(generic.TemplateView):
    template_name = 'inventory/purchase.html'
    
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

# 出庫処理 (Updated View)
class IssueView(generic.View): # Changed from TemplateView
    template_name = 'inventory/issue.html'
    form_class = IssueForm

    def get(self, request, *args, **kwargs):
        form = self.form_class()
        return render(request, self.template_name, {'form': form})

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)
        if form.is_valid():
            sales_order_number = form.cleaned_data['sales_order_number']
            quantity_to_ship = form.cleaned_data['quantity_to_ship']

            try:
                with transaction.atomic():
                    # 1. Find the SalesOrder
                    sales_order = SalesOrder.objects.select_for_update().get(order_number=sales_order_number)

                    # 2. Validate SalesOrder status and quantity
                    if sales_order.status == 'shipped':
                        messages.error(request, f"受注 {sales_order_number} は既に出庫済みです。")
                        return render(request, self.template_name, {'form': form})
                    if sales_order.status == 'canceled':
                        messages.error(request, f"受注 {sales_order_number} はキャンセルされています。")
                        return render(request, self.template_name, {'form': form})

                    if not sales_order.item or not sales_order.warehouse:
                        messages.error(request, f"受注 {sales_order_number} に品目または倉庫が指定されていません。処理を続行できません。")
                        return render(request, self.template_name, {'form': form})

                    remaining_to_ship_on_so = sales_order.quantity - sales_order.shipped_quantity
                    if quantity_to_ship > remaining_to_ship_on_so:
                        messages.error(request, f"出庫数量 ({quantity_to_ship}) が受注残 ({remaining_to_ship_on_so}) を超えています。")
                        return render(request, self.template_name, {'form': form})

                    # 3. Find and update Inventory
                    inventory_item = Inventory.objects.select_for_update().get(
                        part_number=sales_order.item,
                        warehouse=sales_order.warehouse
                    )

                    if not inventory_item.is_active:
                        messages.error(request, f"在庫品目 {sales_order.item} (倉庫: {sales_order.warehouse}) は有効ではありません。")
                        return render(request, self.template_name, {'form': form})

                    if inventory_item.quantity < quantity_to_ship:
                        messages.error(request, f"在庫不足: {sales_order.item} (倉庫: {sales_order.warehouse})。実在庫: {inventory_item.quantity}, 要求: {quantity_to_ship}")
                        return render(request, self.template_name, {'form': form})
                    
                    if inventory_item.reserved < quantity_to_ship:
                        messages.warning(request, f"引当数量 ({inventory_item.reserved}) が要求数量 ({quantity_to_ship}) 未満です。実在庫に基づいて処理しますが、引当状況を確認してください。")

                    inventory_item.quantity -= quantity_to_ship
                    inventory_item.reserved -= min(inventory_item.reserved, quantity_to_ship) # Consume reservation
                    inventory_item.save()

                    # 4. Update SalesOrder
                    sales_order.shipped_quantity += quantity_to_ship
                    if sales_order.shipped_quantity >= sales_order.quantity:
                        sales_order.status = 'shipped'
                    sales_order.save()

                    # 5. Create StockMovement record
                    StockMovement.objects.create(
                        part_number=sales_order.item, # Assumes SalesOrder.item is the part_number
                        movement_type='outgoing',
                        quantity=quantity_to_ship,
                        description=f"SO {sales_order.order_number} による出庫 (倉庫: {sales_order.warehouse})"
                    )

                    messages.success(request, f"受注 {sales_order_number} から {quantity_to_ship} 個の {sales_order.item} を出庫しました。")
                    return redirect('inventory_issue') # Redirect to clear form

            except SalesOrder.DoesNotExist:
                messages.error(request, f"受注番号 {sales_order_number} が見つかりません。")
            except Inventory.DoesNotExist:
                messages.error(request, f"在庫記録が見つかりません: 品目 {getattr(sales_order, 'item', 'N/A')}、倉庫 {getattr(sales_order, 'warehouse', 'N/A')}")
            except Exception as e:
                messages.error(request, f"出庫処理中にエラーが発生しました: {str(e)}")
        
        return render(request, self.template_name, {'form': form})
