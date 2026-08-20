from langchain_core.messages import HumanMessage, SystemMessage
from shared.states_class import AgentState

def build_state(request: dict) -> AgentState:
    req_type = request.get("type", "text")

    state: AgentState = {
        "messages": [],
        "user_input": None,
        "input_type": req_type,
        "text_content": None,
        "image_data": None,
        "image_format": None,
        "messages_llava": [],
        "image_path": None,
        "detected_ingredients": None,
        "confidences": None,
        "calibration_objects": None,
        "validated_ingredients": None,
        "total_calories": None,
        "should_continue": True,
        "need_more_info": False,
    }

    if req_type == "text":
        text = request.get("content", "")
        state["text_content"] = text
        state["user_input"] = {"type": "text", "content": text}
        state["messages"] = [HumanMessage(content=text)]
    elif req_type == "image":
        image_b64 = request.get("image_base64", "")
        if image_b64:
            if not image_b64.startswith("data:image"):
                image_b64 = f"data:image/jpeg;base64,{image_b64}"
            state["image_data"] = image_b64
            state["image_format"] = "base64"
            state["user_input"] = {"type": "image", "image": image_b64}
            state["messages"] = [HumanMessage(content="📸 Загружено фото")]
        else:
            state["should_continue"] = False
            state["messages"] = [SystemMessage(content="Ошибка: нет данных изображения")]
    else:
        state["should_continue"] = False
        state["messages"] = [SystemMessage(content="Неизвестный тип запроса")]

    return state
