from langchain_ollama import ChatOllama
# ------Загрузка моделей------
# Модель для диалогов (быстрая)
llm = ChatOllama(
    model="mistral",
    temperature=0.3,          # ниже → более предсказуемые ответы (0.0–0.5 хорошо для инструкций)
    top_p=0.9,                # ограничивает набор токенов по вероятности
    num_predict=512           # максимальная длина ответа (токены)
)
# Модель для анализа фото (мультимодальная)
llm_llava = ChatOllama(model="llava:7b", temperature=0.0)
