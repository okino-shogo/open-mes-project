#!/usr/bin/env python3
"""
CSVヘッダー自動追加のテストスクリプト
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

# テストCSVファイル（ヘッダーなし）
csv_file = '/Users/okinotakumiware/Downloads/無題のスプレッドシート - 無題のスプレッドシート - WQ枠製造工程 (1) (1).csv'

with open(csv_file, 'r', encoding='utf-8-sig') as f:
    content = f.read()

# ヘッダー行の存在確認と自動追加
lines = content.splitlines()
if lines:
    first_line = lines[0]
    print(f"1行目の最初の30文字: {first_line[:30]}")
    print(f"'QRコード'で始まるか: {first_line.startswith('QRコード')}")

    # 最初の行がヘッダーかどうかをチェック（QRコードで始まるか）
    if not first_line.startswith('QRコード'):
        print("\n✅ ヘッダーなしと判定 - 自動追加します")
        # ヘッダーがない場合は、マッピング設定から自動生成
        header_line = ','.join(expected_headers)
        content = header_line + '\n' + content
        total_rows = len(lines)  # ヘッダーを追加したので全行がデータ
        print(f"データ行数: {total_rows}")
    else:
        print("\n✅ ヘッダーありと判定")
        total_rows = len(lines) - 1  # ヘッダーを除く
        print(f"データ行数: {total_rows}")

# DictReaderでテスト
io_string = io.StringIO(content)
reader = csv.DictReader(io_string)

print(f"\nヘッダー: {reader.fieldnames}")
print(f"\n最初の3行:")
for i, row in enumerate(reader, start=1):
    if i > 3:
        break
    print(f"\n行{i}:")
    print(f"  QRコード: {row.get('QRコード', 'N/A')}")
    print(f"  受付No: {row.get('受付No', 'N/A')}")
    print(f"  得意先名: {row.get('得意先名', 'N/A')}")
    print(f"  数量: {row.get('数量', 'N/A')}")
