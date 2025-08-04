import asyncio
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig
from bs4 import BeautifulSoup
from config import settings
from data_ingestion.loader import store_in_lancedb

async def extract_and_store_faculty_data():
    browser_cfg = BrowserConfig(headless=True)
    run_cfg = CrawlerRunConfig()
    all_data = []

    async with AsyncWebCrawler(config=browser_cfg) as crawler:
        for dept in settings.DEPARTMENTS:
            dept_clean = dept.replace("-", " ").replace("(AI&ML)", "AI & ML")
            for suffix in settings.PAGE_SUFFIXES:
                url = f"{settings.FACULTY_BASE_URL}/{dept}{suffix}"
                result = await crawler.arun(url=url, config=run_cfg)
                if not result.success:
                    print(f"❌ Crawl failed: {url}")
                    continue

                soup = BeautifulSoup(result.html, 'html.parser')
                cards = soup.select('div.upcoming-events.media.maxwidth400.bg-light.mb-20')
                if not cards:
                    break

                for div in cards:
                    name = div.select_one('h4.name')
                    desig = div.select_one('h5.occupation')
                    qual = div.select_one('h5.qualification')
                    add = div.select_one('h5.additional')
                    img = div.select_one('img')

                    phone = email = ''
                    if add:
                        for span in add.find_all('span'):
                            text = span.get_text(strip=True)
                            html = span.decode()
                            if 'fa-phone' in html:
                                phone = text
                            if 'fa-envelope-o' in html:
                                email = text

                    all_data.append([
                        name.get_text(strip=True) if name else '',
                        desig.get_text(strip=True) if desig else '',
                        qual.get_text(strip=True) if qual else '',
                        phone,
                        email,
                        img['src'] if img and img.has_attr('src') else '',
                        dept_clean
                    ])

    if all_data:
        store_in_lancedb(all_data)

if __name__ == '__main__':
    asyncio.run(extract_and_store_faculty_data())
