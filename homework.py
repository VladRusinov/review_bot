import logging
import os
import sys
import time
from http import HTTPStatus

import requests
import telegram
from dotenv import load_dotenv

from exceptions import (
    EmptyAPIAnswerError,
    InvalidStatusCodeError,
    NoEnvVarieblesError,
    RequestError
)

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
    REQUEST_DATA = {
        'url': ENDPOINT,
        'headers': HEADERS,
        'params': {'from_date': timestamp}
    }
    logger.debug(
        'делаем запрос: адрес- {url}, данные заголовка - {headers}, '
        'параметры - {params}'.format(**REQUEST_DATA)
    )
    try:
        response = requests.get(**REQUEST_DATA)
        if response.status_code != HTTPStatus.OK:
            raise InvalidStatusCodeError()
        return response.json()
    except requests.exceptions.RequestException:
        RequestError()


def check_response(response):
    """Проверка ответа API."""
    logger.debug("Проверяем ответ сервара")
    if not isinstance(response, dict):
        raise TypeError(
            f"type of response should be dict, not {type(response)}"
        )
    homeworks = response.get('homeworks')
    if homeworks is None:
        EmptyAPIAnswerError()
    if not isinstance(homeworks, list):
        raise TypeError(
            f"type of 'homeworks' should be list, not {type(homeworks)}"
        )
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
    check_tokens()
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    timestamp = 0
    old_status = None
    while True:
        try:
            answer = get_api_answer(timestamp)
            timestamp = answer.get('current_date', timestamp)
            homeworks = check_response(answer)
            if homeworks:
                new_status = parse_status(homeworks[0])
            else:
                new_status = 'нет нового вердикта'
                logger.debug(new_status)
            if old_status != new_status:
                send_message(bot, new_status)
                old_status = new_status

        except (InvalidStatusCodeError, RequestError) as error:
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
