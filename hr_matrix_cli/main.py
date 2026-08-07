import asyncio
from scrapers import parser_sites, parser_telegram
from nlp import llm_dataset
from analytics import skill_matrix, clustering_tsi
from hr_matrix_cli import config


async def run_scrapers():
    print("🚀 ЭТАП 1: Сбор сырых данных...")
    # Запускаем парсеры параллельно для ускорения
    await asyncio.gather(
        parser_sites.scrape_all_sites(),
        parser_telegram.scrape_all_channels()
    )
    print("✅ Сбор данных завершен.\n")


def run_nlp_pipeline():
    print("🧠 ЭТАП 2: Подготовка датасета и разметка через LLM (Saiga)...")
    llm_dataset.process_and_label_data()
    print("✅ Разметка завершена.\n")


def run_analytics():
    print("📊 ЭТАП 3: Аналитика и расчет грейдов...")

    print("  -> Составление матрицы компетенций...")
    skill_matrix.build_matrix()

    print("  -> Расчет TSI и кластеризация...")
    thresholds = clustering_tsi.calculate_and_cluster()

    print("\n🎉 ВСЕ ГОТОВО! РЕЗУЛЬТАТЫ:")
    print(f"Граница Junior -> Middle: {thresholds['junior_middle']:.2f}")
    print(f"Граница Middle -> Senior: {thresholds['middle_senior']:.2f}")


async def main():
    print("=== ЗАПУСК ПАЙПЛАЙНА HR MATRIX ===\n")

    await run_scrapers()
    run_nlp_pipeline()
    run_analytics()


if __name__ == "__main__":
    asyncio.run(main())