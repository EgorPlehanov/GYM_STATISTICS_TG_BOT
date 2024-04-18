# Используйте официальный образ Python
FROM python:3.10

# Установите рабочую директорию в контейнере
WORKDIR /app

# Скопируйте файлы приложения в контейнер
COPY . /app

# Копируем entrypoint скрипт
# COPY entrypoint.sh /app/entrypoint.sh

# Даем права на выполнение
RUN chmod +x /app/entrypoint.sh

# Установите зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Устанавливаем entrypoint
ENTRYPOINT ["/app/entrypoint.sh"]

# Запустите приложение
CMD ["python", "bot.py"]