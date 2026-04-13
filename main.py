import asyncio
import os
from playwright.async_api import async_playwright
from openai import OpenAI
from dotenv import load_dotenv

# تحميل الإعدادات من ملف .env
load_dotenv()

# إعداد DeepSeek
client = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"), 
    base_url="https://api.deepseek.com"
)

async def get_programmer_report(profile_url):
    endpoint = os.getenv("BRIGHT_DATA_ENDPOINT")
    
    print(f"🚀 جاري فتح المتصفح والدخول على: {profile_url}...")
    
    async with async_playwright() as pw:
        browser = await pw.chromium.connect_over_cdp(endpoint)
        # بنفتح السياق (Context) بـ User Agent حقيقي عشان الأمان
        context = await browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        page = await context.new_page()
        
        try:
            # زودنا الـ Timeout لـ 90 ثانية وبنستنى الـ DOM بس
            await page.goto(profile_url, timeout=90000, wait_until="domcontentloaded")
            
            # بنستنى 5 ثواني إضافية عشان نضمن إن الـ JavaScript اشتغل
            await page.wait_for_timeout(5000) 
            
            # سحب كل النصوص
            raw_text = await page.evaluate("() => document.body.innerText")
            
        except Exception as e:
            print(f"❌ حصلت مشكلة أثناء السحب: {e}")
            raw_text = None
        finally:
            await browser.close()

        if not raw_text or len(raw_text) < 100:
            return "تعذر سحب بيانات كافية من البروفايل، تأكد من أن الرابط صحيح أو عام (Public)."

        print("🧠 جاري تحليل البيانات باستخدام DeepSeek...")
        
        # إرسال البيانات للـ AI
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": "أنت خبير تقني (CTO). حلل بروفايل لينكد إن واستخرج تقرير دقيق باللغة العربية."},
                {"role": "user", "content": raw_text}
            ]
        )
        
        return response.choices[0].message.content

if __name__ == "__main__":
    target_url = "https://www.linkedin.com/in/adam-tayel-54a2bb330/"
    
    report = asyncio.run(get_programmer_report(target_url))
    
    print("\n" + "="*50)
    print("📋 تقرير الـ AI Agent النهائي:")
    print("="*50)
    print(report)