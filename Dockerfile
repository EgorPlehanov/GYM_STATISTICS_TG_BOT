# Используйте официальный образ Python
FROM python:3.10

# Установите рабочую директорию в контейнере
WORKDIR /app

# Скопируйте файлы приложения в контейнер
COPY . /app

# Установите зависимости через uv
RUN pip install --no-cache-dir uv \
    && uv sync --frozen --no-dev

# Запустите приложение
CMD ["uv", "run", "python", "bot.py"]
