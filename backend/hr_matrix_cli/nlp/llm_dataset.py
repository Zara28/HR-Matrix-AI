import os
import re
import json
import pandas as pd
import ollama
from hr_matrix_cli import config


def is_csharp_vacancy(text):
    """Фильтрация: оставляем только вакансии для C# / .NET"""
    text_lower = str(text).lower()
    if re.search(r'c#|\.net|aspnet|dotnet|c-sharp', text_lower):
        # Исключаем, если это явно другая специализация
        if any(lang in text_lower for lang in
               ['java developer', 'python developer', 'php developer', 'golang developer']):
            if 'c#' not in text_lower:
                return False
        return True
    return False


def clean_raw_data():
    """Сборка сырых файлов, очистка и удаление дубликатов"""
    print("  -> Склейка и базовая очистка файлов...")

    all_dfs = []
    for filename in ["sites_raw.csv", "telegram_raw.csv"]:
        filepath = os.path.join(config.RAW_DATA_DIR, filename)
        if os.path.exists(filepath):
            df = pd.read_csv(filepath, sep=';')
            all_dfs.append(df)

    if not all_dfs:
        print("  [!] Сырые данные не найдены. Сначала запустите парсеры.")
        return pd.DataFrame()

    master_df = pd.concat(all_dfs, ignore_index=True)

    # Удаляем пустые описания и дубликаты
    master_df = master_df.dropna(subset=['description'])
    master_df = master_df.drop_duplicates(subset=['description'])

    # Фильтрация по стеку
    master_df['is_valid'] = master_df['description'].apply(is_csharp_vacancy)
    master_df = master_df[master_df['is_valid'] == True].drop(columns=['is_valid'])

    cleaned_path = os.path.join(config.PROCESSED_DATA_DIR, "cleaned_vacancies.csv")
    master_df.to_csv(cleaned_path, index=False, sep=';', encoding='utf-8-sig')
    print(f"  -> Очистка завершена. Итоговых уникальных вакансий: {len(master_df)}")
    return master_df


def extract_features_with_llm(description):
    """Отправка текста в Saiga для извлечения структурированного JSON"""
    prompt = f"""Ты — IT-аналитик. Проанализируй текст вакансии C#-разработчика и извлеки данные в формате строгого JSON.
Ключи JSON:
- "exp_years_norm": минимальный требуемый опыт в годах (число float, например 3.0. Если не указано, пиши 0.0).
- "tech_list": список конкретных технологий и фреймворков через запятую (например "C#, .NET Core, SQL").
- "resp_level": уровень ответственности/грейд от 1 до 5 (1 - Стажер, 2 - Junior, 3 - Middle, 4 - Senior, 5 - Lead/Architect). Оцени по тексту.
- "arch_keywords": ключевые слова по архитектуре и подходам (например "Microservices, Docker, DDD, CI/CD"). Если нет, оставь пустым.

Верни ТОЛЬКО валидный JSON, без markdown-разметки (без ```json), без вступлений и пояснений.
Текст вакансии:
{description[:2500]} # Ограничиваем длину, чтобы не перегрузить контекст
"""
    try:
        response = ollama.generate(
            model=config.OLLAMA_MODEL,
            prompt=prompt,
            options={'temperature': config.OLLAMA_TEMPERATURE}
        )

        # Вырезаем JSON из ответа (защита от "Вот ваш JSON: ...")
        text_resp = response['response']
        match = re.search(r'\{.*\}', text_resp, re.DOTALL)
        if match:
            json_str = match.group(0)
            data = json.loads(json_str)
            return data
        else:
            return None
    except Exception as e:
        print(f"Ошибка LLM: {e}")
        return None


def process_and_label_data():
    """Основной оркестратор этапа подготовки датасета"""
    df = clean_raw_data()
    if df.empty:
        return

    print(f"  -> Начинаю извлечение признаков через {config.OLLAMA_MODEL}...")

    # Новые колонки
    df['exp_years_norm'] = 0.0
    df['tech_list'] = ""
    df['resp_level'] = 0
    df['arch_keywords'] = ""
    df['tech_count'] = 0

    for index, row in df.iterrows():
        print(f"     Обработка {index + 1}/{len(df)}...")
        extracted = extract_features_with_llm(row['description'])

        if extracted:
            df.at[index, 'exp_years_norm'] = float(extracted.get('exp_years_norm', 0.0))

            techs = extracted.get('tech_list', '')
            df.at[index, 'tech_list'] = techs

            # Считаем количество технологий
            tech_count = len([t for t in techs.split(',') if t.strip()]) if techs else 0
            df.at[index, 'tech_count'] = tech_count

            df.at[index, 'resp_level'] = int(extracted.get('resp_level', 0))
            df.at[index, 'arch_keywords'] = extracted.get('arch_keywords', '')

    # Для удобства переименовываем колонку опыта
    df = df.rename(columns={'experience': 'raw_experience'})

    # Сохраняем в том самом формате ANALYZED_VACANCIES.csv
    final_path = os.path.join(config.PROCESSED_DATA_DIR, "ANALYZED_VACANCIES.csv")
    df.to_csv(final_path, index=False, sep=';', encoding='utf-8-sig')
    print(f"✅ Датасет успешно сформирован и сохранен: {final_path}\n")


if __name__ == "__main__":
    process_and_label_data()