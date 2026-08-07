from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

DB_PATH = "hr_database.db"
engine = create_engine(f"sqlite:///{DB_PATH}", connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class CandidateDB(Base):
    __tablename__ = "candidates"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    grade = Column(String)
    market_grade = Column(String)
    self_grade = Column(String)
    k_score = Column(Float)
    theory = Column(Float)
    rationale = Column(String)
    tsi = Column(Float)
    exp_years = Column(Float, default=0.0)
    arch_score = Column(Float, default=0.0)
    vacancy_id = Column(Integer, index=True)

class VacancyDB(Base):
    __tablename__ = "vacancies"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, unique=True, index=True) # Например: "C# Developer"
    sheet_url = Column(String)                      # Ссылка на Google Таблицу
    is_active = Column(Boolean, default=True)       # Активна ли сейчас
    ideal_code = Column(String, default="")
    broken_code = Column(String, default="")


class SystemSettingsDB(Base):
    __tablename__ = "settings"

    id = Column(Integer, primary_key=True, index=True)
    tsi_junior_max = Column(Float, default=4.5)     # Порог до мидла
    tsi_middle_max = Column(Float, default=8.0)     # Порог до сеньора

def init_db():
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()