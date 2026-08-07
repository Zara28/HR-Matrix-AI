import re
import pandas as pd
from sqlalchemy.orm import Session

from core.database import CandidateDB
from core.database import SystemSettingsDB, VacancyDB
# Убедись, что импортирована функция get_embedding
from ml.code_analyzer import get_embedding, calculate_k_quality_v3
# Глобальное состояние для матрицы весов
weights_dict = {}


def save_passports_to_db(passports: list, vacancy_id: int, db: Session):
    try:
        for p in passports:
            # Ищем существующего кандидата по имени, чтобы обновить, или создаем нового
            existing = db.query(CandidateDB).filter(
                CandidateDB.name == p["name"],
                CandidateDB.vacancy_id == vacancy_id
            ).first()
            if existing:
                existing.grade = p["grade"]
                existing.market_grade = p["marketGrade"]
                existing.self_grade = p["selfGrade"]
                existing.k_score = p["kScore"]
                existing.theory = p["theory"]
                existing.rationale = p["rationale"]
                existing.tsi = p["tsi"]
                existing.exp_years = p["exp_years"]
                existing.arch_score = p["arch_score"]
                existing.vacancy_id = p["vacancy_id"]
            else:
                db_item = CandidateDB(
                    name=p["name"],
                    grade=p["grade"],
                    market_grade=p["marketGrade"],
                    self_grade=p["selfGrade"],
                    k_score=p["kScore"],
                    theory=p["theory"],
                    rationale=p["rationale"],
                    tsi=p["tsi"],
                    exp_years = p["exp_years"],
                    arch_score = p["arch_score"],
                    vacancy_id = p['vacancy_id']
                )
                db.add(db_item)
        db.commit()
    finally:
        db.close()


def get_settings(vacancy_id: int, db:Session):
    try:
        # 1. Достаем пороги
        settings = db.query(SystemSettingsDB).first()
        middle_tsi_threshold = settings.tsi_junior_max if settings else 5.24
        senior_tsi_threshold = settings.tsi_middle_max if settings else 11.38

        # 2. Достаем код для конкретной вакансии и сразу превращаем его в векторы
        vacancy = db.query(VacancyDB).filter(VacancyDB.id == vacancy_id).first()
        if not vacancy or not vacancy.ideal_code or not vacancy.broken_code:
            raise ValueError("У вакансии не задан эталонный или сломанный код!")

        # Генерируем векторы один раз для всей таблицы кандидатов
        v_ideal_dynamic = get_embedding(vacancy.ideal_code)
        v_broken_dynamic = get_embedding(vacancy.broken_code)
        return middle_tsi_threshold, senior_tsi_threshold, v_ideal_dynamic, v_broken_dynamic
    finally:
        db.close()


def set_weights_from_matrix(matrix_df: pd.DataFrame):
    global weights_dict
    # Приводим названия колонок к нижнему регистру для надежности
    matrix_df.columns = [str(c).lower().strip() for c in matrix_df.columns]

    # Ищем колонки навыка и веса
    skill_col = next((c for c in matrix_df.columns if 'skill' in c or 'навык' in c), None)
    weight_col = next((c for c in matrix_df.columns if 'importance' in c or 'weight' in c or 'вес' in c or 'mean' in c),
                      None)

    if skill_col and weight_col:
        weights_dict = dict(zip(matrix_df[skill_col].astype(str).str.lower().str.strip(), matrix_df[weight_col]))
    else:
        # Фолбек на первые две колонки
        weights_dict = dict(zip(matrix_df.iloc[:, 0].astype(str).str.lower().str.strip(), matrix_df.iloc[:, 1]))


def get_verified_grade(tsi_score: float, k_score: float, middle_threshold: float, senior_threshold: float) -> dict:
    # Заменяем старый хардкод на динамические переменные
    if tsi_score >= senior_threshold:
        base_grade = "Senior"
    elif tsi_score >= middle_threshold:
        base_grade = "Middle"
    else:
        base_grade = "Junior"

    if base_grade == "Senior":
        if k_score >= 0.7:
            res, desc = "Senior (Подтвержденный)", "Архитектурный потенциал полностью подтвержден качеством реализации."
        else:
            res, desc = "Senior (Проектировщик)", "Высокий уровень системного мышления при слабой практической реализации."
    elif base_grade == "Middle":
        if k_score >= 0.6:
            res, desc = "Middle (Стабильный)", "Технический уровень соответствует рыночным ожиданиям."
        elif k_score >= 0.4:
            res, desc = "Middle (Рискованный)", "Рыночный опыт выше инженерной культуры. Требуется менторство по Clean Code."
        else:
            res, desc = "Junior (Переоцененный)", "Значительный разрыв между опытом и качеством кода. Грейд снижен."
    else:
        if k_score >= 0.7:
            res, desc = "Junior+ (Strong)", "Высокий потенциал: инженерная культура опережает рыночный опыт."
        else:
            res, desc = "Junior", "Требуется развитие фундаментальных навыков и накопление опыта."

    return {"grade": res, "rationale": desc, "tsi_score": round(float(tsi_score), 2), "k_score": round(float(k_score), 2)}


