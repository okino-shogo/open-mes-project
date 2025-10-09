/**
 * 生産計画のCSVマッピング設定をPlaywrightで自動設定するスクリプト
 *
 * 実行方法:
 * PLAYWRIGHT_USER=admin PLAYWRIGHT_PASSWORD=admin123 node setup_csv_mappings.js
 */

const { chromium } = require('playwright');

// 画像カラム順序に基づくCSVマッピング設定
const CSV_MAPPINGS = [
  { order: 10, modelField: 'qr_code', customName: 'QRコード', csvHeader: 'QRコード', isActive: true, isUpdateKey: false },
  { order: 20, modelField: 'reception_no', customName: '受付No', csvHeader: '受付No', isActive: true, isUpdateKey: true },
  { order: 30, modelField: 'additional_no', customName: '追加No', csvHeader: '追加No', isActive: true, isUpdateKey: false },
  { order: 40, modelField: 'customer_name', customName: '得意先名', csvHeader: '得意先名', isActive: true, isUpdateKey: false },
  { order: 50, modelField: 'site_name', customName: '現場名', csvHeader: '現場名', isActive: true, isUpdateKey: false },
  { order: 60, modelField: 'additional_content', customName: '追加内容', csvHeader: '追加内容', isActive: true, isUpdateKey: false },
  { order: 70, modelField: 'planned_start_datetime', customName: '製造予定日', csvHeader: '製造予定日', isActive: true, isUpdateKey: false },
  { order: 80, modelField: 'planned_shipment_date', customName: '出荷予定日', csvHeader: '出荷予定日', isActive: true, isUpdateKey: false },
  { order: 90, modelField: 'product_code', customName: '品名', csvHeader: '品名', isActive: true, isUpdateKey: false },
  { order: 100, modelField: 'process', customName: '工程', csvHeader: '工程', isActive: true, isUpdateKey: false },
  { order: 110, modelField: 'planned_quantity', customName: '数量', csvHeader: '数量', isActive: true, isUpdateKey: false },
  { order: 120, modelField: 'slit_scheduled_date', customName: 'スリット予定日', csvHeader: 'スリット予定日', isActive: true, isUpdateKey: false },
  { order: 130, modelField: 'cut_scheduled_date', customName: 'カット予定日', csvHeader: 'カット予定日', isActive: true, isUpdateKey: false },
  { order: 140, modelField: 'molder_scheduled_date', customName: 'モルダー予定日', csvHeader: 'モルダー予定日', isActive: true, isUpdateKey: false },
  { order: 150, modelField: 'vcut_mapping_scheduled_date', customName: 'Vカットマッピング・後加工予定日', csvHeader: 'Vカットマッピング・後加工予定日', isActive: true, isUpdateKey: false },
  { order: 160, modelField: 'packing_scheduled_date', customName: '梱包予定日', csvHeader: '梱包予定日', isActive: true, isUpdateKey: false },
  { order: 170, modelField: 'delivery_date', customName: '納品日', csvHeader: '納品日', isActive: true, isUpdateKey: false },
  { order: 180, modelField: 'veneer_scheduled_date', customName: '化粧板貼予定日', csvHeader: '化粧板貼予定日', isActive: true, isUpdateKey: false },
  { order: 190, modelField: 'cut_veneer_scheduled_date', customName: 'カット化粧板予定日', csvHeader: 'カット化粧板予定日', isActive: true, isUpdateKey: false },
  { order: 200, modelField: 'plan_name', customName: '計画名', csvHeader: '計画名', isActive: false, isUpdateKey: false },
  { order: 210, modelField: 'status', customName: 'ステータス', csvHeader: 'ステータス', isActive: false, isUpdateKey: false },
  { order: 220, modelField: 'remarks', customName: '備考', csvHeader: '備考', isActive: false, isUpdateKey: false },
];

