import os
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from hr_matrix_cli import config

def get_wsp(tech_string, weights):
    """Вычисляет WSP — сумму нормализованных весов навыков"""
    if pd.isna(tech_string) or str(tech_string).strip() == '':
        return 0.0
    skills = [s.strip().lower() for s in str(tech_string).split(',') if s.strip()]
    # Если навык новый и его нет в матрице, даем ему минимальный базовый вес 0.001
    return sum([weights.get(s, 0.001) for s in skills])


def calculate_and_cluster():
    """Расчет TSI, кластеризация KMeans и вычисление пограничных значений грейдов"""
    print("  -> Запуск расчета TSI и кластеризации...")

    vacancies_path = os.path.join(config.PROCESSED_DATA_DIR, "ANALYZED_VACANCIES.csv")
    matrix_path = os.path.join(config.PROCESSED_DATA_DIR, "SKILL_IMPORTANCE_MATRIX.csv")

    if not os.path.exists(vacancies_path) or not os.path.exists(matrix_path):
        print("  [!] Не найдены исходные файлы для кластеризации.")
        return {'junior_middle': 0.0, 'middle_senior': 0.0}

    df = pd.read_csv(vacancies_path, sep=';', encoding='utf-8-sig')
    skill_matrix = pd.read_csv(matrix_path, sep=';', encoding='utf-8-sig')

    # Превращаем матрицу компетенций в словарь {навык: вес}
    weights = dict(zip(skill_matrix['skill'], skill_matrix['mean_importance']))

    # 1. Расчет базовых метрик
    df['WSP'] = df['tech_list'].apply(lambda x: get_wsp(x, weights))
    df['L_resp'] = pd.to_numeric(df['resp_level'], errors='coerce').fillna(0)

    # Флаг наличия архитектурных навыков (1 - есть, 0 - нет)
    df['B_arch'] = df['arch_keywords'].apply(
        lambda x: 1 if pd.notna(x) and str(x).strip().lower() not in ['', 'none'] else 0
    )

    # Топологическое взаимодействие (Мультипликатор архитектуры)
    df['Arch_Multiplier'] = df['B_arch'] * df['WSP']

    # 2. Итоговая формула TSI
    df['TSI'] = df['WSP'] + (2 * df['L_resp']) + df['Arch_Multiplier']

    # 3. Кластеризация
    features = ['WSP', 'L_resp', 'B_arch', 'Arch_Multiplier']
    X = df[features].fillna(0)

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # Находим 3 кластера (Junior, Middle, Senior)
    kmeans = KMeans(n_clusters=3, random_state=42, n_init=10)
    df['cluster'] = kmeans.fit_predict(X_scaled)

    # Маппинг: сортируем кластеры по среднему значению TSI, чтобы правильно назвать грейды
    order = df.groupby('cluster')['TSI'].mean().sort_values().index
    grade_map = {order[0]: 'Junior', order[1]: 'Middle', order[2]: 'Senior'}
    df['Grade'] = df['cluster'].map(grade_map)

    # 4. Расчет математических порогов (середина между экстремумами соседних грейдов)
    try:
        t1 = (df[df['Grade'] == 'Junior']['TSI'].max() + df[df['Grade'] == 'Middle']['TSI'].min()) / 2
        t2 = (df[df['Grade'] == 'Middle']['TSI'].max() + df[df['Grade'] == 'Senior']['TSI'].min()) / 2
    except BaseException:
        # Резервный вариант, если в мелком датасете один из грейдов не определился
        t1, t2 = 0.0, 0.0

    # 5. Сохранение итогов
    final_path = os.path.join(config.FINAL_DATA_DIR, "FINAL_CLUSTERED_RESULTS.csv")
    df.to_csv(final_path, index=False, sep=';', encoding='utf-8-sig')

    return {
        'junior_middle': float(t1),
        'middle_senior': float(t2)
    }


if __name__ == "__main__":
    thresholds = calculate_and_cluster()
    print(f"J -> M: {thresholds['junior_middle']}, M -> S: {thresholds['middle_senior']}")