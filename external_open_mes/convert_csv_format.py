#!/usr/bin/env python3
"""
既存のCSVデータを新しいフォーマットに変換するスクリプト

使用方法:
    python convert_csv_format.py input.csv output.csv
"""
import csv
import sys
from datetime import datetime

def parse_datetime(date_str):
    """日時文字列をYYYY-MM-DD形式に変換"""
    if not date_str or date_str.strip() == '':
        return ''
    try:
        # "2025/05/19 0:00:00" -> "2025-05-19"
        dt = datetime.strptime(date_str.strip(), '%Y/%m/%d %H:%M:%S')
        return dt.strftime('%Y-%m-%d')
    except:
        return ''

def extract_qr_code(combined_no):
    """受付No-追加No-NoからQRコードを生成"""
    if not combined_no or combined_no.strip() == '':
        return ''
    return f'QR-{combined_no}'

def convert_csv(input_file, output_file):
    """CSVファイルを新フォーマットに変換"""

    # 新しいヘッダー
    new_headers = [
        'QRコード', '受付No', '追加No', '得意先名', '現場名', '追加内容',
        '製造予定日', '出荷予定日', '品名', '工程', '数量',
        'スリット予定日', 'カット予定日', 'モルダー予定日',
        'Vカットラッピング予定日', '後加工予定日', '梱包予定日', '納品日',
        '化粧板貼予定日', 'カット化粧板予定日'
    ]

    with open(input_file, 'r', encoding='utf-8') as infile, \
         open(output_file, 'w', encoding='utf-8-sig', newline='') as outfile:

        reader = csv.reader(infile)
        writer = csv.writer(outfile)

        # 新しいヘッダーを書き込み
        writer.writerow(new_headers)

        # ヘッダー行をスキップ（入力ファイルにヘッダーがある場合）
        next(reader, None)

        for row in reader:
            if len(row) < 20:
                print(f'警告: 列数が不足しています（{len(row)}列）: {row}')
                continue

            # 新しい行を構築（元データの列番号は0始まり）
            new_row = [
                extract_qr_code(row[0]),           # QRコード（受付No-追加No-Noから生成）
                row[1],                            # 受付No
                row[2],                            # 追加No
                row[3],                            # 得意先名
                row[4],                            # 現場名
                row[5],                            # 追加内容
                parse_datetime(row[6]),            # 製造予定日
                parse_datetime(row[7]),            # 出荷予定日
                row[8],                            # 品名
                row[9],                            # 工程
                row[10],                           # 数量
                parse_datetime(row[11]) if len(row) > 11 else '',  # スリット予定日
                parse_datetime(row[12]) if len(row) > 12 else '',  # カット予定日
                parse_datetime(row[13]) if len(row) > 13 else '',  # モルダー予定日
                parse_datetime(row[14]) if len(row) > 14 else '',  # Vカットラッピング予定日
                parse_datetime(row[15]) if len(row) > 15 else '',  # 後加工予定日
                parse_datetime(row[16]) if len(row) > 16 else '',  # 梱包予定日
                parse_datetime(row[17]) if len(row) > 17 else '',  # 納品日
                parse_datetime(row[18]) if len(row) > 18 else '',  # 化粧板貼予定日
                parse_datetime(row[19]) if len(row) > 19 else '',  # カット化粧板予定日
            ]

            writer.writerow(new_row)

        print(f'✓ 変換完了: {output_file}')

if __name__ == '__main__':
    if len(sys.argv) != 3:
        print('使用方法: python convert_csv_format.py input.csv output.csv')
        sys.exit(1)

    convert_csv(sys.argv[1], sys.argv[2])
