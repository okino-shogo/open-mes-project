const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({ headless: false });
  const page = await browser.newPage();
  
  // コンソールログを監視
  page.on('console', msg => {
    console.log('BROWSER:', msg.type(), msg.text());
  });
  
  try {
    // 作業者インターフェースにアクセス
    await page.goto('http://localhost:8050/production/worker-interface-list/');
    await page.waitForTimeout(3000);
    
    // 作業者IDを入力
    await page.fill('#workerId', '5435');
    
    // 工程選択（後加工）
    await page.selectOption('#processSelect', 'post_processing');
    await page.waitForTimeout(2000);
    
    // APIレスポンスを確認
    const apiResponse = await page.evaluate(() => {
      return fetch('/api/production/plans/')
        .then(r => r.json())
        .then(data => data.results ? data.results[0] : null);
    });
    
    console.log('API Response sample:', JSON.stringify(apiResponse, null, 2));
    
    // 予定日カラムの内容を確認
    const scheduleColumn = await page.$$eval('#productionPlansTable tr td:nth-child(8)', 
      cells => cells.map(cell => cell.textContent)
    );
    
    console.log('Schedule column contents:', scheduleColumn);
    
    // デバッグログも確認
    await page.waitForTimeout(1000);
    
  } catch (error) {
    console.error('Error:', error.message);
  } finally {
    await browser.close();
  }
})();