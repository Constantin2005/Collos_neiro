from langgraph.graph import StateGraph, START, END
from shared.nodes import *
from shared.states_class import AgentState

# -------------- Создаём граф --------------
graph = StateGraph(AgentState)

# Добавление узлов
graph.add_node("user_input_node", user_input_node)
graph.add_node("determinant_node", determinant_node)
graph.add_node("route_strategy_node",route_strategy_node)
graph.add_node("request_yolo",request_yolo )
graph.add_node("llava_analysis_node", llava_analysis_node)


# -------------- Строим рёбра --------------
graph.add_edge(START, "user_input_node")
graph.add_edge("user_input_node", "determinant_node")
graph.add_edge("determinant_node", "route_strategy_node")
graph.add_conditional_edges(
    "route_strategy_node",
    if_roude_node,
    {
        "False": "user_input_node",
        "True": "request_yolo"
    }
)
graph.add_edge("request_yolo", "llava_analysis_node")
#graph.add_edge("llava_analysis_node", END)
graph.add_conditional_edges("llava_analysis_node",
    if_missing_ingredients,
    {
        "yes": "user_input_node",
        "no": END
    }
)

app = graph.compile()
