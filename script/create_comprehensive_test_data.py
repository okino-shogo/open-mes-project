# Filename: create_comprehensive_test_data.py
#
# Purpose:
# This script generates a large volume of test data for an Open MES system via its API.
# It creates:
# 1. Production Plans.
# 2. PartsUsed entries for each Production Plan.
# 3. Purchase Orders based on the PartsUsed entries (simulating replenishment).
#
# How to run:
# 1. Ensure your Django project is running and all relevant API endpoints are active.
#    - Production Plans: /api/production/plans/
#    - Parts Used: /api/production/parts-used/
#    - Purchase Orders: /api/inventory/purchase-orders/ (VERIFY THIS ENDPOINT)
# 2. Make sure 'requests' and 'Faker' are installed: pip install requests Faker
# 3. Ensure 'config.ini' is present in the same directory as this script and contains
#    a valid API_TOKEN under the [API] section.
# 4. Run from terminal: python create_comprehensive_test_data.py

import requests
import json
import configparser
import os
from datetime import datetime, timezone, timedelta
from faker import Faker
import random

# --- Configuration ---
API_BASE_URL = "http://127.0.0.1:8000/api" # Adjust if your API base URL is different
PRODUCTION_PLANS_ENDPOINT = f"{API_BASE_URL}/production/plans/"
PARTS_USED_ENDPOINT = f"{API_BASE_URL}/production/parts-used/"
# !!! ATTENTION: Verify this endpoint for PurchaseOrders in your Django app's urls.py !!!
PURCHASE_ORDERS_ENDPOINT = f"{API_BASE_URL}/inventory/"

# --- Load API Token ---
API_TOKEN = None
HEADERS = {"Content-Type": "application/json"}
try:
    config = configparser.ConfigParser()
    script_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(script_dir, 'config.ini')
    config.read(config_path)
    API_TOKEN = config.get('API', 'TOKEN', fallback=None)
    if API_TOKEN:
        HEADERS["Authorization"] = f"Token {API_TOKEN}"
    else:
        print("警告: config.ini に API_TOKEN が見つかりません。リクエストは認証なしで送信されます。")
except Exception as e:
    print(f"警告: config.ini からAPIトークンを読み取れませんでした。エラー: {e}")

# --- Faker Instance ---
fake = Faker('ja_JP') # 日本語ロケール

# --- Global Counter for unique PO numbers ---
purchase_order_number_counter = 1

# --- API Helper Functions ---

def _make_api_request(method, url, data=None, params=None):
    """Helper function to make API requests and handle common errors."""
    if not API_TOKEN:
        print(f"エラー: API_TOKEN が設定されていません。 {url} への認証付きリクエストは送信できません。")
        return None
    try:
        response = requests.request(method, url, json=data, params=params, headers=HEADERS)
        response.raise_for_status() # Raises HTTPError for 4XX/5XX status
        return response.json()
    except requests.exceptions.HTTPError as http_err:
        print(f"HTTPエラー発生 ({method} {url}): {http_err}")
        print(f"レスポンスステータス: {http_err.response.status_code}")
        try:
            print(f"レスポンス内容: {json.dumps(http_err.response.json(), indent=2, ensure_ascii=False)}")
        except json.JSONDecodeError:
            print(f"レスポンス内容 (raw): {http_err.response.text}")
        return None
    except requests.exceptions.RequestException as req_err:
        print(f"リクエストエラー発生 ({method} {url}): {req_err}")
        return None
    except Exception as e:
        print(f"予期せぬエラー発生 ({method} {url}): {e}")
        return None

def create_production_plan_api():
    """API経由で新しい生産計画を作成します。"""
    global fake
    
    start_date = datetime.now(timezone.utc) + timedelta(days=fake.random_int(min=1, max=30))
    end_date = start_date + timedelta(days=fake.random_int(min=30, max=90)) # Ensure end_date is after start_date

    payload = {
        'plan_name': f'生産計画 {fake.company_suffix()} {fake.random_int(min=100, max=999)} ({fake.word()})',
        'product_code': f'製品-{fake.bothify(text="???-####").upper()}',
        'production_plan': None,  # トップレベル計画
        'planned_quantity': fake.random_int(min=50, max=2000),
        'planned_start_datetime': start_date.isoformat(),
        'planned_end_datetime': end_date.isoformat(),
        'remarks': fake.sentence(nb_words=10)
    }
    print(f"  生産計画を作成試行: {payload['plan_name']}")
    response_data = _make_api_request("POST", PRODUCTION_PLANS_ENDPOINT, data=payload)
    if response_data and response_data.get('id'):
        print(f"  生産計画の作成成功 ID: {response_data['id']}")
        return response_data['id']
    else:
        print(f"  生産計画の作成失敗。")
        return None

