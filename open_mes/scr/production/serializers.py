from rest_framework import serializers
from .models import ProductionPlan

class ProductionPlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductionPlan
        fields = [
            'id',
            'plan_name',
            'product_code',
            'production_plan', # FK to another ProductionPlan (referenced plan)
            'planned_quantity',
            'planned_start_datetime',
            'planned_end_datetime',
            'actual_start_datetime',
            'actual_end_datetime',
            'status',
            'remarks',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'status'] # status has a default

    def validate(self, data):
        """
        Check that planned_start_datetime is before planned_end_datetime.
        """
        if 'planned_start_datetime' in data and 'planned_end_datetime' in data:
            if data['planned_start_datetime'] >= data['planned_end_datetime']:
                raise serializers.ValidationError({
                    "planned_end_datetime": "Planned end datetime must be after planned start datetime."
                })
        return data