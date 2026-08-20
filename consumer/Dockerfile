FROM python:3.14-slim

WORKDIR /app

# Та же замена пакета
RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY shared/ /app/shared/
COPY consumer/consumer.py /app/

RUN touch /app/shared/__init__.py

CMD ["python", "/app/consumer.py"]
