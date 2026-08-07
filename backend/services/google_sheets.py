import gspread
import pandas as pd


def fetch_survey_from_google_sheet(sheet_url: str) -> pd.DataFrame:
    """
    Забирает данные из Google Таблицы по ее URL с помощью Service Account.
    """
    try:
        # Авторизация по нашему JSON-файлу
        gc = gspread.service_account(filename="credentials.json")

        # Открываем документ по ссылке
        spreadsheet = gc.open_by_url(sheet_url)

        # Берем первый лист таблицы
        worksheet = spreadsheet.get_worksheet(0)

        # Получаем все строчки в виде словарей
        data = worksheet.get_all_records()

        if not data:
            raise ValueError("Таблица пуста или не содержит данных!")

        return pd.DataFrame(data)

    except Exception as e:
        raise RuntimeError(f"Не удалось прочитать Google Таблицу: {str(e)}")