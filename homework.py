"""Бот для уведомления о статусе домашней работы в Telegram."""

import time
import logging
from logging import StreamHandler
from sys import stdout
from http import HTTPStatus

import requests
import telegram


import config

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
        (config.PRACTICUM_TOKEN, 'PRACTICUM_TOKEN'),
        (config.TELEGRAM_TOKEN, 'TELEGRAM_TOKEN'),
        (config.TELEGRAM_CHAT_ID, 'TELEGRAM_CHAT_ID'),
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
        bot.send_message(chat_id=config.TELEGRAM_CHAT_ID, text=message)
        logger.debug(f'Бот отправил сообщение: {message}')
    except Exception as error:
        logger.error(f'Сообщение не отправлено! {error}')


def get_api_answer(timestamp):
    """Получение ответа от API."""
    payload = {'from_date': timestamp}
    try:
        response = requests.get(
            config.ENDPOINT, headers=config.HEADERS, params=payload)
    except requests.RequestException as error:
        logger.error(f'Не удалось выполнить подключение к API! {error}')
    if response.status_code != HTTPStatus.OK:
        logger.error(f'Эндпоинт {config.ENDPOINT} недоступен. '
                     f'Код ответа API: {response.status_code}')
        raise Exception(f'Эндпоинт {config.ENDPOINT} недоступен. '
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
    if homework['status'] in config.HOMEWORK_VERDICTS:
        verdict = config.HOMEWORK_VERDICTS[homework['status']]
        return f'Изменился статус проверки работы "{homework_name}". {verdict}'
    else:
        logger.error('Статус домашней работы не соответствует документации')
        raise Exception('Статус домашней работы не соответствует документации')


def main():
    """Основная логика работы бота."""
    check_tokens()
    bot = telegram.Bot(token=config.TELEGRAM_TOKEN)
    timestamp = int(time.time())
    # переменная для обозначения начального статуса домашки
    status_before = ''
    # пременная-флаг, указывает отправлено ли сообщение об ошибке
    message_have_sent = False

    while True:
        send_message(bot, 'HI!')
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
        time.sleep(config.RETRY_PERIOD)


if __name__ == '__main__':
    main()
