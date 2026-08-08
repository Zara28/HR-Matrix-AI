import torch
import time
import numpy as np
from transformers import AutoTokenizer, AutoModel
from core.monitoring import INFERENCE_TIME, PROCESSED_CODE_BYTES, ACTIVE_WORKERS


print("Загрузка GraphCodeBERT...")
MODEL_NAME = "microsoft/graphcodebert-base"
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
model = AutoModel.from_pretrained(MODEL_NAME)
model.eval()


def get_embedding(code: str) -> np.ndarray:
    if not code or str(code).strip() == "" or str(code) == 'nan':
        return np.zeros(768)

    code_size = len(str(code).encode('utf-8'))
    PROCESSED_CODE_BYTES.inc(code_size)

    # 2. Регистрируем начало работы воркера
    ACTIVE_WORKERS.inc()
    start_time = time.time()

    try:
        inputs = tokenizer(str(code), return_tensors="pt", truncation=True, padding=True, max_length=512)
        with torch.no_grad():
            outputs = model(**inputs)
        return outputs.last_hidden_state.mean(dim=1).numpy()[0]
    finally:
        # 3. Записываем время выполнения и освобождаем воркер в блоке finally,
        # чтобы метрики снялись даже в случае ошибки токенизации
        INFERENCE_TIME.observe(time.time() - start_time)
        ACTIVE_WORKERS.dec()


def calculate_k_quality_v3(v_ideal: np.ndarray, v_broken: np.ndarray, v_cand: np.ndarray) -> float:
    """Расчет K-score через проекцию векторов (версия 3)."""
    vec_ideal = v_ideal - v_broken
    vec_cand = v_cand - v_broken
    dot_product = np.dot(vec_cand, vec_ideal)
    mag_ideal_sq = np.dot(vec_ideal, vec_ideal)
    if mag_ideal_sq == 0:
        return 0.0
    progress = dot_product / mag_ideal_sq
    return round(float(max(0, min(progress, 1.2))), 4)