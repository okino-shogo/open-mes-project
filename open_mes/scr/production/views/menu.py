from django.views import generic
from ..models import ProductionPlan # Import the ProductionPlan model

    
# 生産計画
class ProductionPlanView(generic.TemplateView):
    template_name = 'production/production_plan.html'


# 使用部品
class PartsUsedView(generic.TemplateView):
    template_name = 'production/parts_used.html'


# 材料引当
class MaterialAllocationView(generic.TemplateView):
    template_name = 'production/material_allocation.html'

# 作業進捗 (生産計画一覧をAPI経由で表示)
class WorkProgressView(generic.TemplateView):
    template_name = 'production/work_progress.html'

# ガントチャート表示
class GanttChartView(generic.TemplateView):
    template_name = 'production/gantt_chart.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from ..utils import get_gantt_chart_data
        
        # 日付フィルター
        start_date = self.request.GET.get('start_date')
        end_date = self.request.GET.get('end_date')
        
        chart_data = get_gantt_chart_data(start_date, end_date)
        context.update(chart_data)
        
        return context

# 改善提案 (Kaizen)
class KaizenView(generic.TemplateView):
    template_name = 'production/kaizen.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from ..models import Kaizen
        
        # ステータス・優先度フィルター
        status_filter = self.request.GET.get('status')
        priority_filter = self.request.GET.get('priority')
        
        kaizen_list = Kaizen.objects.all()
        
        if status_filter:
            kaizen_list = kaizen_list.filter(status=status_filter)
        if priority_filter:
            kaizen_list = kaizen_list.filter(priority=priority_filter)
        
        context['kaizen_list'] = kaizen_list
        context['status_choices'] = Kaizen.STATUS_CHOICES
        context['priority_choices'] = Kaizen.PRIORITY_CHOICES
        
        return context

# 作業者インターフェース
class WorkerInterfaceView(generic.TemplateView):
    template_name = 'production/worker_interface.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # 必要に応じて初期データをコンテキストに追加
        return context

# 作業者インターフェース（リスト形式）
class WorkerInterfaceListView(generic.TemplateView):
    template_name = 'production/worker_interface_list.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # 必要に応じて初期データをコンテキストに追加
        return context

# 生産性分析ダッシュボード
class AnalyticsView(generic.TemplateView):
    template_name = 'production/analytics.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # 分析期間のデフォルト値を設定
        context['default_days'] = 30
        return context

# AI作業者分析ダッシュボード
class AIWorkerAnalysisView(generic.TemplateView):
    template_name = 'production/ai_dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # AI分析の初期設定
        context['default_analysis_type'] = 'individual'
        context['default_days'] = 30
        return context
