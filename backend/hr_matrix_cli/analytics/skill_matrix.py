import os
import pandas as pd
from collections import defaultdict
from hr_matrix_cli import config


def build_matrix():
    """Сбор статистики по навыкам и расчет их относительной важности"""
    print("  -> Формирование матрицы компетенций...")
    input_path = os.path.join(config.PROCESSED_DATA_DIR, "ANALYZED_VACANCIES.csv")

    if not os.path.exists(input_path):
        print(f"  [!] Файл {input_path} не найден. Сначала запустите NLP пайплайн.")
        return

    df = pd.read_csv(input_path, sep=';', encoding='utf-8-sig')

    # Собираем статистику по каждому навыку
    skill_stats = defaultdict(lambda: {'count': 0, 'resp_sum': 0})

    for _, row in df.iterrows():
        techs = str(row.get('tech_list', ''))
        resp_level = int(row.get('resp_level', 0)) if pd.notna(row.get('resp_level')) else 0

        if pd.isna(techs) or not techs.strip():
            continue

        # Очищаем и приводим к нижнему регистру для точного совпадения
        skills = [s.strip().lower() for s in techs.split(',') if s.strip()]

        for s in skills:
            skill_stats[s]['count'] += 1
            skill_stats[s]['resp_sum'] += resp_level

    # Формируем итоговый DataFrame
    matrix_data = []
    for skill, stats in skill_stats.items():
        avg_resp = stats['resp_sum'] / stats['count'] if stats['count'] > 0 else 0
        # Базовая метрика важности: частота упоминаний * средний требуемый уровень ответственности
        raw_importance = stats['count'] * avg_resp

        matrix_data.append({
            'skill': skill,
            'count': stats['count'],
            'avg_resp_level': avg_resp,
            'raw_importance': raw_importance
        })

    matrix_df = pd.DataFrame(matrix_data)

    if not matrix_df.empty:
        # Нормализуем метрику важности от 0 до 1 для расчета WSP
        max_imp = matrix_df['raw_importance'].max()
        matrix_df['mean_importance'] = matrix_df['raw_importance'] / max_imp
        matrix_df = matrix_df.sort_values(by='mean_importance', ascending=False)

    output_path = os.path.join(config.PROCESSED_DATA_DIR, "SKILL_IMPORTANCE_MATRIX.csv")
    matrix_df.to_csv(output_path, index=False, sep=';', encoding='utf-8-sig')
    print(f"  -> Матрица компетенций сохранена (Всего уникальных навыков: {len(matrix_df)})")


if __name__ == "__main__":
    build_matrix()