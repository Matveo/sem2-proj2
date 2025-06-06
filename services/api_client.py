import aiohttp
import asyncio
from typing import Dict, List, Optional
from utils.logger import logger

API_BASE_URL = "https://ftapi.pythonanywhere.com"
REQUEST_TIMEOUT = 10
RETRY_COUNT = 3

# Кэш для списка языков
_languages_cache: Optional[Dict] = None

async def get_languages() -> Dict[str, str]:
    """
    Получает список поддерживаемых языков из API с кэшированием
    """
    global _languages_cache
    
    if _languages_cache is not None:
        return _languages_cache
    
    try:
        timeout = aiohttp.ClientTimeout(total=REQUEST_TIMEOUT)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(f"{API_BASE_URL}/languages") as response:
                if response.status == 200:
                    data = await response.json()
                    _languages_cache = data
                    logger.info("Список языков успешно загружен и закэширован")
                    return data
                else:
                    logger.error(f"Ошибка получения языков: HTTP {response.status}")
                    return _get_fallback_languages()
    except asyncio.TimeoutError:
        logger.error("Таймаут при получении списка языков")
        return _get_fallback_languages()
    except aiohttp.ClientError as e:
        logger.error(f"Сетевая ошибка при получении языков: {e}")
        return _get_fallback_languages()
    except Exception as e:
        logger.error(f"Неожиданная ошибка при получении языков: {e}")
        return _get_fallback_languages()

def _get_fallback_languages() -> Dict[str, str]:
    """
    Возвращает базовый набор языков в случае ошибки API
    """
    return {
        "en": "English",
        "ru": "Русский",
        "es": "Español", 
        "fr": "Français",
        "de": "Deutsch",
        "it": "Italiano",
        "pt": "Português",
        "zh": "中文",
        "ja": "日本語",
        "ko": "한국어"
    }

async def translate_text(text: str, source_lang: str, target_lang: str) -> Optional[str]:
    """
    Переводит текст с помощью API
    
    Args:
        text: Текст для перевода
        source_lang: Исходный язык (например, 'en')
        target_lang: Целевой язык (например, 'ru')
        
    Returns:
        Переведённый текст или None в случае ошибки
    """
    if not text or not text.strip():
        logger.error("Пустой текст для перевода")
        return None
    
    if source_lang == target_lang:
        logger.info("Исходный и целевой языки совпадают")
        return text
    
    # Обрезаем текст если он слишком длинный
    if len(text) > 4000:
        text = text[:4000]
        logger.warning("Текст обрезан до 4000 символов")
    
    for attempt in range(RETRY_COUNT):
        try:
            timeout = aiohttp.ClientTimeout(total=REQUEST_TIMEOUT)
            
            params = {
                'sl': source_lang,
                'dl': target_lang,
                'text': text
            }
            
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(f"{API_BASE_URL}/translate", params=params) as response:
                    
                    if response.status == 200:
                        data = await response.json()
                        
                        # Проверяем структуру ответа
                        if isinstance(data, dict) and 'destination-text' in data:
                            translated = data['destination-text']
                            if translated and translated.strip():
                                logger.info(f"Перевод выполнен успешно: {source_lang} -> {target_lang}")
                                return translated.strip()
                            else:
                                logger.error("API вернул пустой перевод")
                                return None
                        else:
                            logger.error(f"Некорректная структура ответа API: {data}")
                            return None
                    
                    elif response.status == 400:
                        logger.error("Некорректные параметры запроса")
                        return None
                    
                    elif response.status == 429:
                        logger.warning("Превышен лимит запросов, повторная попытка...")
                        await asyncio.sleep(2 ** attempt)  # Экспоненциальная задержка
                        continue
                    
                    else:
                        logger.error(f"API вернул ошибку: HTTP {response.status}")
                        if attempt < RETRY_COUNT - 1:
                            await asyncio.sleep(1)
                            continue
                        return None
                        
        except asyncio.TimeoutError:
            logger.error(f"Таймаут при переводе (попытка {attempt + 1}/{RETRY_COUNT})")
            if attempt < RETRY_COUNT - 1:
                await asyncio.sleep(1)
                continue
            return None
            
        except aiohttp.ClientError as e:
            logger.error(f"Сетевая ошибка при переводе: {e} (попытка {attempt + 1}/{RETRY_COUNT})")
            if attempt < RETRY_COUNT - 1:
                await asyncio.sleep(1)
                continue
            return None
            
        except Exception as e:
            logger.error(f"Неожиданная ошибка при переводе: {e}")
            return None
    
    logger.error("Все попытки перевода исчерпаны")
    return None

async def detect_language(text: str) -> str:
    """
    Определяет язык текста (заглушка)
    В реальном API может быть отдельный endpoint для определения языка
    """
    if not text:
        return "auto"
    
    # Простая эвристика для определения языка
    russian_chars = set('абвгдеёжзийклмнопрстуфхцчшщъыьэюя')
    if any(char.lower() in russian_chars for char in text):
        return "ru"
    
    return "en"  # По умолчанию английский