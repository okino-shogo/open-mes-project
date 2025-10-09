#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import json
import configparser
from faker import Faker
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

# Faker インスタンスの作成
fake = Faker('ja_JP') # 日本語ロケールを使用



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
    num_records = 1000
    print(f"{num_records}件のテストデータ送信を開始します...")

    for i in range(num_records):
        # ユニークな発注番号を生成 (例: PO-YYYYMMDD-連番)
        order_number = f"PO-{fake.date_object().strftime('%Y%m%d')}-{i+1:04d}"

        # テストデータを生成
        payload = {
            "order_number": order_number,
            "supplier": fake.company(),
            "item": fake.word() + "部品",
            "warehouse": fake.random_element(elements=('倉庫A', '倉庫B', '倉庫C')),
            "quantity": fake.random_int(min=1, max=500),

            "part_number": fake.bothify(text='PN-####-??'),
            "product_name": fake.catch_phrase(),
            "parent_part_number": fake.bothify(text='PPN-####'),
            "instruction_document": fake.url(),
            "shipment_number": fake.bothify(text='SHP-######'),
            "model_type": fake.random_element(elements=('Type-X', 'Type-Y', 'Type-Z', '汎用')),
            "is_first_time": fake.boolean(chance_of_getting_true=20), # 20%の確率でTrue
            "color_info": fake.color_name() if fake.boolean(chance_of_getting_true=50) else None, # 50%の確率で色情報あり
            "delivery_destination": fake.city() + "倉庫",
            "delivery_source": fake.city() + "工場",
            "remarks1": fake.sentence() if fake.boolean(chance_of_getting_true=30) else None,
            "remarks2": fake.sentence() if fake.boolean(chance_of_getting_true=10) else None,
            "remarks3": None,
            "remarks4": None,
            "remarks5": None,
            "expected_arrival": fake.date_time_this_year().isoformat(), # ISO 8601形式
        }
        create_purchase_order(payload)
        print(f"送信済み: {i+1}/{num_records}件 (発注番号: {order_number})")