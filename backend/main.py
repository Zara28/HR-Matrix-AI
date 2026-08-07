from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import candidate, matrix, settings
from core.database import init_db

app = FastAPI(title="HR Matrix AI API", version="2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(matrix.router)
app.include_router(candidate.router)
app.include_router(settings.router)
@app.get("/")
def read_root():
    return {"status": "Модульный FastAPI сервер работает!"}


@app.on_event("startup")
def startup_event():
    init_db()