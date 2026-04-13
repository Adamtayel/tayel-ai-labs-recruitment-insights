import asyncio
import os
from playwright.async_api import async_playwright
from openai import OpenAI
from dotenv import load_dotenv
from fpdf import FPDF

# 1. تحميل الإعدادات
load_dotenv()

client = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"), 
    base_url="https://api.deepseek.com"
)

# 2. وظيفة إنشاء الـ PDF
def create_pdf(text, lang):
    pdf = FPDF()
    pdf.add_page()
    
    try:
        # يفضل وجود خط Amiri-Regular.ttf لدعم العربي
        pdf.add_font('Amiri', '', 'Amiri-Regular.ttf')
        pdf.set_font('Amiri', size=12)
    except:
        pdf.set_font("Helvetica", size=12)
        text = text.encode('ascii', 'ignore').decode('ascii')
    
    clean_text = text.replace("#", "").replace("*", "")
    pdf.multi_cell(0, 10, text=clean_text)
    
    filename = "Tayel_AI_Report.pdf"
    pdf.output(filename)
    return filename

# 3. الوظيفة الأساسية للسحب والتحليل (النسخة الاحترافية)
async def run_agent(profile_url, lang):
    target_url = profile_url.strip()
    if target_url.startswith('ttps://'): target_url = 'h' + target_url
    if not target_url.startswith('http'): target_url = 'https://' + target_url

    endpoint = os.getenv("BRIGHT_DATA_ENDPOINT")
    
    prompts = {
        '1': { # Arabic
            'system': "أنت خبير تقني (CTO). حلل نص بروفايل لينكد إن المرفق واستخرج تقرير دقيق بالعربية. ركز على المهارات والخبرة والمشاريع.",
            'loading': "🚀 جاري الاتصال بسيرفرات Bright Data...",
            'ai': "🧠 جاري تحليل البيانات بواسطة DeepSeek..."
        },
        '2': { # English
            'system': "You are a Technical Expert (CTO). Analyze the provided LinkedIn profile text and provide a detailed professional report in English. Focus on skills and experience.",
            'loading': "🚀 Connecting to Bright Data servers...",
            'ai': "🧠 Analyzing data with DeepSeek..."
        }
    }
    
    config = prompts.get(lang, prompts['2'])
    print(config['loading'])
    
    async with async_playwright() as pw:
        try:
            # الاتصال بـ Bright Data مع وقت انتظار كافٍ
            browser = await pw.chromium.connect_over_cdp(endpoint, timeout=120000)
            context = await browser.new_context(user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36")
            page = await context.new_page()
            
            attempts = 3
            success = False
            for i in range(attempts):
                try:
                    print(f"Attempt {i+1}: Navigating to {target_url}")
                    await page.goto(target_url, timeout=120000, wait_until="domcontentloaded")
                    
                    # --- حركة سحرية: Scroll عشان الـ Lazy Loading ---
                    await page.mouse.wheel(0, 1000) 
                    await page.wait_for_timeout(4000) # استنى الداتا تظهر
                    
                    success = True
                    break 
                except Exception as e:
                    if i < attempts - 1:
                        print("⚠️ Server busy, retrying in 5 seconds...")
                        await asyncio.sleep(5)
                        continue
                    raise e

            # سحب النص بذكاء (حتى لو لينكد إن حاول يغير الـ Tags)
            raw_text = await page.evaluate("""() => {
                // محاولة استهداف الجزء الرئيسي أولاً
                const main = document.querySelector('main') || document.querySelector('#main');
                if (main && main.innerText.length > 500) return main.innerText;
                
                // لو فشل، نسحب كل حاجة ما عدا الأكواد الزيادة
                const scripts = document.querySelectorAll('script, style, nav, footer, header');
                scripts.forEach(s => s.remove());
                return document.body.innerText;
            }""")
            
            await browser.close()

            # تنظيف وحفظ النص للـ Debug
            clean_raw_text = " ".join(raw_text.split())
            with open("last_profile_raw.txt", "w", encoding="utf-8") as f:
                f.write(clean_raw_text)
            
            # التحقق من جودة الداتا
            if len(clean_raw_text) < 400:
                if "authwall" in clean_raw_text.lower() or "sign in" in clean_raw_text.lower():
                    return "❌ Error: LinkedIn requested login (Authwall). Please try again later."
                return "❌ Error: Could not extract enough data. Profile might be private or empty."

            print(config['ai'])
            
            # التحليل بواسطة DeepSeek
            response = client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": config['system']},
                    {"role": "user", "content": f"Analyze this LinkedIn profile text:\n\n{clean_raw_text[:12000]}"}
                ]
            )
            
            return response.choices[0].message.content

        except Exception as e:
            return f"❌ Error: {str(e)}"

# 4. تشغيل البرنامج
async def main():
    print("--- 🤖 Tayel AI Labs v1.3 ---")
    lang_choice = input("Select Language (1 Arabic, 2 English): ")
    url = input("Enter LinkedIn URL: ")
    
    final_report = await run_agent(url, lang_choice)
    print("\n" + "="*50 + "\n" + final_report + "\n" + "="*50)
    
    if "Error" not in final_report:
        create_pdf(final_report, lang_choice)
        print("✅ Success!")

if __name__ == "__main__":
    asyncio.run(main())