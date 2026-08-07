import asyncio
import qrcode
import getpass
import pandas as pd
import os
from datetime import datetime
from telethon import TelegramClient
from telethon.tl.functions.messages import GetHistoryRequest
from telethon.errors import SessionPasswordNeededError

from hr_matrix_cli import config


async def login_with_qr(client):
    """Логика входа через QR-код с поддержкой 2FA[cite: 9]"""
    if not await client.is_user_authorized():
        print("Начинаю процесс авторизации через QR-код...[cite: 9]")
        qr_login = await client.qr_login()

        print("\n" + "=" * 50)
        print("СКАНИРУЙТЕ ЭТОТ КОД В ПРИЛОЖЕНИИ TELEGRAM:[cite: 9]")
        qr_login.url
        qr = qrcode.QRCode()
        qr.add_data(qr_login.url)
        qr.print_ascii()

        try:
            await qr_login.wait(timeout=120)
            print("\n[ИНФО] QR отсканирован.[cite: 9]")
        except SessionPasswordNeededError:
            print("\nУ ВАС ВКЛЮЧЕН ОБЛАЧНЫЙ ПАРОЛЬ (2FA).[cite: 9]")
            password = getpass.getpass("Введите ваш облачный пароль Telegram:[cite: 9]")
            try:
                await client.sign_in(password=password)
            except Exception as e:
                print(f"[ОШИБКА] Не удалось войти: {e}")
                return False
        except Exception as e:
            print(f"\n[ОШИБКА] {e}")
            return False

    print("\n[УСПЕХ] Вы авторизованы в Telegram!")
    return True


async def scrape_channels(client):
    """Сбор сообщений из каналов[cite: 9]"""
    all_vacancies = []

    for channel_username in config.TG_CHANNELS:
        print(f"Парсинг TG канала: @{channel_username}...")
        try:
            entity = await client.get_entity(channel_username)
            history = await client(GetHistoryRequest(
                peer=entity, offset_id=0, offset_date=None,
                add_offset=0, limit=1000, max_id=0, min_id=0, hash=0
            ))

            for msg in history.messages:
                if msg.message:
                    text_lower = msg.message.lower()
                    if any(word in text_lower for word in config.TG_KEYWORDS):
                        all_vacancies.append({
                            'title': f"Telegram: {channel_username}",
                            'experience': 'Не указано',
                            'description': msg.message,
                            'url': f"https://t.me/{channel_username}/{msg.id}",
                            'source': 'telegram'
                        })
        except Exception as e:
            print(f"Ошибка при обработке @{channel_username}: {e}")

    return all_vacancies


async def scrape_all_channels():
    print("--- Запуск парсинга Telegram ---")
    client = TelegramClient(
        'parser_session',
        config.TG_API_ID,
        config.TG_API_HASH,
        device_model="HR Matrix Parser",
        system_version="Windows 11"
    )

    await client.connect()
    if await login_with_qr(client):
        data = await scrape_channels(client)
        if data:
            df = pd.DataFrame(data)

            # Базовая очистка[cite: 9]
            df['description'] = df['description'].apply(lambda x: str(x).replace('\r', '').replace('\t', ' ').strip())
            df.drop_duplicates(subset=['description'], inplace=True)

            filename = os.path.join(config.RAW_DATA_DIR, "telegram_raw.csv")
            df.to_csv(filename, index=False, sep=';', encoding='utf-8-sig')
            print(f"[УСПЕХ] Собрано TG вакансий: {len(df)}")
        else:
            print("В Telegram вакансий не найдено.")
    await client.disconnect()