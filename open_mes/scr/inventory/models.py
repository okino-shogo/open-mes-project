from django.db import models
from master.models import Item, Supplier, Warehouse

import uuid
from uuid6 import uuid7

# 在庫情報
class Inventory(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid7, editable=False)  # UUIDv7を使用
    item = models.ForeignKey(Item, on_delete=models.SET_NULL, null=True)  # 管理対象の製品/材料
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE)  # 倉庫と関連付ける
    quantity = models.IntegerField(default=0)  # 在庫
    reserved = models.IntegerField(default=0)  # 引当在庫
    location = models.CharField(max_length=255, blank=True, null=True)  # 倉庫や棚の場所
    last_updated = models.DateTimeField(auto_now=True)  # 更新日時
    is_active = models.BooleanField(default=True)  # 在庫が有効かどうか
    is_allocatable = models.BooleanField(default=True)  # 引き当て可能かどうか

    def __str__(self):
        return f"{self.item.name} - {self.quantity} ({self.location})"
    
    @property
    def available_quantity(self):
        """実際に利用可能な在庫（total - reserved）"""
        if not self.is_active or not self.is_allocatable:
            return 0  # 在庫が無効または引き当て不可なら利用不可
        return max(0, self.quantity - self.reserved)

    def __str__(self):
        status = "Active" if self.is_active else "Inactive"
        allocatable = "Allocatable" if self.is_allocatable else "Not Allocatable"
        return f"{self.item.name} - {self.quantity} in {self.warehouse.warehouse_number} ({self.location}) [{status}, {allocatable}]"



# 入出庫履歴
class StockMovement(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid7, editable=False)
    MOVEMENT_TYPE_CHOICES = [
        ('incoming', 'Incoming'),  # 入庫
        ('outgoing', 'Outgoing'),  # 出庫
        ('used', 'Used in production'),  # 生産で使用
    ]

    item = models.ForeignKey(Item, on_delete=models.CASCADE)  # 在庫対象の製品/材料
    movement_type = models.CharField(max_length=20, choices=MOVEMENT_TYPE_CHOICES)  # 入庫・出庫・使用
    quantity = models.PositiveIntegerField()  # 数量
    timestamp = models.DateTimeField(auto_now_add=True)  # 変更日時
    description = models.TextField(blank=True, null=True)  # 備考

    def __str__(self):
        return f"{self.item.name} - {self.movement_type} - {self.quantity}"


# 入庫予定
class PurchaseOrder(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid7, editable=False)
    order_number = models.CharField(max_length=20, unique=True)  # 発注番号
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE)  # 仕入れ先
    item = models.ForeignKey(Item, on_delete=models.CASCADE)  # 発注対象（製品・材料）
    quantity = models.PositiveIntegerField()  # 発注数量
    received_quantity = models.PositiveIntegerField(default=0) # 実際に入庫した数量を保持
    order_date = models.DateTimeField(auto_now_add=True)  # 発注日
    expected_arrival = models.DateTimeField(blank=True, null=True)  # 到着予定日
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE) # どの倉庫に入庫するかを追加
    status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'),  # 未入庫
        ('received', 'Received'),  # 入庫済み
        ('canceled', 'Canceled')  # キャンセル
    ], default='pending')

    def __str__(self):
        return f"PO {self.order_number} - {self.item.name} ({self.status})"

# 出庫予定
class SalesOrder(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid7, editable=False)
    order_number = models.CharField(max_length=20, unique=True)  # 受注番号
    item = models.ForeignKey(Item, on_delete=models.CASCADE)  # 出庫対象（製品・材料）
    quantity = models.PositiveIntegerField()  # 出庫予定数量
    shipped_quantity = models.PositiveIntegerField(default=0) # 実際に出庫した数量を保持
    order_date = models.DateTimeField(auto_now_add=True)  # 受注日
    expected_shipment = models.DateTimeField(blank=True, null=True)  # 出庫予定日
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE) # どの倉庫から出庫するかを追加
    status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'),  # 未出庫
        ('shipped', 'Shipped'),  # 出庫済み
        ('canceled', 'Canceled')  # キャンセル
    ], default='pending')

    def __str__(self):
        return f"SO {self.order_number} - {self.item.name} ({self.status})"
