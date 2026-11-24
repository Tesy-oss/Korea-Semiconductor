#!/usr/bin/env python3
import asyncio
from playwright.async_api import async_playwright
import sys

async def capture_screenshots():
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            executable_path="/usr/local/bin/google-chrome",
            args=[
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
                '--disable-gpu'
            ]
        )
        page = await browser.new_page(viewport={'width': 1920, 'height': 1080})
        
        try:
            # Navigate to the dashboard
            print("Navigating to dashboard...")
            await page.goto('http://localhost:8000/', wait_until='networkidle', timeout=30000)
            
            # Wait for content to load
            print("Waiting for content...")
            await page.wait_for_selector('#stock-cards', timeout=15000)
            await asyncio.sleep(3)
            
            # Screenshot 1: Overview section
            print("Capturing overview...")
            await page.screenshot(path='/opt/cursor/artifacts/dashboard-overview.png', full_page=False)
            
            # Full page screenshot
            print("Capturing full page...")
            await page.screenshot(path='/opt/cursor/artifacts/dashboard-full.png', full_page=True)
            
            print("Screenshots captured successfully!")
            
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            raise
        finally:
            await browser.close()

if __name__ == '__main__':
    asyncio.run(capture_screenshots())