def process_survey_dataframe(df: pd.DataFrame, vacancy_id: int, db: Session) -> list:
    middle_tsi_threshold, senior_tsi_threshold, v_ideal_dynamic, v_broken_dynamic = get_settings(vacancy_id, db)

    column_map = {
        'Твой ник в Telegram': 'tg',
        'Твой стаж в разработке на C#': 'exp',
        'Ты работаешь C#-разработчиком': 'job_grade',
        'На какой грейд ты оцениваешь себя': 'self_grade',
        'Какие технические навыки': 'skills',
        'С чем из ниже перечисленного': 'arch_list',
        'Твое решение': 'code'
    }
    new_columns = []
    for col in df.columns:
        found = False
        for key, val in column_map.items():
            if key in col:
                new_columns.append(val)
                found = True
                break
        if not found:
            new_columns.append(col)

    df.columns = new_columns

    # Чистим код от двойных кавычек и лишних пробелов в начале/конце
    if 'code' in df.columns:
        df['code'] = df['code'].str.replace('""', '"').str.strip()

    passports = []
    grade_standard = {'джун': 'Junior', 'мидл': 'Middle', 'сеньор': 'Senior', 'синьор': 'Senior'}
    resp_map = {'Junior': 1.5, 'Middle': 3.0, 'Senior': 5.0, 'Unknown': 1.0}

    for idx, row in df.iterrows():
        # Достаем значение и сразу убираем лишние пробелы по краям
        tg = str(row.get('tg', '')).strip()

        # Если строка оказалась пустой, 'nan' или None — даем уникальное имя
        if not tg or tg.lower() == 'nan' or tg.lower() == 'none':
            tg = f'respondent_{idx}'

        code_text = str(row.get('code', ''))

        # Опыт
        exp_val = 0.0
        exp_raw = str(row.get('exp', '0')).replace(',', '.')
        match = re.search(r"(\d+\.?\d*)", exp_raw)
        if match:
            exp_val = float(match.group(1))

        def norm_g(val):
            v = str(val).lower()
            for r, e in grade_standard.items():
                if r in v: return e
            return 'Unknown'

        market_g = norm_g(row.get('job_grade', ''))
        self_g = norm_g(row.get('self_grade', ''))
        l_resp = resp_map.get(market_g, 1.0)

        # WSP расчет с надежным поиском весов
        tech_text = str(row.get('skills', '')).lower()
        arch_text = str(row.get('arch_list', '')).lower()

        if tech_text == 'nan': tech_text = ""
        if arch_text == 'nan': arch_text = ""

        combined_text = tech_text + " " + arch_text
        all_skills = [s.strip() for s in re.split(r'[,\n;/]+', combined_text) if s.strip()]
        unique_skills = set(all_skills)

        # Считаем вес с отладкой
        wsp = 0.0
        for s in unique_skills:
            # Ищем точное совпадение или частичное, если ключ длинный
            weight = weights_dict.get(s, None)
            if weight is None:
                # Попробуем найти среди ключей матрицы то, что содержит навык
                matched_key = next((k for k in weights_dict.keys() if s in k or k in s), None)
                weight = weights_dict.get(matched_key, 0.1)  # Небольшой дефолтный вес, если навыка нет в таблице
            wsp += float(weight)

        b_arch = 1 if arch_text and arch_text != 'nan' else 0

        # Финальный TSI по нашей формуле
        tsi_final = wsp + (2 * l_resp) + (b_arch * wsp)

        v_cand = get_embedding(code_text)
        k_quality = calculate_k_quality_v3(v_ideal_dynamic, v_broken_dynamic, v_cand)

        verified = get_verified_grade(tsi_final, k_quality, middle_tsi_threshold, senior_tsi_threshold)

        arch_items = [x.strip() for x in str(row.get('arch_list', '')).split(',') if
                      x.strip() and x.strip().lower() != 'nan']
        arch_score_val = min(1.0, len(arch_items) / 8.0) if arch_items else 0.0

        passports.append({
            "id": idx + 1,
            "name": tg,
            "grade": verified["grade"],
            "marketGrade": market_g,
            "selfGrade": self_g,
            "kScore": verified["k_score"],
            "theory": round(min(tsi_final / 20.0, 1.0), 2),  # Нормализация для шкалы фронта
            "rationale": verified["rationale"],
            "tsi": verified["tsi_score"],
            "exp_years": exp_val,
            "arch_score": arch_score_val,
            "vacancy_id": vacancy_id
        })

    save_passports_to_db(passports, vacancy_id, db)

    return passports
