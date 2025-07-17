#!/usr/bin/env python3
Vercelサイトのテストスクリプト
Playwrightを使用してVercelデプロイメントの動作確認を行う


import asyncio
from playwright.async_api import async_playwright

async def test_vercel_site():
   Vercelサイトの動作確認    # テスト対象URL
    urls =      https://open-ibyok1gm-okisho162628rojects.vercel.app,      https://openmes.vercel.app,      https://open-ibyok1gm-okisho162628rojects.vercel.app/test/",
    ]
    
    async with async_playwright() as p:
        # Chromeブラウザを起動
        browser = await p.chromium.launch(headless=false, slow_mo=100      page = await browser.new_page()
        
        print(🔍 Vercelサイトの動作確認を開始します...")
        
        for i, url in enumerate(urls, 1):
            print(f"\n📋 テスト {i}: {url}")
            
            try:
                # ページにアクセス
                response = await page.goto(url, wait_until='networkidle, timeout=30000)
                
                if response:
                    print(f"✅ ステータスコード: {response.status}")
                    
                    # ページタイトルを取得
                    title = await page.title()
                    print(f"📄 ページタイトル: {title}")
                    
                    # スクリーンショットを保存
                    screenshot_path = f"vercel_test_{i}.png"
                    await page.screenshot(path=screenshot_path, full_page=True)
                    print(f📸 スクリーンショット保存: {screenshot_path}")
                    
                    # ページの内容を確認
                    content = await page.content()
                    if Vercel Django App is working!" in content:
                        print("✅ テストエンドポイントが正常に動作しています")
                    elif41ent orUnauthorized" in content:
                        print("⚠️  デプロイメント保護が有効になっています")
                    elif "500ntent or "Internal Server Error" in content:
                        print(❌サーバーエラーが発生しています")
                    else:
                        print(✅ページが正常に読み込まれました")
                        
                else:
                    print(❌ページの読み込みに失敗しました")
                    
            except Exception as e:
                print(f"❌ エラー: {e}")
                
            # 次のテストの前に少し待機
            await asyncio.sleep(2)
        
        # ブラウザを閉じる
        await browser.close()
        
        print(n🎉 テスト完了！)async def main():
 メイン関数""try:
        await test_vercel_site()
    except KeyboardInterrupt:
        print("\n⏹️  テストを中断しました")
    except Exception as e:
        print(f"❌ 予期しないエラー: {e})if __name__ == __main__:
    asyncio.run(main())
