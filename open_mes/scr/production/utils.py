import csv
import io
from datetime import datetime
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from .models import ProductionPlan, ProcessSchedule

def parse_date_string(date_str):
    """
    日付文字列を解析してdatetimeオブジェクトに変換する
    """
    if not date_str or date_str.strip() == '':
        return None
    
    # 様々な日付形式に対応
    formats = [
        '%Y/%m/%d %H:%M',
        '%Y/%m/%d %H:%M:%S',
        '%Y-%m-%d %H:%M',
        '%Y-%m-%d %H:%M:%S',
        '%m/%d %H:%M',
        '%Y/%m/%d',
        '%Y-%m-%d',
    ]
    
    for fmt in formats:
        try:
            parsed_date = datetime.strptime(date_str.strip(), fmt)
            # 年が指定されていない場合は現在の年を使用
            if fmt.startswith('%m/'):
                parsed_date = parsed_date.replace(year=datetime.now().year)
            return timezone.make_aware(parsed_date)
        except ValueError:
            continue
    
    # 特殊な形式（例：「4/26 16:35 検査完了」）の処理
    if '検査完了' in date_str or '完了' in date_str:
        date_part = date_str.split()[0] + ' ' + date_str.split()[1]
        try:
            parsed_date = datetime.strptime(date_part, '%m/%d %H:%M')
            parsed_date = parsed_date.replace(year=datetime.now().year)
            return timezone.make_aware(parsed_date)
        except ValueError:
            pass
    
    return None

def parse_csv_row(row):
    """
    CSVの1行を解析してProductionPlanモデルに対応するデータに変換する
    """
    data = {
        'qr_code': row.get('QRコード', ''),
        'reception_no': row.get('受付No', ''),
        'additional_no': row.get('追加No', ''),
        'client_name': row.get('得意先名', ''),
        'site_name': row.get('現場名', ''),
        'additional_content': row.get('追加内容', ''),
        'product_name': row.get('品名', ''),
        'process_type': row.get('工程', ''),
        'planned_quantity': int(row.get('数量', 0)) if row.get('数量') else 0,
        'manufacturing_scheduled_date': parse_date_string(row.get('製造予定日', '')),
        'shipping_scheduled_date': parse_date_string(row.get('出荷予定日', '')),
        
        # 納期目標
        'delivery_target_date': parse_date_string(row.get('納期目標日', '')),
        'delivery_target_note': row.get('納期目標備考', ''),
        
        # 予定日
        'slit_scheduled_date': parse_date_string(row.get('スリット予定日', '')),
        'cut_scheduled_date': parse_date_string(row.get('カット予定日', '')),
        'base_material_cut_scheduled_date': parse_date_string(row.get('基材カット予定日', '')),
        'molder_scheduled_date': parse_date_string(row.get('モルダー予定日', '')),
        'v_cut_lapping_scheduled_date': parse_date_string(row.get('Vカットラッピング予定日', '')),
        'post_processing_scheduled_date': parse_date_string(row.get('後加工予定日', '')),
        'packing_scheduled_date': parse_date_string(row.get('梱包予定日', '')),
        'decorative_board_scheduled_date': parse_date_string(row.get('化粧板貼付予定日', '')),
        'decorative_board_cut_scheduled_date': parse_date_string(row.get('化粧板カット予定日', '')),
        
        # 着手時間
        'slit_start_time': parse_date_string(row.get('スリット着手時間', '')),
        'cut_start_time': parse_date_string(row.get('カット着手時間', '')),
        'base_material_cut_start_time': parse_date_string(row.get('基材カット着手時間', '')),
        'molder_start_time': parse_date_string(row.get('モルダー着手時間', '')),
        'v_cut_lapping_start_time': parse_date_string(row.get('Vカットラッピング着手時間', '')),
        'post_processing_start_time': parse_date_string(row.get('後加工着手時間', '')),
        'packing_start_time': parse_date_string(row.get('梱包着手時間', '')),
        'decorative_board_start_time': parse_date_string(row.get('化粧板貼付着手時間', '')),
        'decorative_board_cut_start_time': parse_date_string(row.get('化粧板カット着手時間', '')),
        
        # 完了時間
        'slit_completion_time': parse_date_string(row.get('スリット完了時間', '')),
        'cut_completion_time': parse_date_string(row.get('カット完了時間', '')),
        'base_material_cut_completion_time': parse_date_string(row.get('基材カット完了時間', '')),
        'molder_completion_time': parse_date_string(row.get('モルダー完了時間', '')),
        'v_cut_lapping_completion_time': parse_date_string(row.get('Vカットラッピング完了時間', '')),
        'post_processing_completion_time': parse_date_string(row.get('後加工完了時間', '')),
        'packing_completion_time': parse_date_string(row.get('梱包完了時間', '')),
        'decorative_board_completion_time': parse_date_string(row.get('化粧板貼付完了時間', '')),
        'decorative_board_cut_completion_time': parse_date_string(row.get('化粧板カット完了時間', '')),
        
        # 所要時間（分）
        'slit_duration_minutes': int(row.get('スリット所要時間', 0)) if row.get('スリット所要時間') else None,
        'cut_duration_minutes': int(row.get('カット所要時間', 0)) if row.get('カット所要時間') else None,
        'base_material_cut_duration_minutes': int(row.get('基材カット所要時間', 0)) if row.get('基材カット所要時間') else None,
        'molder_duration_minutes': int(row.get('モルダー所要時間', 0)) if row.get('モルダー所要時間') else None,
        'v_cut_lapping_duration_minutes': int(row.get('Vカットラッピング所要時間', 0)) if row.get('Vカットラッピング所要時間') else None,
        'post_processing_duration_minutes': int(row.get('後加工所要時間', 0)) if row.get('後加工所要時間') else None,
        'packing_duration_minutes': int(row.get('梱包所要時間', 0)) if row.get('梱包所要時間') else None,
        'decorative_board_duration_minutes': int(row.get('化粧板貼付所要時間', 0)) if row.get('化粧板貼付所要時間') else None,
        'decorative_board_cut_duration_minutes': int(row.get('化粧板カット所要時間', 0)) if row.get('化粧板カット所要時間') else None,
        
        # ステータス
        'slit_status': row.get('スリットステータス', '未着手'),
        'cut_status': row.get('カットステータス', '未着手'),
        'base_material_cut_status': row.get('基材カットステータス', '未着手'),
        'molder_status': row.get('モルダーステータス', '未着手'),
        'v_cut_lapping_status': row.get('Vカットラッピングステータス', '未着手'),
        'post_processing_status': row.get('後加工ステータス', '未着手'),
        'packing_status': row.get('梱包ステータス', '未着手'),
        'decorative_board_status': row.get('化粧板貼付ステータス', '未着手'),
        'decorative_board_cut_status': row.get('化粧板カットステータス', '未着手'),
    }
    
    # 基本フィールドの設定
    data['plan_name'] = f"{data['reception_no']}_{data['additional_no']}" if data['reception_no'] and data['additional_no'] else 'CSV Import'
    data['product_code'] = data['product_name'] or 'UNKNOWN'
    data['planned_start_datetime'] = data['manufacturing_scheduled_date'] or timezone.now()
    data['planned_end_datetime'] = data['shipping_scheduled_date'] or (data['manufacturing_scheduled_date'] or timezone.now())
    
    return data

