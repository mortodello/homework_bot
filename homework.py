"""Бот для уведомления о статусе домашней работы в Telegram."""
import requests
import os
import telegram
import time
import logging

from dotenv import load_dotenv
from logging import StreamHandler
from sys import stdout
from http import HTTPStatus

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

formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
handler = StreamHandler(stdout)
handler.setLevel(logging.DEBUG)
handler.setFormatter(formatter)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logger.addHandler(handler)


def check_tokens():
    """Проверка наличия необходимых данных."""
    REQUIRED_DATA = [
        (PRACTICUM_TOKEN, 'PRACTICUM_TOKEN'),
        (TELEGRAM_TOKEN, 'TELEGRAM_TOKEN'),
        (TELEGRAM_CHAT_ID, 'TELEGRAM_CHAT_ID'),
        ]

    for value, name in REQUIRED_DATA:
        if not value:
            logger.critical(f'Отсутствует обязательная переменная окружения: '
                            f'{name}.'
                            'Программа принудительно остановлена.')
            raise Exception(f'Отсутствует обязательная переменная окружения: '
                            f'{name}.'
                            'Программа принудительно остановлена.')


def send_message(bot, message):
    """Отправка сообщения."""
    try:
        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
        logger.debug(f'Бот отправил сообщение: {message}')
    except Exception as error:
        logger.error(f'Сообщение не отправлено! {error}')


def get_api_answer(timestamp):
    """Получение ответа от API."""
    payload = {'from_date': timestamp}
    try:
        response = requests.get(ENDPOINT, headers=HEADERS, params=payload)
    except requests.RequestException as error:
        logger.error(f'Не удалось выполнить подключение к API! {error}')
    if response.status_code != HTTPStatus.OK:
        logger.error(f'Эндпоинт {ENDPOINT} недоступен. '
                     f'Код ответа API: {response.status_code}')
        raise Exception(f'Эндпоинт {ENDPOINT} недоступен. '
                        f'Код ответа API: {response.status_code}')
    else:
        return response.json()


def check_response(response):
    """Проверяем информацию о домашней работе."""
    if type(response) is not dict:
        logger.error('Ответ API содержит неверный тип данных.')
        raise TypeError('Ответ API содержит неверный тип данных.')
    elif 'homeworks' not in response:
        logger.error('Значение по ключу homeworks не найдено.')
        raise KeyError('Значение по ключу homeworks не найдено.')
    elif type(response['homeworks']) is not list:
        logger.error('Ответ API содержит неверный тип данных.')
        raise TypeError('Ответ API содержит неверный тип данных.')
    else:
        homework = response['homeworks'][0]
        return homework


def parse_status(homework):
    """Возвращаем сообщение о статусе домашнего задания."""
    if 'homework_name' in homework:
        homework_name = homework['homework_name']
    else:
        logger.error('Значения по ключу homework_name не найдено')
        raise KeyError('Значения по ключу homework_name не найдено')
    if homework['status'] in HOMEWORK_VERDICTS:
        verdict = HOMEWORK_VERDICTS[homework['status']]
        return f'Изменился статус проверки работы "{homework_name}". {verdict}'
    else:
        logger.error('Статус домашней работы не соответствует документации')
        raise Exception('Статус домашней работы не соответствует документации')


def main():
    """Основная логика работы бота."""
    check_tokens()
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    timestamp = int(time.time())
    # переменная для обозначения начального статуса домашки
    status_before = ''
    # пременная-флаг, указывает отправлено ли сообщение об ошибке
    message_have_sent = False

    while True:
        try:
            message = parse_status(check_response(get_api_answer(timestamp)))
            if message != status_before:
                status_before = message
                send_message(bot, message)
                message_have_sent = False
            else:
                logger.debug('Статус не обновился.')
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            logger.error(message)
            if not message_have_sent:
                send_message(bot, message)
                message_have_sent = True
        time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    main()
