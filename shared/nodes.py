from cv2.cuda import printCudaDeviceInfo
from shared.states_class import AgentState
from langchain_core.messages import SystemMessage, HumanMessage, BaseMessage, AIMessage
from abc import ABC, abstractmethod
from shared.models import llm, llm_llava

import json
import re

from shared.yolo_node import analyze_image_sync
import asyncio # Асинхронное программирование (для запуска синхронного кода в executor).

def user_input_node(state: AgentState) -> dict:
    print(f" user_input_node")
    # Берём ввод из состояния (уже должен быть передан через API)
    person_input = state.get("text_content") or ""
    # Если ничего нет, возможно, это ошибка, но мы просто возвращаем пустую строку
    return {
        "text_content": person_input,
        "should_continue": True  # чтобы граф не завершился
    }
def determinant_node(state: AgentState) -> dict:  # данный узел определяет тип сообщения, и подготавливает фото
    print(f" determinant_node") # строка для отладки

    person_input = state["text_content"] or "" # " or "" необходимо для обработки None"
    if person_input.lower().endswith(("jpg",".jpeg",".png", ".bmp")):
        print(f"Загружаю фото: {person_input}")
        try:
            import base64
            with open(person_input, "rb") as f:
                img_bytes=f.read()
            b64 = base64.b64encode(img_bytes).decode()
            ext = person_input.split('.')[-1].lower()
            mime = f"image/{ext}"
            image_data = f"data:{mime};base64,{b64}"
        except Exception as e:
            return {
                "messages": [SystemMessage(content=f"X ошибка чтоения файла: {e}")],
                "should_continue": False
            }
        return {
            "messages": [HumanMessage(content=person_input)],
            "input_type": "image",
            "user_input": {"type": "image", "image": image_data},
            "image_data": image_data,
            "image_format": "base64",
            "should_continue": True
        }
    else:
        # Обычный текст
        print(f"📝 Получен текст: {person_input}")
        return{
            "messages": [HumanMessage(content=person_input)],
            "input_type": "text",
            "user_input": {"type": "text", "content": person_input},
            "text_content": person_input,
            "should_continue": True
        }

# Создадим стртегию через словарь
class text_answer():
    def send_request(self,state: AgentState) -> dict:
        print(f"📝 Обрабатываю текст")


        response = llm.invoke(state["messages"])
        print(f"ИИ: {response.content}")
        new_messages = state["messages"] + [AIMessage(content=response.content)]
        return {"messages": new_messages,
        "should_continue": False}
class image_answer():
    def send_request(self,state: AgentState) -> dict:
        print(f"Обрабатываю изображение")
        # Берём данные из ссостояния
        image_data = state.get("image_data")
        image_format = state.get("image_format", "base64")

        if not image_data:
            error_msg = "Не удалось загрузить изображение для анализа!"
            print(error_msg)
            new_messages = state["messages"] + [AIMessage(content=error_msg)]
            return {
                "messages": new_messages,
                "should_continue": False
            }
        else:
            # Нейросеть реагирует на загруженное изображение, получая системное уведомление о загрузке фото
            response = llm.invoke(state["messages"])
            print(f"ИИ: {response.content}")
            new_messages = state["messages"] + [AIMessage(content=response.content)]
            # Сохраняем ответ модели
            new_messages = new_messages + [AIMessage(content=response.content)]
            return {
                "messages": new_messages,
                "should_continue": True
            }

strategies  = {
    "text": text_answer(),
    "image": image_answer(),
}
# функция, выюирающая стратегию запроса-ответа нейронки
# Используется отдельно,что бы сохранять принципы разделения задач узлов графа
def route_strategy_node(state: AgentState) -> dict: # данный узел выбирает стратегию
    input_type = state.get("input_type", "text")  # значение по умолчанию
    strategy = strategies.get(input_type)

    if strategy is None:
        # Если тип не поддерживается
        return {
            "messages": [SystemMessage(content="❌ Неизвестный тип сообщения.")],
            "should_continue": False
        }
    # Вызываем стратегию
    return strategy.send_request(state)

# Ассинхронный узел для Yollo запросов
async def request_yolo(state: AgentState) -> dict:
    print(f"📸 Запрашиваю YOLO")
    image_data = state.get("image_data")
    image_format = state.get("image_format")
    # Проверяем наличие данных
    if not image_data:
        return {
            "messages": [AIMessage(content="❌ Нет данных изображения")],
            "should_continue": False
        }
    if not image_format:
        return {
            "messages": [AIMessage(content="❌ Неизвестный формат изображения")],
            "should_continue": False
        }

    loop = asyncio.get_event_loop()
    try:
        # Запускаем синхронную функцию в executor
        # Передаём аргументы как именованные или через partial (чтобы избежать проблем с типами)
        result = await loop.run_in_executor(
            None,
            analyze_image_sync,
            image_data,   # type: ignore[arg-type]  # можно добавить для подавления, но лучше убедиться, что типы совпадают
            image_format  # теперь точно str
        )
    except Exception as e:
        return {
            "messages": [AIMessage(content=f"❌ Ошибка анализа: {e}")],
            "should_continue": False
        }

    # Возвращаем обновление состояния
    return {
        "messages": [SystemMessage(content=result["message_text"])],
        "detected_ingredients": result["detected_ingredients"],
        "calibration_objects": result["calibration_objects"],
        "confidences": result["confidences"],
        "should_continue": True
    }

