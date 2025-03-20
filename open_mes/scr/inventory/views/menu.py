from django.views import generic

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
class ShipmentView(generic.TemplateView):
    template_name = 'inventory/shipment.html'

    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


# 入庫処理
class PurchaseView(generic.TemplateView):
    template_name = 'inventory/purchase.html'
    
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

# 出庫処理
class IssueView(generic.TemplateView):
    template_name = 'inventory/issue.html'

    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