def create_parts_used_api(production_plan_id):
    """指定された生産計画IDに対して使用部品エントリを作成します。"""
    global fake
    # 部品は最近使用されたと仮定
    used_datetime_obj = fake.date_time_between(start_date="-30d", end_date="now", tzinfo=timezone.utc)
    
    payload = {
        "production_plan": production_plan_id,
        "part_code": f"部品-{fake.bothify(text='??##-###?').upper()}",
        "quantity_used": fake.random_int(min=1, max=50),
        "used_datetime": used_datetime_obj.isoformat(),
        "remarks": fake.sentence(nb_words=7) if fake.boolean(chance_of_getting_true=50) else None,
    }
    print(f"    計画ID {production_plan_id} の使用部品を作成試行: 部品 {payload['part_code']}")
    response_data = _make_api_request("POST", PARTS_USED_ENDPOINT, data=payload)
    if response_data and response_data.get('id'):
        print(f"    使用部品の作成成功 ID: {response_data['id']} (部品: {response_data.get('part_code')}, 数量: {response_data.get('quantity_used')})")
        return {
            "id": response_data.get('id'),
            "part_code": response_data.get("part_code"),
            "quantity_used": response_data.get("quantity_used"),
            # "used_datetime": used_datetime_obj # PO作成時に使用日の情報が必要な場合
        }
    else:
        print(f"    計画ID {production_plan_id} の使用部品エントリ作成失敗。")
        return None

def create_purchase_order_api(part_code, quantity):
    """使用された部品に基づいて発注（入庫予定）を作成します。"""
    global fake, purchase_order_number_counter
    
    # 発注品の到着予定日は未来の日付
    arrival_delay_days = fake.random_int(min=7, max=45)
    expected_arrival_dt = datetime.now(timezone.utc) + timedelta(days=arrival_delay_days)

    order_number = f"PO-{datetime.now().strftime('%Y%m%d')}-{purchase_order_number_counter:05d}"
    purchase_order_number_counter += 1

    payload = {
        "order_number": order_number,
        "supplier": fake.company(),
        "item": f"{part_code} ({fake.bs()})", # 品目名（説明的）
        "warehouse": fake.random_element(elements=('中央倉庫', '部品倉庫A', '組立ライン横')),
        "quantity": quantity,
        "part_number": part_code, # 品番
        "product_name": f"{part_code} - {fake.word().capitalize()}仕様", # 品名
        "expected_arrival": expected_arrival_dt.isoformat(), # 到着予定日
        "remarks1": fake.sentence(nb_words=5) if fake.boolean(chance_of_getting_true=30) else None,
        "model_type": fake.random_element(elements=('標準型', '特注型', '改良版')),
        "delivery_destination": fake.random_element(elements=(f"{fake.city()}工場", f"{fake.city()}物流センター")),
        # PurchaseOrderモデルの他のオプションフィールドも必要に応じてFakerで生成
    }
    print(f"      発注を作成試行 {order_number} (部品 {part_code}, 数量 {quantity})")
    response_data = _make_api_request("POST", PURCHASE_ORDERS_ENDPOINT, data=payload)
    if response_data and response_data.get('id'):
        print(f"      発注の作成成功 ID: {response_data['id']}")
        return response_data['id']
    else:
        print(f"      部品 {part_code} の発注作成失敗。")
        return None

# --- Main Execution ---
if __name__ == '__main__':
    print("包括的テストデータ作成スクリプトを開始します。")
    print(f"生産計画API: {PRODUCTION_PLANS_ENDPOINT}")
    print(f"使用部品API: {PARTS_USED_ENDPOINT}")
    print(f"発注API: {PURCHASE_ORDERS_ENDPOINT} (このエンドポイントが正しいか確認してください)")
    print("Djangoサーバーが稼働中で、config.iniのAPIトークンが有効であることを確認してください。\n")

    if not API_TOKEN:
        print("重要: API_TOKENが設定されていません。認証付きリクエストを送信できないため、スクリプトを終了します。")
    else:
        num_production_plans_to_create = 1000 # リクエストされた件数
        # num_production_plans_to_create = 2 # テスト用に少なく設定する場合

        successful_plans = 0
        total_parts_used_created = 0
        total_purchase_orders_created = 0

        for i in range(num_production_plans_to_create):
            print(f"\n--- 生産計画 {i+1}/{num_production_plans_to_create} を処理中 ---")
            plan_id = create_production_plan_api()

            if plan_id:
                successful_plans += 1
                num_parts_to_create_for_plan = random.randint(5, 30) # 計画ごとに5～30個の部品
                print(f"  計画ID {plan_id}: {num_parts_to_create_for_plan} 件の使用部品エントリを作成します。")

                for j in range(num_parts_to_create_for_plan):
                    print(f"    - 計画ID {plan_id} の使用部品エントリ {j+1}/{num_parts_to_create_for_plan}")
                    parts_used_info = create_parts_used_api(plan_id)

                    if parts_used_info and parts_used_info.get("part_code") and parts_used_info.get("quantity_used") is not None:
                        total_parts_used_created += 1
                        print(f"      使用部品ID {parts_used_info['id']} に基づいて発注を作成中...")
                        po_id = create_purchase_order_api(
                            part_code=parts_used_info["part_code"],
                            quantity=parts_used_info["quantity_used"]
                        )
                        if po_id:
                            total_purchase_orders_created +=1
                    else:
                        print(f"    計画ID {plan_id} の使用部品作成失敗またはデータ不足のため、発注作成をスキップ。")
            else:
                print(f"  計画 {i+1} の作成失敗のため、使用部品と発注の作成をスキップ。")
        
        print("\n--- スクリプト実行結果 ---")
        print(f"生産計画の作成試行数: {num_production_plans_to_create}")
        print(f"作成成功した生産計画数: {successful_plans}")
        print(f"作成成功した使用部品エントリ数: {total_parts_used_created}")
        print(f"作成成功した発注（入庫予定）数: {total_purchase_orders_created}")
        print("\n包括的テストデータ作成スクリプトが終了しました。")