def import_csv_data(csv_file):
    """
    CSVファイルからデータを読み込み、ProductionPlanとProcessScheduleを作成する
    """
    results = {
        'success': 0,
        'errors': [],
        'created_plans': [],
        'created_schedules': []
    }
    
    try:
        # CSVファイルを読み込む
        if hasattr(csv_file, 'read'):
            csv_content = csv_file.read()
            if isinstance(csv_content, bytes):
                csv_content = csv_content.decode('utf-8')
        else:
            csv_content = csv_file
            
        csv_reader = csv.DictReader(io.StringIO(csv_content))
        
        for row_num, row in enumerate(csv_reader, start=2):  # ヘッダーを除くため2から開始
            try:
                # CSVデータを解析
                parsed_data = parse_csv_row(row)
                
                # ProductionPlanを作成
                production_plan = ProductionPlan.objects.create(**parsed_data)
                results['created_plans'].append(production_plan)
                
                # 工程スケジュールを作成
                process_schedules = create_process_schedules(production_plan, parsed_data)
                results['created_schedules'].extend(process_schedules)
                
                results['success'] += 1
                
            except Exception as e:
                results['errors'].append({
                    'row': row_num,
                    'error': str(e),
                    'data': row
                })
                
    except Exception as e:
        results['errors'].append({
            'row': 'file',
            'error': f'CSVファイルの読み込みエラー: {str(e)}',
            'data': None
        })
    
    return results

def create_process_schedules(production_plan, data):
    """
    ProductionPlanから工程スケジュールを作成する
    """
    process_schedules = []
    
    # 工程と対応する日付フィールドのマッピング
    process_mapping = {
        'スリット': 'slit_scheduled_date',
        'カット': 'cut_scheduled_date',
        'モルダー': 'molder_scheduled_date',
        'Vカットラッピング': 'v_cut_lapping_scheduled_date',
        '後加工': 'post_processing_scheduled_date',
        '梱包': 'packing_scheduled_date',
        '化粧板貼付': 'decorative_board_scheduled_date',
        'カット化粧板貼付': 'cut_decorative_board_scheduled_date',
    }
    
    for process_name, date_field in process_mapping.items():
        scheduled_date = data.get(date_field)
        if scheduled_date:
            process_schedule = ProcessSchedule.objects.create(
                production_plan=production_plan,
                process_name=process_name,
                scheduled_start_date=scheduled_date.date(),
                scheduled_end_date=scheduled_date.date(),
                status='未着手'
            )
            process_schedules.append(process_schedule)
    
    return process_schedules

def get_gantt_chart_data(start_date=None, end_date=None):
    """
    ガントチャート表示用のデータを取得する
    """
    # 基本的な生産計画データを取得
    production_plans = ProductionPlan.objects.all()
    
    if start_date:
        production_plans = production_plans.filter(
            planned_start_datetime__gte=start_date
        )
    
    if end_date:
        production_plans = production_plans.filter(
            planned_end_datetime__lte=end_date
        )
    
    # 工程スケジュールデータを取得
    process_schedules = ProcessSchedule.objects.filter(
        production_plan__in=production_plans
    )
    
    # 日付範囲を決定
    if not start_date and not end_date:
        dates = []
        for plan in production_plans:
            if plan.planned_start_datetime:
                dates.append(plan.planned_start_datetime.date())
            if plan.planned_end_datetime:
                dates.append(plan.planned_end_datetime.date())
        
        if dates:
            start_date = min(dates)
            end_date = max(dates)
        else:
            start_date = timezone.now().date()
            end_date = timezone.now().date()
    
    return {
        'production_plans': production_plans,
        'process_schedules': process_schedules,
        'date_range': {
            'start': start_date,
            'end': end_date
        }
    }