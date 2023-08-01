import datetime as DT
import logging
import os
import sys
import time

import requests
import telegram
from dotenv import load_dotenv

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler(stream=sys.stdout)
formatter = logging.Formatter(
    '%(asctime)s - %(levelname)s - %(message)s'
)
handler.setFormatter(formatter)
logger.addHandler(handler)

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
    if (
        (PRACTICUM_TOKEN is None)
        or (TELEGRAM_TOKEN is None)
        or (TELEGRAM_CHAT_ID is None)
    ):
        logger.critical('Отсутствуют переменные окружения')
        raise Exception('Отсутствуют переменные окружения')


def send_message(bot, message):
    """отправка сообщения в Telegram чат."""
    try:
        bot.send_message(
            chat_id=TELEGRAM_CHAT_ID,
            text=message,
        )
        logger.debug('Сообщение успешно отправлено')
    except Exception:
        logger.error(f'Не удалось отправить сообщение: {Exception}')


def get_api_answer(timestamp):
    """Получение ответа от API."""
    params = {'from_date': timestamp}
    try:
        response = requests.get(ENDPOINT, headers=HEADERS, params=params)
        if response.status_code != 200:
            logger.error('status_code != 200')
            raise Exception('Error: status_code != 200')
        return response.json()
    except Exception:
        logger.error(Exception)
        raise Exception(f'Error: {Exception}')


def check_response(response):
    """Проверка ответа API."""
    if type(response) != dict:
        raise TypeError()
    if 'homeworks' not in response:
        logger.error('нет ключа "homeworks"')
        send_message(
            telegram.Bot(token=TELEGRAM_TOKEN), 'нет ключа "homeworks"'
        )
        raise Exception('нет ключа "homeworks"')
    if type(response.get('homeworks')) != list:
        raise TypeError()


def parse_status(homework):
    """извлечение из информации о конкретной домашней работе её статус."""
    homework_name = homework.get('homework_name')
    if homework_name is None:
        logger.error('нет ключа "homework_name"')
        send_message(
            telegram.Bot(token=TELEGRAM_TOKEN), 'нет ключа "homework_name"'
        )
        raise Exception('нет ключа "homework_name"')
    verdict = homework.get('status')
    if verdict not in HOMEWORK_VERDICTS:
        logger.error('неизвестный вердикт')
        send_message(
            telegram.Bot(token=TELEGRAM_TOKEN), 'неизвестный вердикт"'
        )
        raise Exception('неизвестный вердикт')
    else:
        verdict = HOMEWORK_VERDICTS.get(verdict)
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def main():
    """Основная логика работы бота."""
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    dt = DT.datetime.now() - DT.timedelta(days=30)
    timestamp = int(dt.replace(tzinfo=DT.timezone.utc).timestamp())
    check_tokens()
    old_status = None
    while True:
        try:
            answer = get_api_answer(timestamp)
            check_response(answer)
            new_status = parse_status(answer.get('homeworks')[0])
            if old_status != new_status:
                send_message(bot, new_status)
                old_status = new_status
            else:
                logger.debug('нет нового вердикта')

        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            logger.error(message)
        time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    main()
