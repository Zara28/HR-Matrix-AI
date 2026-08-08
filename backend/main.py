from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from routers import candidate, matrix, settings
from core.database import init_db
from prometheus_client import make_asgi_app
import asyncio
import psutil

from core.monitoring import SYSTEM_CPU_USAGE, SYSTEM_RAM_USAGE

app = FastAPI(title="HR Matrix AI API", version="2.0")

metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)


# 2. Фоновая задача для снятия метрик инфраструктуры
async def collect_system_metrics():
    # Инициализируем счетчик CPU (первый вызов нужен для калибровки psutil)
    psutil.cpu_percent(interval=None)

    while True:
        # Снимаем текущие показания
        cpu_usage = psutil.cpu_percent(interval=None)
        ram_usage = psutil.virtual_memory().percent

        # Записываем их в метрики Prometheus
        SYSTEM_CPU_USAGE.set(cpu_usage)
        SYSTEM_RAM_USAGE.set(ram_usage)

        # Делаем паузу в 5 секунд перед следующим замером
        await asyncio.sleep(5)

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
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)


# 2. Фоновая задача для снятия метрик железа
async def collect_system_metrics():
    while True:
        SYSTEM_CPU_USAGE.set(psutil.cpu_percent(interval=None))

        ram_usage = psutil.virtual_memory().percent
        SYSTEM_RAM_USAGE.set(ram_usage)

        await asyncio.sleep(5)  # Обновляем каждые 5 секунд


@app.get("/")
def read_root():
    return {"status": "Модульный FastAPI сервер работает!"}


@app.on_event("startup")
def startup_event():
    init_db()
    asyncio.create_task(collect_system_metrics())


def check_ram_throttle():
    if psutil.virtual_memory().percent >= 85.0:
        raise HTTPException(
            status_code=503,
            detail="System is currently overloaded (RAM > 85%). Throttling active."
        )