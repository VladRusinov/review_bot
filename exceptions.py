class NoEnvVarieblesError(Exception):
    """Исключение отсутствия переменных окружения."""

    def __init__(self, message=None):
        if message:
            self.message = message
        else:
            self.message = "Отсутсвуют переменные окружения"

    def __str__(self):
        return self.message


class InvalidStatusCodeError(Exception):
    """Ошибка статуса ответа."""

    def __init__(self, message=None):
        if message:
            self.message = message
        else:
            self.message = "status_code != 200"

    def __str__(self):
        return self.message


class EmptyAPIAnswerError(Exception):
    """Ошибка отсутствия ключа."""

    def __init__(self, message=None):
        if message:
            self.message = message
        else:
            self.message = "неверное значение параметра 'homeworks'"

    def __str__(self):
        return self.message


class RequestError(Exception):
    """Ошибка запроса."""

    def __init__(self, message=None):
        if message:
            self.message = message
        else:
            self.message = "ошибка запроса"

    def __str__(self):
        return self.message
