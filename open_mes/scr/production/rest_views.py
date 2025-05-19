from rest_framework import viewsets
# from rest_framework import permissions # Uncomment if you want to add permissions
from .models import ProductionPlan
from .serializers import ProductionPlanSerializer

class ProductionPlanViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows Production Plans to be viewed or created.
    """
    queryset = ProductionPlan.objects.all().order_by('-planned_start_datetime')
    serializer_class = ProductionPlanSerializer
    # permission_classes = [permissions.IsAuthenticated] # Example: Add authentication