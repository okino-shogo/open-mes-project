#!/usr/bin/env python3
"""
CSVインポートのデバッグスクリプト - 実際のtasks.pyロジックをシミュレート
"""
import csv
import io

# 期待されるヘッダー（CsvColumnMappingから）
expected_headers = [
    'QRコード', '受付No', '追加No', '得意先名', '現場名', '追加内容',
    '製造予定日', '出荷予定日', '品名', '工程', '数量',
    'スリット予定日', 'カット予定日', 'モルダー予定日',
    'Vカットラッピング予定日', '後加工予定日', '梱包予定日', '納品日',
    '化粧板貼予定日', 'カット化粧板予定日'
]

# ヘッダー→モデルフィールドマッピング
header_to_model_map = {
    'QRコード': 'qr_code',
    '受付No': 'reception_no',
    '追加No': 'additional_no',
    '得意先名': 'customer_name',
    # ... 他のフィールド
}

update_keys_model = ['qr_code']

# テストCSVファイル
csv_file = '/Users/okinotakumiware/Downloads/無題のスプレッドシート - 無題のスプレッドシート - WQ枠製造工程 (1) (1).csv'

with open(csv_file, 'r', encoding='utf-8-sig') as f:
    content = f.read()

print("=== ヘッダー検出ロジックのテスト ===\n")

# ヘッダー行の存在確認と自動追加（tasks.pyと同じロジック）
lines = content.splitlines()
if lines:
    first_line = lines[0]
    print(f"1行目の最初の部分: {first_line[:50]}")
    print(f"'QRコード'で始まるか: {first_line.startswith('QRコード')}")

    # 最初の行がヘッダーかどうかをチェック（QRコードで始まるか）
    if not first_line.startswith('QRコード'):
        print("\n✅ ヘッダーなしと判定 - 自動追加")
        # ヘッダーがない場合は、マッピング設定から自動生成
        header_line = ','.join(expected_headers)
        content = header_line + '\n' + content
        total_rows = len(lines)
        print(f"追加したヘッダー行: {header_line[:80]}...")
    else:
        print("\n❌ ヘッダーありと判定")
        total_rows = len(lines) - 1

print(f"\nデータ行数: {total_rows}")

# DictReaderでパース
io_string = io.StringIO(content)
reader = csv.DictReader(io_string)

print(f"\n=== DictReaderのヘッダー ===")
print(f"検出されたフィールド: {reader.fieldnames[:5]}...")

print(f"\n=== 最初の3行のqr_code値 ===")
for i, row in enumerate(reader, start=1):
    if i > 3:
        break

    # update_kwarg構築ロジックをシミュレート
    model_data = {}
    for csv_header in expected_headers[:5]:  # 最初の5フィールドだけテスト
        value = row.get(csv_header, '').strip()
        model_data[header_to_model_map.get(csv_header, csv_header)] = value if value else None

    # 上書きキーの抽出
    update_kwargs = {key: model_data.pop(key, None) for key in update_keys_model}

    print(f"\n行{i}:")
    print(f"  row['QRコード']: {row.get('QRコード', 'KEY_NOT_FOUND')}")
    print(f"  update_kwargs: {update_kwargs}")
    print(f"  len(update_kwargs): {len(update_kwargs)}")
    print(f"  len(update_keys_model): {len(update_keys_model)}")

    if len(update_kwargs) != len(update_keys_model):
        print(f"  ❌ エラー: 上書きキー (qr_code) の値が空、または見つかりません。")
    elif update_kwargs.get('qr_code') is None:
        print(f"  ❌ エラー: qr_codeがNone")
    else:
        print(f"  ✅ OK")
