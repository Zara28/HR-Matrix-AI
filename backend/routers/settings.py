from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from core.database import get_db, SystemSettingsDB, VacancyDB

router = APIRouter(prefix="/api/settings", tags=["Settings"])


class TSISettingsUpdate(BaseModel):
    tsi_middle_min: float
    tsi_senior_min: float


@router.get("/tsi")
def get_tsi_settings(db: Session = Depends(get_db)):
    settings = db.query(SystemSettingsDB).first()
    # Если настроек еще нет в базе, создаем их с твоими значениями по умолчанию
    if not settings:
        settings = SystemSettingsDB(tsi_junior_max=5.24, tsi_middle_max=11.38)
        db.add(settings)
        db.commit()
        db.refresh(settings)

    return {
        "tsi_middle_min": settings.tsi_junior_max,
        "tsi_senior_min": settings.tsi_middle_max
    }


@router.post("/tsi")
def update_tsi_settings(data: TSISettingsUpdate, db: Session = Depends(get_db)):
    settings = db.query(SystemSettingsDB).first()
    if not settings:
        settings = SystemSettingsDB()
        db.add(settings)

    settings.tsi_junior_max = data.tsi_middle_min
    settings.tsi_middle_max = data.tsi_senior_min

    db.commit()
    return {"message": "Пороги TSI успешно обновлены!"}


class VacancyCreate(BaseModel):
    title: str
    sheet_url: str
    ideal_code: str
    broken_code: str


@router.get("/vacancies")
def get_vacancies(db: Session = Depends(get_db)):
    return db.query(VacancyDB).all()


# Обновляем POST-эндпоинт
@router.post("/vacancies")
def create_vacancy(data: VacancyCreate, db: Session = Depends(get_db)):
    new_vac = VacancyDB(
        title=data.title,
        sheet_url=data.sheet_url,
        ideal_code=data.ideal_code,
        broken_code=data.broken_code
    )
    db.add(new_vac)
    db.commit()
    db.refresh(new_vac)
    return new_vac


@router.delete("/vacancies/{vac_id}")
def delete_vacancy(vac_id: int, db: Session = Depends(get_db)):
    vac = db.query(VacancyDB).filter(VacancyDB.id == vac_id).first()
    if vac:
        db.delete(vac)
        db.commit()
    return {"message": "Вакансия удалена"}


class VacancyUpdate(BaseModel):
    title: str
    sheet_url: str
    ideal_code: str
    broken_code: str


@router.put("/vacancies/{vac_id}")
def update_vacancy(vac_id: int, data: VacancyUpdate, db: Session = Depends(get_db)):
    vac = db.query(VacancyDB).filter(VacancyDB.id == vac_id).first()
    if not vac:
        raise HTTPException(status_status=404, detail="Вакансия не найдена")

    vac.title = data.title
    vac.sheet_url = data.sheet_url
    vac.ideal_code = data.ideal_code
    vac.broken_code = data.broken_code

    db.commit()
    return {"message": "Вакансия обновлена"}