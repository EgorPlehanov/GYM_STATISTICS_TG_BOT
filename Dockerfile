# Используйте официальный образ Python
FROM python:3.10

# Установите рабочую директорию в контейнере
WORKDIR /app

# Скопируйте файлы приложения в контейнер
COPY . /app

# Установите зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Запустите приложение
CMD ["python", "bot.py"]