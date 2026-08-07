import asyncio
import re
import os
import pandas as pd
from playwright.async_api import async_playwright
from hr_matrix_cli import config

def is_target_vacancy(title):
    """Строгий фильтр по C#[cite: 13]"""
    title_lower = title.lower()
    has_target = re.search(r'c#|\.net|dotnet', title_lower)
    has_cpp = 'c++' in title_lower or 'cpp' in title_lower
    return has_target and not has_cpp


def get_grade(text):
    """Попытка вытащить грейд из заголовка[cite: 13]"""
    text = text.lower()
    if re.search(r'\b(lead|principal|тимлид|лид|architect|архитектор)\b', text): return 'Lead'
    if re.search(r'\b(senior|сеньор|сеньер|старший)\b', text): return 'Senior'
    if re.search(r'\b(middle|мидл|средний)\b', text): return 'Middle'
    if re.search(r'\b(junior|джуниор|джун|стажер|intern)\b', text): return 'Junior'
    return 'Не указан'


async def parse_remote_job(context, query):
    """Сбор с remote-job.ru[cite: 12]"""
    print("--- Парсинг Remote-Job ---[cite: 12]")
    page = await context.new_page()
    all_links = []

    # 1. Сбор ссылок
    for page_num in range(1, config.PAGES_TO_SCAN + 1):
        url = f"https://remote-job.ru/search?search%5Bquery%5D={query.replace(' ', '%20')}&page={page_num}"
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=30000)
            cards = await page.query_selector_all(".vacancy_item")  # [cite: 12]
            if not cards: break
            for card in cards:
                link_el = await card.query_selector("a")
                if link_el:
                    href = await link_el.get_attribute("href")
                    if href: all_links.append("https://remote-job.ru" + href)
        except Exception as e:
            print(f"Ошибка сбора ссылок Remote-Job: {e}")
            break

    # 2. Сбор данных
    all_links = list(set(all_links))
    final_data = []
    for link in all_links:
        try:
            await page.goto(link, wait_until="domcontentloaded", timeout=30000)
            title = await page.inner_text("h1")  # [cite: 12]
            title = title.replace("(удаленная работа)", "").strip()

            if not is_target_vacancy(title): continue

            salary = "Не указана"
            info_blocks = await page.query_selector_all(".panel-heading .col-md-4")  # [cite: 12]
            for block in info_blocks:
                text = await block.inner_text()
                if "зарплаты" in text.lower():
                    salary = text.split(":")[-1].strip()  # [cite: 12]

            desc_el = await page.query_selector(".panel-body .row.p-y-3")  # [cite: 12]
            if not desc_el:
                desc_el = await page.query_selector(".panel-body")
            description = await desc_el.inner_text() if desc_el else ""

            if "Посмотрите похожие вакансии" in description:
                description = description.split("Посмотрите похожие вакансии")[0]  # [cite: 12]

            final_data.append({
                'title': title,
                'experience': get_grade(title),
                'description': description.strip(),
                'url': link,
                'source': 'remote_job'
            })
        except Exception:
            continue

    await page.close()
    return final_data


async def parse_habr_career(context, query):
    """Сбор с Habr Career[cite: 13]"""
    print("--- Парсинг Habr Career ---[cite: 13]")
    page = await context.new_page()
    all_vacancies = []

    for p in range(1, config.PAGES_TO_SCAN + 1):
        url = f"https://career.habr.com/vacancies?page={p}&q={query.replace(' ', '+')}&type=all"  # [cite: 13]
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=30000)
            links_loc = await page.locator('.vacancy-card__title-link').all()  # [cite: 13]
            for loc in links_loc:
                title = await loc.inner_text()
                href = await loc.get_attribute('href')
                if href and is_target_vacancy(title):
                    full_url = f"https://career.habr.com{href}"  # [cite: 13]

                    # Проваливаемся внутрь вакансии[cite: 13]
                    inner_page = await context.new_page()
                    await inner_page.goto(full_url)
                    desc = await inner_page.locator('.vacancy-description__text').inner_text()  # [cite: 13]

                    all_vacancies.append({
                        'title': title,
                        'experience': get_grade(title),
                        'description': desc.replace('\n', ' ').strip(),
                        'url': full_url,
                        'source': 'habr_career'
                    })
                    await inner_page.close()
                    await asyncio.sleep(1)
        except Exception as e:
            print(f"Ошибка Habr: {e}")
            break

    await page.close()
    return all_vacancies


async def scrape_all_sites():
    async with async_playwright() as p:
        # headless=True для работы в фоне, но если сайты будут блокировать, можно поставить False[cite: 13]
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},  # [cite: 13]
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            # [cite: 13]
        )

        # Скрываем флаг webdriver[cite: 13]
        await context.add_init_script(
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")  # [cite: 13]

        all_data = []
        all_data.extend(await parse_habr_career(context, config.SEARCH_QUERY))
        all_data.extend(await parse_remote_job(context, "C%23"))

        if all_data:
            df = pd.DataFrame(all_data)
            filename = os.path.join(config.RAW_DATA_DIR, "sites_raw.csv")
            df.to_csv(filename, index=False, sep=';', encoding='utf-8-sig')
            print(f"\n[УСПЕХ] Собрано вакансий с сайтов: {len(df)}")
        else:
            print("\nДанные с сайтов не найдены.")

        await browser.close()