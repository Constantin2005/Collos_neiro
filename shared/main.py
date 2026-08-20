import asyncio
from shared.create_graph import app
from shared.states_class import AgentState, system_prompt



async def main():

    initial_state: AgentState = {
        "messages": [],
        "user_input": None,
        "input_type": "text",
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

    final_state = await app.ainvoke(initial_state)


if __name__ == "__main__":
    asyncio.run(main())
