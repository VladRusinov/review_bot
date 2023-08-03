import logging
import os
import sys
import time
from http import HTTPStatus

import requests
import telegram
from dotenv import load_dotenv

from exceptions import (EmptyAPIAnswerError, InvalidStatusCodeError,
                        NoEnvVarieblesError)

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
stream_handler = logging.StreamHandler(stream=sys.stdout)
BOT_PATH = os.path.abspath(__file__)
CATALOG_NAME = os.path.dirname(BOT_PATH) + r'\logs.log'
file_handler = logging.FileHandler(filename=CATALOG_NAME)
formatter = logging.Formatter(
    '%(asctime)s - %(filename)s - %(lineno)d - '
    '%(funcName)s - %(levelname)s - %(message)s'
)
stream_handler.setFormatter(formatter)
file_handler.setFormatter(formatter)
logger.addHandler(stream_handler)
logger.addHandler(file_handler)

load_dotenv()


PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_PERIOD = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


def check_tokens():
    """Проверка доступности переменных окружения."""
    if not all((PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID)):
        logger.critical('Отсутствуют переменные окружения')
        raise NoEnvVarieblesError()


def send_message(bot, message):
    """отправка сообщения в Telegram чат."""
    try:
        logger.debug('Начинаем отправлять сообщение')
        bot.send_message(
            chat_id=TELEGRAM_CHAT_ID,
            text=message,
        )
    except telegram.error.TelegramError as error:
        logger.error(f'Не удалось отправить сообщение: {error}')
    else:
        logger.debug('Сообщение успешно отправлено')


def get_api_answer(timestamp):
    """Получение ответа от API."""
    params = {'from_date': timestamp}
    REQUEST_DATA = {
        'endpoint': ENDPOINT,
        'headers': HEADERS,
        'params': params
    }
    logger.debug(
        'делаем запрос: адрес- {endpoint}, данные заголовка - {headers}, '
        'параметры - {params}'.format(**REQUEST_DATA)
    )
    try:
        response = requests.get(
            REQUEST_DATA['endpoint'],
            params=REQUEST_DATA['params'],
            headers=REQUEST_DATA['headers']
        )
        if response.status_code != HTTPStatus.OK:
            raise InvalidStatusCodeError()
        return response.json()
    except requests.RequestException:
        ...


def check_response(response):
    """Проверка ответа API."""
    logger.debug("Проверяем ответ сервара")
    if not isinstance(response, dict):
        raise TypeError("type of response should be dict")
    homeworks = response.get('homeworks')
    if homeworks is None:
        EmptyAPIAnswerError()
    if not isinstance(homeworks, list):
        raise TypeError("type of 'homeworks' should be list")
    return homeworks


def parse_status(homework):
    """извлечение из информации о конкретной домашней работе её статус."""
    homework_name = homework.get('homework_name')
    if homework_name is None:
        raise KeyError('нет ключа "homework_name"')
    verdict = homework.get('status')
    if verdict not in HOMEWORK_VERDICTS:
        raise ValueError('неизвестный вердикт')
    verdict = HOMEWORK_VERDICTS.get(verdict)
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def main():
    """Основная логика работы бота."""
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    timestamp = 0
    check_tokens()
    old_status = None
    while True:
        try:
            answer = get_api_answer(timestamp)
            timestamp = answer.get('current_date', timestamp)
            homeworks = check_response(answer)
            if len(homeworks) != 0:
                new_status = parse_status(answer.get('homeworks')[0])
                if old_status != new_status:
                    send_message(bot, new_status)
                    old_status = new_status
            else:
                logger.debug('нет нового вердикта')
        except (InvalidStatusCodeError, requests.RequestException) as error:
            message = f'Сбой в работе программы: {error}'
            logger.error(message)
        except (EmptyAPIAnswerError, KeyError, ValueError) as error:
            message = f"Сбой в работе программы: {error}"
            logger.error(message)
            if message != old_status:
                send_message(bot, message)
                old_status = message
        finally:
            time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    main()
