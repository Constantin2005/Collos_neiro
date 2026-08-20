FROM python:3.14-slim

WORKDIR /app

# Установка системных зависимостей для OpenCV (исправленный пакет)
RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY shared/ /app/shared/
COPY api/api_start.py /app/

RUN touch /app/shared/__init__.py

EXPOSE 8000

CMD ["uvicorn", "api_start:fastapi_app", "--host", "0.0.0.0", "--port", "8000"]
