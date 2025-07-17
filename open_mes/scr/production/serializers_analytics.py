from rest_framework import serializers
from django.db.models import Avg, Count, Sum, F, Case, When, Value, FloatField
from django.db.models.functions import Extract
from .models import ProductionPlan, WorkProgress
from datetime import datetime, timedelta

class ProcessDurationAnalyticsSerializer(serializers.Serializer):
    """
    工程別所要時間分析用シリアライザー
    """
    process_name = serializers.CharField()
    avg_duration = serializers.FloatField()
    min_duration = serializers.FloatField()
    max_duration = serializers.FloatField()
    total_plans = serializers.IntegerField()
    completion_rate = serializers.FloatField()

class PlanVsActualAnalyticsSerializer(serializers.Serializer):
    """
    予実差分析用シリアライザー
    """
    plan_name = serializers.CharField()
    planned_duration_hours = serializers.FloatField()
    actual_duration_hours = serializers.FloatField()
    variance_hours = serializers.FloatField()
    variance_percentage = serializers.FloatField()
    status = serializers.CharField()
    planned_start = serializers.DateTimeField()
    actual_start = serializers.DateTimeField(allow_null=True)
    planned_end = serializers.DateTimeField()
    actual_end = serializers.DateTimeField(allow_null=True)

class WorkerProductivityAnalyticsSerializer(serializers.Serializer):
    """
    作業者別生産性分析用シリアライザー
    """
    worker_name = serializers.CharField()
    total_completed_tasks = serializers.IntegerField()
    avg_completion_time_hours = serializers.FloatField()
    efficiency_score = serializers.FloatField()
    quality_score = serializers.FloatField()
    favorite_processes = serializers.ListField(child=serializers.CharField())

class DashboardSummarySerializer(serializers.Serializer):
    """
    ダッシュボードサマリー用シリアライザー
    """
    total_plans = serializers.IntegerField()
    completed_plans = serializers.IntegerField()
    in_progress_plans = serializers.IntegerField()
    delayed_plans = serializers.IntegerField()
    avg_completion_rate = serializers.FloatField()
    on_time_delivery_rate = serializers.FloatField()

class ProcessTrendSerializer(serializers.Serializer):
    """
    工程別トレンド分析用シリアライザー
    """
    date = serializers.DateField()
    process_name = serializers.CharField()
    avg_duration = serializers.FloatField()
    completed_count = serializers.IntegerField()