async function setupCSVMappings() {
  const baseURL = process.env.PLAYWRIGHT_BASE_URL || 'http://localhost:8100';
  const username = process.env.PLAYWRIGHT_USER || 'admin';
  const password = process.env.PLAYWRIGHT_PASSWORD || 'admin123';

  console.log('🚀 CSVマッピング設定を開始します...');
  console.log(`   Base URL: ${baseURL}`);
  console.log(`   User: ${username}`);

  const browser = await chromium.launch({ headless: false });
  const context = await browser.newContext();
  const page = await context.newPage();

  try {
    // ログイン
    console.log('\n📝 ログイン中...');
    await page.goto(`${baseURL}/login`);
    await page.fill('input[name="username"]', username);
    await page.fill('input[name="password"]', password);
    await page.click('button[type="submit"]');
    await page.waitForURL('**/top', { timeout: 10000 });
    console.log('   ✓ ログイン成功');

    // CSVマッピング設定ページへ移動
    console.log('\n🔧 CSVマッピング設定ページへ移動...');
    await page.goto(`${baseURL}/system/csv-mappings`);
    await page.waitForLoadState('networkidle');

    // データ種別で「生産計画」を選択
    console.log('   データ種別で「生産計画」を選択...');
    await page.selectOption('select', 'production_plan');
    await page.waitForTimeout(1000); // データ読み込み待機

    // 既存のマッピングをすべてクリア（非アクティブ化）
    console.log('\n🗑️  既存のマッピングを非アクティブ化中...');
    const rows = await page.locator('tbody tr').count();
    for (let i = 0; i < rows; i++) {
      const checkbox = page.locator('tbody tr').nth(i).locator('input[type="checkbox"]').first();
      const isChecked = await checkbox.isChecked();
      if (isChecked) {
        await checkbox.uncheck();
      }
    }

    // 新しいマッピング設定を適用
    console.log('\n✨ 新しいマッピング設定を適用中...');
    for (const mapping of CSV_MAPPINGS) {
      console.log(`   設定: ${mapping.customName} (${mapping.modelField})`);

      // 該当するモデルフィールドの行を探す
      const row = page.locator(`tbody tr:has-text("${mapping.modelField}")`).first();

      if (await row.count() > 0) {
        // 有効チェックボックス
        const activeCheckbox = row.locator('input[type="checkbox"]').first();
        if (mapping.isActive) {
          await activeCheckbox.check();
        } else {
          await activeCheckbox.uncheck();
        }

        // カスタム表示名
        const customNameInput = row.locator('input[type="text"]').nth(0);
        await customNameInput.fill(mapping.customName);

        // CSVヘッダー名
        const csvHeaderInput = row.locator('input[type="text"]').nth(1);
        await csvHeaderInput.fill(mapping.csvHeader);

        // 上書きキー（必要に応じて）
        if (mapping.isUpdateKey) {
          const updateKeyCheckbox = row.locator('input[type="checkbox"]').nth(1);
          await updateKeyCheckbox.check();
        }
      } else {
        console.log(`   ⚠️  警告: ${mapping.modelField} の行が見つかりません`);
      }
    }

    // 保存ボタンをクリック
    console.log('\n💾 設定を保存中...');
    await page.click('button:has-text("この設定で保存")');
    await page.waitForTimeout(2000);

    // 成功メッセージの確認
    const successMessage = await page.locator('.alert-success').count();
    if (successMessage > 0) {
      console.log('   ✓ 保存成功！');
    } else {
      console.log('   ⚠️  保存結果を確認できませんでした');
    }

    // 設定結果のスクリーンショット
    await page.screenshot({ path: 'csv_mappings_result.png', fullPage: true });
    console.log('\n📸 スクリーンショット保存: csv_mappings_result.png');

    console.log('\n✅ CSVマッピング設定完了！');

  } catch (error) {
    console.error('\n❌ エラーが発生しました:', error);
    await page.screenshot({ path: 'csv_mappings_error.png', fullPage: true });
    console.log('   エラー時のスクリーンショット: csv_mappings_error.png');
  } finally {
    await browser.close();
  }
}

setupCSVMappings();
