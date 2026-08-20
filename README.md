# 🍽️ Food Analyzer Agent

Мультимодальная система анализа питания на основе **LangGraph**, **YOLO**, **LLaVA** и **Mistral**.  
Позволяет определять ингредиенты на фото, уточнять их у пользователя и рассчитывать калорийность блюда.

---

## 🚀 Возможности

- ✅ Распознавание ингредиентов на фото (YOLO)
- ✅ Визуальный анализ с помощью LLaVA (поиск пропущенных ингредиентов, соусов)
- ✅ Диалоговый агент на Mistral (уточняющие вопросы, общение)
- ✅ Асинхронная обработка через RabbitMQ
- ✅ REST API на FastAPI
- ✅ Контейнеризация Docker / Docker Compose

---

## 🏗️ Архитектура

```mermaid
graph TD
    User[User] --> PHP[PHP Server]
    PHP -->|POST /analyze| API[FastAPI Gateway]
    API -->|generates request_id| Broker[(RabbitMQ)]
    API -->|returns request_id| PHP
    PHP -->|GET /result/{id}| API
    API -->|query result| Store[(Storage)]
    Store -->|result| API
    API -->|result| PHP
    PHP -->|response| User

    Broker -->|task| Consumer[Consumer Worker]
    Consumer -->|executes| Graph[LangGraph]
    Graph -->|YOLO + LLaVA + Mistral| LLM[Ollama]
```

FastAPI – принимает запросы, публикует задачи в очередь, отдаёт результаты.
RabbitMQ – брокер сообщений (очереди tasks и results).
Consumer – воркер, обрабатывает задачи, запускает LangGraph.
LangGraph – агент, объединяет YOLO, LLaVA и Mistral.
Ollama – сервер для локальных LLM (Mistral, LLaVA).

Требования
  Docker и Docker Compose (рекомендуется)
  Python 3.14+ (для локальной разработки)
  Ollama (локально или в контейнере) с моделями:
  mistral
  llava:7b
Установка и запуск
  Клонировать репозиторий
    bash
    git clone https://github.com/ваш_аккаунт/food-analyzer-agent.git
    cd food-analyzer-agent

Настроить переменные окружения
  Скопируйте .env.example в .env и заполните значения:
  cp .env.example .env
  Отредактируйте .env (например, укажите IP вашего компьютера для Ollama).

Запустить через Docker Compose
  docker-compose up -d
Все сервисы поднимутся автоматически:
  API на порту 8000
  RabbitMQ Management на порту 15672
  Consumer (2 реплики)

Загрузить модели в Ollama (если запускаете локально)
Если вы используете локальный Ollama (не в контейнере):
  ollama pull mistral
  ollama pull llava:7b
Если Ollama запущен в контейнере:
  docker exec -it ollama ollama pull mistral
  docker exec -it ollama ollama pull llava:7b

📡 Использование API
Синхронный режим (без очереди)
curl -X POST http://localhost:8000/analyze_sync \
  -H "Content-Type: application/json" \
  -d '{"type":"text","content":"Сколько калорий в яблоке?"}'
Асинхронный режим (с очередью)
  Отправить задание:
  curl -X POST http://localhost:8000/analyze \
    -H "Content-Type: application/json" \
    -d '{"type":"text","content":"Привет"}'
  Ответ: {"request_id":"...","status":"queued"}
  Получить результат:
  curl http://localhost:8000/result/<request_id>
  Если результат ещё не готов – вернётся 404.

Пример с фото (base64)
json
{
  "type": "image",
  "image_base64": "/9j/4AAQSkZJRgABAQEAYABgAAD/..."
}
Фото должно быть закодировано в base64 без префикса data:image/...;base64, (или с ним – система сама добавит, если нужно).

Структура проекта

├── api/                    # FastAPI-приложение
│   ├── Dockerfile
│   └── api_start.py
├── consumer/               # Consumer-воркер
│   ├── Dockerfile
│   └── consumer.py
├── shared/                 # Общие модули
│   ├── broker.py
│   ├── create_graph.py
│   ├── models.py
│   ├── nodes.py
│   ├── state_builder.py
│   ├── states_class.py
│   └── yolo_node.py
├── models/                 # Модели (YOLO, если скачаны)
├── docker-compose.yml
├── .env.example
├── requirements.txt
└── README.md

Переменные окружения (.env)
  Переменная	Описание	Пример
  RABBITMQ_USER	Пользователь RabbitMQ	guest
  RABBITMQ_PASS	Пароль RabbitMQ	guest
  OLLAMA_HOST	Адрес сервера Ollama	http://host.docker.internal:11434

Локальная разработка (без Docker)
Создать виртуальное окружение:

python -m venv venv
source venv/bin/activate  # или venv\Scripts\activate на Windows

Установить зависимости:
pip install -r requirements.txt
Запустить RabbitMQ и Ollama локально.

Запустить API и consumer в отдельных терминалах:

uvicorn api.api_start:fastapi_app --host 0.0.0.0 --port 8000
python consumer/consumer.py

Лицензия
MIT License – свободно для использования, модификации и распространения.

Контакты
Если у вас есть вопросы или предложения – создавайте Issue в репозитории.
