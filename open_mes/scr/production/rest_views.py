from rest_framework import viewsets
# from rest_framework import permissions # Uncomment if you want to add permissions
from .models import ProductionPlan, PartsUsed # PartsUsedモデルをインポート
from .serializers import ProductionPlanSerializer, PartsUsedSerializer # PartsUsedSerializerをインポート
from inventory.rest_views import StandardResultsSetPagination # inventoryアプリのページネーションクラスをインポート

class ProductionPlanViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows Production Plans to be viewed or created.
    """
    queryset = ProductionPlan.objects.all().order_by('-planned_start_datetime')
    serializer_class = ProductionPlanSerializer
    pagination_class = StandardResultsSetPagination # ページネーションクラスを指定
    # permission_classes = [permissions.IsAuthenticated] # Example: Add authentication

class PartsUsedViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows PartsUsed records to be viewed or created.
    """
    queryset = PartsUsed.objects.all().order_by('-used_datetime')
    serializer_class = PartsUsedSerializer
    pagination_class = StandardResultsSetPagination # ページネーションクラスを指定
    # permission_classes = [permissions.IsAuthenticated] # Example: Add authentication