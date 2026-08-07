import io
import pandas as pd
from fastapi import APIRouter, UploadFile, File, HTTPException
from services.survey_processor import process_survey_dataframe
from pydantic import BaseModel
from services.google_sheets import fetch_survey_from_google_sheet
from fastapi import Depends
from sqlalchemy.orm import Session
from core.database import get_db, CandidateDB

router = APIRouter(prefix="/api/candidate", tags=["Candidate"])

@router.post("/process-survey")
async def process_survey(survey_file: UploadFile = File(...)):
    try:
        contents = await survey_file.read()
        df = pd.read_excel(io.BytesIO(contents)) if survey_file.filename.endswith('.xlsx') else pd.read_csv(io.BytesIO(contents), sep='\t')
        passports = process_survey_dataframe(df)
        return {"status": "success", "candidates": passports}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка обработки опроса: {str(e)}")


class SyncRequest(BaseModel):
    sheet_url: str
    vacancy_id: int # Теперь фронт обязан прислать ID вакансии


@router.post("/sync-sheet")
def sync_sheet(data: SyncRequest, db: Session = Depends(get_db)):
    try:
        # 1. Вытягиваем свежий датафрейм из Google Таблицы
        df = fetch_survey_from_google_sheet(data.sheet_url)

        # 2. Прогоняем через наш пайплайн анализа (который обрабатывает код и TSI)
        passports = process_survey_dataframe(df, data.vacancy_id, db)
        return {"message": "Успешно!", "candidates": passports}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/list")
def get_stored_candidates(vacancy_id: int = None, db: Session = Depends(get_db)):
    query = db.query(CandidateDB)
    if vacancy_id:
        query = query.filter(CandidateDB.vacancy_id == vacancy_id)
    candidates = query.all()
    result = []
    for c in candidates:
        result.append({
            "id": c.id,
            "name": c.name,
            "grade": c.grade,
            "marketGrade": c.market_grade,
            "selfGrade": c.self_grade,
            "kScore": c.k_score,
            "theory": c.theory,
            "rationale": c.rationale,
            "tsi": c.tsi
        })
    return {"status": "success", "candidates": result}


@router.get("/{candidate_id}")
def get_single_candidate(candidate_id: int, db: Session = Depends(get_db)):
    candidate = db.query(CandidateDB).filter(CandidateDB.id == candidate_id).first()
    if not candidate:
        raise HTTPException(status_code=404, detail="Кандидат не найден")

    return {
        "id": candidate.id,
        "name": candidate.name,
        "grade": candidate.grade,
        "marketGrade": candidate.market_grade,
        "selfGrade": candidate.self_grade,
        "kScore": candidate.k_score,
        "theory": candidate.theory,
        "rationale": candidate.rationale,
        "tsi": candidate.tsi,
        # Новые поля
        "expYears": candidate.exp_years,
        "archScore": candidate.arch_score
    }