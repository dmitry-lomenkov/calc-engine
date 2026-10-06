FROM python:3.12-slim

WORKDIR /app

# Системные зависимости для сборки pyswisseph
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Эфемериды Swiss Ephemeris (диапазон 1800–2400) кладутся в app/ephe.
# Файлы .se1 не хранятся в git (см. .gitignore) — их тянет скрипт на Шаге 2.
COPY app ./app

EXPOSE 8130
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8130"]