async def llava_analysis_node(state: AgentState) -> dict:
    """
        Узел для анализа фото с помощью LLaVA и сравнения с данными YOLO.
        Определяет, есть ли на фото ингредиенты, не обнаруженные YOLO.
    """
    print("🔍 LLaVA анализирует фото...")

    # 1. Получаем изображение
    raw_image = state.get("image_data")
    if not raw_image:
        return {
            "messages": [AIMessage(content="❌ Нет данных изображения")],
            "should_continue": False,
            "need_more_info": False
        }

    # Очищаем префикс base64, если есть
    if raw_image.startswith("data:image"):
        image_base64 = raw_image.split(",", 1)[1]
    else:
        image_base64 = raw_image
    # 2. Данные от YOLO
    yolo_ingredients = state.get("detected_ingredients") or []
    confidences = state.get("confidences") or {}

    # 3. Формируем промпт для LLaVA
    prompt = (
        f"Ты — эксперт по анализу блюд. Твоя задача — сравнить то, что ты видишь на фото, с переданным списком ингредиентов от YOLO: {yolo_ingredients}.\n"
        f"Если на фото есть дополнительные ингредиенты (особенно соусы, заправки, приправы, масла), которых нет в списке, ты должен:\n"
        f"  - перечислить их в поле 'missing_ingredients'.\n"
        f"  - задать уточняющий вопрос в поле 'question'.\n"
        f"Если дополнительных ингредиентов нет, ты ОБЯЗАН:\n"
        f"  - вернуть пустой список 'missing_ingredients': []\n"
        f"  - вернуть пустую строку 'question': \"\"\n"
        f"НЕ ЗАДАВАЙ ВОПРОС, ЕСЛИ НЕТ ПРОПУЩЕННЫХ ИНГРЕДИЕНТОВ.\n"
        f"Отвечай строго в формате JSON с двумя полями: 'missing_ingredients' (список строк) и 'question' (строка).\n"
        f"Пример правильного ответа (когда всё совпадает):\n"
        f'{{"missing_ingredients": [], "question": ""}}\n'
        f"Пример правильного ответа (когда есть пропуски):\n"
        f'{{"missing_ingredients": ["соус песто", "пармезан"], "question": "Я вижу на фото соус песто и сыр пармезан. Подтвердите, пожалуйста, эти ингредиенты."}}\n'
        f"Никакого другого текста, только JSON."
    )

    system = SystemMessage(
        content="Ты — система визуального анализа. Отвечай только JSON."
    )

    user_msg = HumanMessage(
        content=[
            {"type": "text", "text": prompt},
            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}}
        ]
    )

    # 4. Вызов LLaVA
    try:
        response = llm_llava.invoke([system, user_msg])
        raw_content = response.content
        print("LLaVA сырой ответ:", raw_content)

        # Извлекаем JSON из ответа (на случай, если модель добавила пояснения)
        json_match = re.search(r'\{.*\}', raw_content, re.DOTALL)
        if json_match:
            json_str = json_match.group()
            data = json.loads(json_str)
            missing = data.get("missing_ingredients", [])
            question = data.get("question", "")
        else:
            raise ValueError("JSON не найден в ответе LLaVA")
    except Exception as e:
        print(f"Ошибка при работе с LLaVA: {e}")
        #  считаем, что пропусков нет, чтобы не останавливать процесс
        missing = []
        question = ""

    # 5. Принимаем решение
    if missing:
        # Есть пропущенные ингредиенты -> задаём уточняющий вопрос
        user_question = f"Я вижу на фото дополнительные ингредиенты: {', '.join(missing)}. {question if question else 'Уточните, пожалуйста, что именно входит в блюдо.'}"
        new_messages = state["messages"] + [AIMessage(content=user_question)]
        return {
            "messages": new_messages,
            "need_more_info": True,
            "should_continue": True,
            "llava_missing": missing  # сохраним для логики
        }
    else:
       # Всё совпадает — продолжаем
        return {
            "need_more_info": False,
            "should_continue": True
        }

# ------ Условные узлы ------
def if_roude_node(state: AgentState) -> str:
    string_should_continue = str(state.get("should_continue"))
    return string_should_continue
def if_missing_ingredients(state: AgentState) -> str:
    if state.get("need_more_info"):
        return "yes"
    return "no"
