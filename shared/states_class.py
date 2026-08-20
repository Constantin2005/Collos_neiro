from langgraph.graph import StateGraph, START, END
from typing import TypedDict, List, Optional, Annotated, Literal
from langgraph.graph.message import add_messages
from langchain_core.messages import SystemMessage, HumanMessage, BaseMessage, AIMessage

system_prompt = SystemMessage(
    content=(
        "Ты — дружелюбный помощник по анализу питания.\n"
        "Ты - часть мультимодальной системы, и ты отвечаешь на вопросы пользователя, называешь стадии работы системы."
        "Твоя задача — приветствовать пользователя, поддерживать беседу и предлагать загрузить фото блюда для расчёта калорий.\n"
        "Правила:\n"
        "1. Всегда начинай диалог с приветствия.\n"
        "2. После каждого ответа предлагай загрузить фото еды.\n"
        "3. Если пользователь загружет фото, ответь, что сейчас проанализируешь и выдашь ответ. Система всё сделает.\n"
        "4. Отвечай кратко, вежливо и по делу.\n"
        "5. Если пользователь спрашивает о чём-то, не связанном с едой, вежливо направляй его к теме питания.\n"
        "Пример твоего ответа: 'Здравствуйте! Чем могу помочь? Если хотите узнать калорийность блюда, просто загрузите фото.'"
    )
)

class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage], add_messages] # История диалога
    user_input: Optional[dict] # то, что передалось от брокера
    messages_llava: Annotated[List[BaseMessage], add_messages] # История для Llava

    input_type: Literal["text", "image"]      # тип входящего сообщения
    text_content: Optional[str] # текст сообщения
    image_path: Optional[str] # путь к фото
    image_data: Optional[str]                 # изображение в base64, ссылка или путь
    image_format: Optional[str]               # формат: "url", "base64", "file"
    confidences: Optional[dict]   # {ингредиент: уверенность}
    calibration_objects:Optional[list]
    validated_ingredients: Optional[List[str]] # Подтверждённые ингридиенты
    total_calories: Optional[float]
    should_continue: bool
    need_more_info: bool # Нужнен уточняющий вопрос
    detected_ingredients: Optional[List[str]]
