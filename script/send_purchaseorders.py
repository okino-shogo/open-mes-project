#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import json
import configparser
import os

# ————— 設定 —————
API_URL = "http://127.0.0.1:8000/api/inventory/"

# INIファイルから設定を読み込む
config = configparser.ConfigParser()
# スクリプトのディレクトリを取得
script_dir = os.path.dirname(os.path.abspath(__file__))
config_path = os.path.join(script_dir, 'config.ini')
config.read(config_path)

API_TOKEN = config.get('API', 'TOKEN', fallback=None)

headers = {
    "Content-Type": "application/json",
    # 認証が不要なら以下行はコメントアウト
    "Authorization": f"Token {API_TOKEN}",
}

# ————— POST データ —————
payload = {
    # 必須フィールド
    "order_number": "PO-20250516-001",
    "supplier": "Supplier A",     # Supplier 名
    "item": "Item X",        # Item 名
    "warehouse": "Warehouse 1",    # Warehouse 名
    "quantity": 150,

    # 任意フィールド（必要なら追加）
    "part_number": "PN-AX123",
    "product_name": "Example Widget",
    "parent_part_number": "PPN-0005",
    "instruction_document": "https://example.com/docs/instruction.pdf",
    "shipment_number": "SHP-7890",
    "model_type": "Type-X",
    "is_first_time": True,
    "color_info": "Red",
    "delivery_destination": "Tokyo Warehouse",
    "delivery_source": "Osaka Factory",
    "remarks1": "Urgent order",
    "remarks2": "",
    "remarks3": "",
    "remarks4": "",
    "remarks5": "",
    "expected_arrival": "2025-06-01",
}

def create_purchase_order(data):
    if not API_TOKEN:
        print("エラー: APIトークンがconfig.iniファイルに設定されていません。")
        return
    resp = requests.post(API_URL, headers=headers, data=json.dumps(data))
    if resp.status_code == 201:
        print("入庫予定(PurchaseOrder) を作成しました。")
        print("Response JSON:", resp.json())
    else:
        print(f"エラー: HTTP {resp.status_code}")
        try:
            print("Error details:", resp.json())
        except ValueError:
            pass
            # print(resp.text)

if __name__ == "__main__":
    create_purchase_order(payload)