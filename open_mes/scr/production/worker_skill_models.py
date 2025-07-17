"""
作業者スキル分析・管理用モデル
"""

from django.db import models
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
import uuid
from uuid6 import uuid7


class WorkerSkillProfile(models.Model):
    """
    作業者スキルプロファイル
    各作業者の工程別スキルレベルと習熟度を管理
    """
    SKILL_LEVEL_CHOICES = [
        (1, '初級'),
        (2, '中級'),
        (3, '上級'),
        (4, '熟練'),
        (5, 'エキスパート'),
    ]
    
    PROCESS_CHOICES = [
        ('slit', 'スリット'),
        ('cut', 'カット'),
        ('base_material_cut', '基材カット'),
        ('molder', 'モルダー'),
        ('v_cut_lapping', 'Vカットラッピング'),
        ('post_processing', '後加工'),
        ('packing', '梱包'),
        ('decorative_board', '化粧板貼付'),
        ('decorative_board_cut', '化粧板カット'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid7, editable=False)
    worker = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='skill_profiles',
        verbose_name="作業者"
    )
    process_type = models.CharField(
        max_length=50,
        choices=PROCESS_CHOICES,
        verbose_name="工程種類"
    )
    
    # スキルレベル指標
    skill_level = models.IntegerField(
        choices=SKILL_LEVEL_CHOICES,
        default=1,
        verbose_name="スキルレベル"
    )
    efficiency_score = models.FloatField(
        default=100.0,
        verbose_name="効率スコア(%)"
    )
    quality_score = models.FloatField(
        default=100.0,
        verbose_name="品質スコア(%)"
    )
    
    # 統計データ
    total_tasks_completed = models.IntegerField(
        default=0,
        verbose_name="総完了タスク数"
    )
    average_completion_time = models.FloatField(
        default=0.0,
        verbose_name="平均完了時間(分)"
    )
    best_completion_time = models.FloatField(
        default=0.0,
        verbose_name="最高完了時間(分)"
    )
    defect_rate = models.FloatField(
        default=0.0,
        verbose_name="不良率(%)"
    )
    
    # 学習進捗
    learning_progress = models.FloatField(
        default=0.0,
        verbose_name="学習進捗(%)"
    )
    last_improvement_date = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="最終改善日"
    )
    
    # 推薦レベル
    recommendation_confidence = models.FloatField(
        default=0.0,
        verbose_name="推薦信頼度(%)"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "作業者スキルプロファイル"
        verbose_name_plural = "作業者スキルプロファイル"
        unique_together = ['worker', 'process_type']
    
    def __str__(self):
        return f"{self.worker.username} - {self.get_process_type_display()} (Lv.{self.skill_level})"


class WorkerPerformanceHistory(models.Model):
    """
    作業者パフォーマンス履歴
    時系列でのパフォーマンス変化を記録
    """
    id = models.UUIDField(primary_key=True, default=uuid7, editable=False)
    worker = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='performance_history',
        verbose_name="作業者"
    )
    production_plan = models.ForeignKey(
        'ProductionPlan',
        on_delete=models.CASCADE,
        related_name='worker_performances',
        verbose_name="生産計画"
    )
    process_type = models.CharField(
        max_length=50,
        choices=WorkerSkillProfile.PROCESS_CHOICES,
        verbose_name="工程種類"
    )
    
    # パフォーマンス指標
    completion_time_minutes = models.FloatField(verbose_name="完了時間(分)")
    planned_time_minutes = models.FloatField(verbose_name="計画時間(分)")
    efficiency_ratio = models.FloatField(verbose_name="効率比率")
    
    # 品質指標
    quantity_completed = models.IntegerField(verbose_name="完了数量")
    defect_count = models.IntegerField(default=0, verbose_name="不良数")
    quality_ratio = models.FloatField(verbose_name="品質比率")
    
    # 環境要因
    workload_factor = models.FloatField(default=1.0, verbose_name="作業負荷係数")
    time_of_day = models.TimeField(verbose_name="作業時間帯")
    day_of_week = models.IntegerField(verbose_name="曜日")
    
    # 学習効果
    cumulative_experience = models.IntegerField(verbose_name="累積経験値")
    learning_effect = models.FloatField(verbose_name="学習効果係数")
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "作業者パフォーマンス履歴"
        verbose_name_plural = "作業者パフォーマンス履歴"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.worker.username} - {self.get_process_type_display()} ({self.created_at.strftime('%Y-%m-%d')})"


