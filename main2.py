import asyncio
import os
from playwright.async_api import async_playwright
from openai import OpenAI
from dotenv import load_dotenv
from fpdf import FPDF

# Load environment variables
load_dotenv()

client = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com"
)

# Create PDF report
def create_pdf(text, lang):
    pdf = FPDF()
    pdf.add_page()

    try:
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


# Main scraping and analysis function
async def run_agent(profile_url, lang):
    target_url = profile_url.strip()
    if target_url.startswith('ttps://'):
        target_url = 'h' + target_url
    if not target_url.startswith('http'):
        target_url = 'https://' + target_url

    endpoint = os.getenv("BRIGHT_DATA_ENDPOINT")

    prompts = {
        '1': {
            'system': "You are a Technical Expert (CTO). Analyze the LinkedIn profile text and extract a detailed report in Arabic focusing on skills and experience.",
            'loading': "Connecting to Bright Data servers...",
            'ai': "Analyzing data using DeepSeek..."
        },
        '2': {
            'system': "You are a Technical Expert (CTO). Analyze the LinkedIn profile text and extract a detailed professional report in English focusing on skills and experience.",
            'loading': "Connecting to Bright Data servers...",
            'ai': "Analyzing data using DeepSeek..."
        }
    }

    config = prompts.get(lang, prompts['2'])
    print(config['loading'])

    async with async_playwright() as pw:
        try:
            browser = await pw.chromium.connect_over_cdp(endpoint, timeout=120000)
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
            )
            page = await context.new_page()

            attempts = 3
            for i in range(attempts):
                try:
                    print(f"Attempt {i+1}: Navigating to {target_url}")
                    await page.goto(target_url, timeout=120000, wait_until="domcontentloaded")

                    await page.mouse.wheel(0, 1000)
                    await page.wait_for_timeout(4000)
                    break
                except Exception as e:
                    if i < attempts - 1:
                        print("Server busy, retrying...")
                        await asyncio.sleep(5)
                        continue
                    raise e

            raw_text = await page.evaluate("""
            () => {
                const main = document.querySelector('main') || document.querySelector('#main');
                if (main && main.innerText.length > 500) return main.innerText;

                const scripts = document.querySelectorAll('script, style, nav, footer, header');
                scripts.forEach(s => s.remove());
                return document.body.innerText;
            }
            """)

            await browser.close()

            clean_raw_text = " ".join(raw_text.split())

            with open("last_profile_raw.txt", "w", encoding="utf-8") as f:
                f.write(clean_raw_text)

            if len(clean_raw_text) < 400:
                if "authwall" in clean_raw_text.lower() or "sign in" in clean_raw_text.lower():
                    return "Error: LinkedIn auth wall detected."
                return "Error: Not enough data extracted."

            print(config['ai'])

            response = client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": config['system']},
                    {"role": "user", "content": clean_raw_text[:12000]}
                ]
            )

            return response.choices[0].message.content

        except Exception as e:
            return f"Error: {str(e)}"


# Entry point
async def main():
    print("Tayel AI Labs v1.3")

    lang_choice = input("Select Language (1 Arabic, 2 English): ")
    url = input("Enter LinkedIn URL: ")

    final_report = await run_agent(url, lang_choice)

    print("=" * 50)
    print(final_report)
    print("=" * 50)

    if "Error" not in final_report:
        create_pdf(final_report, lang_choice)
        print("Success")


if __name__ == "__main__":
    asyncio.run(main())
