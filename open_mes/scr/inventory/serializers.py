from rest_framework import serializers
from .models import PurchaseOrder, Inventory # Inventoryモデルをインポート
from master.models import Item, Supplier, Warehouse # masterアプリケーションからモデルをインポート

class PurchaseOrderSerializer(serializers.ModelSerializer):
    """
    入庫予定モデルのためのシリアライザ。
    作成時には、関連モデルのIDを受け付けます。
    応答時には、読み取り専用フィールドを含む完全なオブジェクトを返します。
    """
    supplier = serializers.CharField(max_length=255, allow_null=True, required=False)
    item = serializers.CharField(max_length=255, allow_null=True, required=False)
    warehouse = serializers.CharField(max_length=255, allow_null=True, required=False)
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # help_text を設定
        self.fields['supplier'].help_text = "仕入先のID (存在しない場合はnull)"
        self.fields['item'].help_text = "品目のID (存在しない場合はnull)"
        self.fields['warehouse'].help_text = "入庫倉庫のID (存在しない場合はnull)"
        
        # 関連オブジェクトがなくても作成できるように required=False を設定
        self.fields['supplier'].required = False
        self.fields['item'].required = False
        self.fields['warehouse'].required = False



    class Meta:
        model = PurchaseOrder
        fields = [
            'id',                   # ID (自動生成、読み取り専用)
            'order_number',         # 発注番号
            'supplier',             # 仕入先 (入力はID、出力はID)
            'item',                 # 品目 (入力はID、出力はID)
            'quantity',             # 発注数量
            'part_number',          # 品番 (任意)
            'product_name',         # 品名 (任意)
            'parent_part_number',   # 親品番 (任意)
            'instruction_document', # 指示書 (任意)
            'shipment_number',      # 便番号 (任意)
            'model_type',           # 機種 (任意)
            'is_first_time',        # 初回 (デフォルトFalse)
            'color_info',           # 色情報 (任意)
            'delivery_destination', # 納入先 (任意)
            'delivery_source',      # 納入元 (任意)
            'remarks1',             # 備考1 (任意)
            'remarks2',             # 備考2 (任意)
            'remarks3',             # 備考3 (任意)
            'remarks4',             # 備考4 (任意)
            'remarks5',             # 備考5 (任意)
            'received_quantity',    # 入庫済数量 (デフォルト0、読み取り専用)
            'order_date',           # 発注日 (自動設定、読み取り専用)
            'expected_arrival',     # 入荷予定日 (任意)
            'warehouse',            # 入庫倉庫 (入力はID、出力はID)
            'status'                # ステータス (デフォルト'pending'、読み取り専用)
        ]
        read_only_fields = ['id', 'received_quantity', 'order_date', 'status'] # is_first_time はデフォルト値があるので読み取り専用には含めません

class InventorySerializer(serializers.ModelSerializer):
    """
    在庫情報モデルのためのシリアライザ。
    available_quantity プロパティも読み取り専用フィールドとして含みます。
    """
    available_quantity = serializers.IntegerField(read_only=True)

    class Meta:
        model = Inventory
        fields = [
            'id',
            'part_number',
            'warehouse',
            'quantity',
            'reserved',
            'available_quantity', # 利用可能在庫 (プロパティ)
            'location',
            'last_updated',
            'is_active',
            'is_allocatable',
        ]
        read_only_fields = ['id', 'last_updated', 'available_quantity']