class WorkerOptimizationRecommendation(models.Model):
    """
    作業者最適化推薦
    AIが生成した作業者配置・改善提案
    """
    RECOMMENDATION_TYPE_CHOICES = [
        ('assignment', '配置推薦'),
        ('training', '訓練推薦'),
        ('improvement', '改善推薦'),
        ('warning', '警告・注意'),
    ]
    
    PRIORITY_CHOICES = [
        ('low', '低'),
        ('medium', '中'),
        ('high', '高'),
        ('urgent', '緊急'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid7, editable=False)
    worker = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='optimization_recommendations',
        verbose_name="対象作業者"
    )
    
    recommendation_type = models.CharField(
        max_length=20,
        choices=RECOMMENDATION_TYPE_CHOICES,
        verbose_name="推薦タイプ"
    )
    priority = models.CharField(
        max_length=10,
        choices=PRIORITY_CHOICES,
        verbose_name="優先度"
    )
    
    # 推薦内容
    title = models.CharField(max_length=200, verbose_name="推薦タイトル")
    description = models.TextField(verbose_name="推薦内容")
    target_process = models.CharField(
        max_length=50,
        choices=WorkerSkillProfile.PROCESS_CHOICES,
        null=True,
        blank=True,
        verbose_name="対象工程"
    )
    
    # AI分析結果
    confidence_score = models.FloatField(verbose_name="信頼度スコア")
    expected_improvement = models.FloatField(
        null=True,
        blank=True,
        verbose_name="期待改善効果(%)"
    )
    analysis_data = models.JSONField(
        null=True,
        blank=True,
        verbose_name="分析データ"
    )
    
    # 実行状況
    is_implemented = models.BooleanField(
        default=False,
        verbose_name="実装済み"
    )
    implementation_date = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="実装日"
    )
    actual_improvement = models.FloatField(
        null=True,
        blank=True,
        verbose_name="実際の改善効果(%)"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="有効期限"
    )
    
    class Meta:
        verbose_name = "作業者最適化推薦"
        verbose_name_plural = "作業者最適化推薦"
        ordering = ['-priority', '-created_at']
    
    def __str__(self):
        return f"{self.worker.username} - {self.title} ({self.get_priority_display()})"
    
    def is_expired(self):
        """推薦が期限切れかどうか"""
        if self.expires_at:
            return timezone.now() > self.expires_at
        return False


class TeamOptimizationSession(models.Model):
    """
    チーム最適化セッション
    特定の期間・プロジェクトに対する最適化結果
    """
    id = models.UUIDField(primary_key=True, default=uuid7, editable=False)
    session_name = models.CharField(max_length=200, verbose_name="セッション名")
    target_date = models.DateField(verbose_name="対象日")
    
    # 最適化結果
    optimization_result = models.JSONField(verbose_name="最適化結果")
    expected_efficiency = models.FloatField(verbose_name="期待効率(%)")
    confidence_level = models.FloatField(verbose_name="信頼度レベル")
    
    # 実行結果
    actual_efficiency = models.FloatField(
        null=True,
        blank=True,
        verbose_name="実際の効率(%)"
    )
    is_executed = models.BooleanField(
        default=False,
        verbose_name="実行済み"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name="作成者"
    )
    
    class Meta:
        verbose_name = "チーム最適化セッション"
        verbose_name_plural = "チーム最適化セッション"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.session_name} - {self.target_date}"