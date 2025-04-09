# Используем официальный образ Python
FROM python:3.11-slim

# Устанавливаем зависимости системы для tkinter и других библиотек
RUN apt-get update && apt-get install -y \
    python3-tk \
    && rm -rf /var/lib/apt/lists/*

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем зависимости и устанавливаем их
COPY requirements.txt .
RUN pip install -r requirements.txt

# Копируем весь проект
COPY . .

# Указываем команду для запуска приложения
CMD ["python", "src/main.py"]
