import torch
import numpy as np
from transformers import AutoTokenizer, AutoModel
from scipy.spatial.distance import cosine

print("Загрузка GraphCodeBERT...")
MODEL_NAME = "microsoft/graphcodebert-base"
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
model = AutoModel.from_pretrained(MODEL_NAME)
model.eval()


def get_embedding(code: str) -> np.ndarray:
    if not code or str(code).strip() == "" or str(code) == 'nan':
        return np.zeros(768)
    inputs = tokenizer(str(code), return_tensors="pt", truncation=True, padding=True, max_length=512)
    with torch.no_grad():
        outputs = model(**inputs)
    return outputs.last_hidden_state.mean(dim=1).numpy()[0]


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