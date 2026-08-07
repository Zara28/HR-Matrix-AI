import os
import pandas as pd
from fastapi import APIRouter, UploadFile, File, HTTPException
from core.config import UPLOAD_DIR
from services.survey_processor import set_weights_from_matrix

router = APIRouter(prefix="/api/matrix", tags=["Matrix"])


@router.post("/upload")
async def upload_matrix(matrix_file: UploadFile = File(...)):
    file_path = os.path.join(UPLOAD_DIR, matrix_file.filename)

    with open(file_path, "wb") as buffer:
        buffer.write(await matrix_file.read())

    try:
        filename_lower = matrix_file.filename.lower()

        # Читаем в зависимости от расширения файла
        if filename_lower.endswith('.csv'):
            # Пробуем прочитать CSV с разделителем точка с запятой (как было в прототипе)
            matrix_df = pd.read_csv(file_path, sep=';')
            if len(matrix_df.columns) == 1:  # Если разделитель оказался другим
                matrix_df = pd.read_csv(file_path, sep=',')
        elif filename_lower.endswith(('.xlsx', '.xls')):
            matrix_df = pd.read_excel(file_path)
        else:
            raise HTTPException(status_code=400, detail="Формат должен быть .csv, .xlsx или .xls")

        # Убираем возможные лишние пробелы в названиях колонок
        matrix_df.columns = matrix_df.columns.str.strip()

        set_weights_from_matrix(matrix_df)
        print(matrix_df)

        return {
            "message": "Матрица успешно загружена и прочитана!",
            "total_skills": len(matrix_df),
            "columns_found": list(matrix_df.columns)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка чтения матрицы: {str(e)}")