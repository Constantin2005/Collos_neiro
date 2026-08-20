import asyncio
import json
import os
import sys
import traceback
from aio_pika.abc import AbstractIncomingMessage

results_store = {}
# --- Отложенный импорт графа ---
# Импортируем только после того, как RabbitMQ будет готов
def import_graph():
    from shared.create_graph import app
    from shared.state_builder import build_state
    from shared.broker import get_connection, publish_result
    return app, build_state, get_connection, publish_result

# --- Вспомогательные функции ---
async def wait_for_rabbitmq(retries=20, delay=5):
    for attempt in range(1, retries + 1):
        try:
            # Пробуем подключиться к RabbitMQ без импорта графа
            from aio_pika import connect_robust
            connection = await connect_robust(os.environ.get("RABBITMQ_URL", "amqp://guest:guest@rabbitmq/"))
            await connection.close()
            print(f"✅ RabbitMQ готов (попытка {attempt})")
            return True
        except Exception as e:
            print(f"⏳ Ожидание RabbitMQ... ({attempt}/{retries}), ошибка: {e}")
            await asyncio.sleep(delay)
    return False

async def process_message(message: AbstractIncomingMessage):
    async with message.process():
        try:
            data = json.loads(message.body.decode())
            request_id = data.get("request_id")
            req_type = data.get("type")
            print(f"📩 Получено задание {request_id}, тип: {req_type}")

            # Импортируем граф внутри обработки (но он уже будет импортирован после подключения)
            app, build_state, get_connection, publish_result = import_graph()
            initial_state = build_state(data)
            final_state = await app.ainvoke(initial_state)

            last_message = final_state.get("messages", [])[-1] if final_state.get("messages") else None
            result_content = last_message.content if last_message else "Не удалось получить ответ"

            results_store[request_id] = result_content

            await publish_result({
                "request_id": request_id,
                "status": "completed",
                "result": result_content,
            })
            print(f"✅ Задание {request_id} обработано")
        except Exception as e:
            error_msg = str(e)
            request_id = data.get("request_id") if 'data' in locals() else None
            print(f"❌ Ошибка обработки задания {request_id}: {error_msg}")
            traceback.print_exc()
            if request_id:
                results_store[request_id] = f"Ошибка: {error_msg}"
                await publish_result({
                    "request_id": request_id,
                    "status": "error",
                    "error": error_msg,
                })

async def consume_tasks():
    print("🔍 Начало работы consumer")
    print(f"🔍 RABBITMQ_URL: {os.environ.get('RABBITMQ_URL', 'не установлена')}")

    if not await wait_for_rabbitmq():
        print("❌ Не удалось подключиться к RabbitMQ после всех попыток")
        return

    # Теперь, когда RabbitMQ готов, импортируем граф (это может занять время)
    print("🔍 Импортируем граф...")
    try:
        app, build_state, get_connection, publish_result = import_graph()
        print("✅ Граф успешно импортирован")
    except Exception as e:
        print(f"❌ Ошибка импорта графа: {e}")
        traceback.print_exc()
        return

    # Подключаемся к RabbitMQ для прослушивания
    try:
        connection = await get_connection()
        print("✅ Соединение с RabbitMQ установлено")
        channel = await connection.channel()
        print("✅ Канал создан")
        queue = await channel.declare_queue("tasks", durable=True)
        print("✅ Очередь 'tasks' объявлена")
        await queue.consume(process_message)
        print(" [*] Consumer запущен. Ожидание задач. Для выхода Ctrl+C.")
        await asyncio.Future()
    except Exception as e:
        print(f"❌ Ошибка при инициализации consumer: {e}")
        traceback.print_exc()
        raise

# --- Точка входа ---
if __name__ == "__main__":
    try:
        asyncio.run(consume_tasks())
    except KeyboardInterrupt:
        print(" Consumer остановлен пользователем")
    except Exception as e:
        print("❌ Критическая ошибка в consumer:")
        traceback.print_exc()
        sys.exit(1)
