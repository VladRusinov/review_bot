[![Typing SVG align="center"](https://readme-typing-svg.herokuapp.com?color=%2336BCF7&lines=HOMEWORK+BOT)](https://git.io/typing-svg)
## О проекте
проект homework_bot реализует телеграм бота который отправляет сообщения с информацией о ревью проекта.

## Как запустить проект:

Клонировать репозиторий и перейти в него в командной строке:

```
git clone https://github.com/VladRusinov/homework_bot.git
```
Cоздать и активировать виртуальное окружение:

```
python3 -m venv env
```

```
source env/bin/activate
```

Установить зависимости из файла requirements.txt:

```
python3 -m pip install --upgrade pip
```

```
pip install -r requirements.txt
```

Создать и заполнить файл .env.

Запустить бота:

```
python homework.py
```


## как заполнить .env:
```
PRACTICUM_TOKEN=ваш practicum token
TELEGRAM_TOKEN=telegram token
TELEGRAM_CHAT_ID=id чата
