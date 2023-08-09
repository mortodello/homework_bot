"""Дополнительные исключения."""


class EnviromentVariablesError(Exception):
    """Исключение отсутсвия переменных окружения."""

    def __init__(self, text):
        """Текст исключения."""
        self.text = text


class EndpointNotAvailable(Exception):
    """Исключение недоступного эндпоинта."""

    def __init__(self, text):
        """Текст исключения."""
        self.text = text


class StatusError(Exception):
    """Исключение неверного статуса."""

    def __init__(self, text):
        """Текст исключения."""
        self.text = text
