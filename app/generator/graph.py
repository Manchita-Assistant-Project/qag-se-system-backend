from app.generator.oracle import tools, run_oracle, run_tool, router

from IPython.display import Image

from typing import TypedDict, Annotated, List, Union
from langchain_core.agents import AgentAction, AgentFinish
from langchain_core.messages import BaseMessage
from langgraph.graph import StateGraph, END
import operator

class AgentState(TypedDict):
    input: str # input del usuario
    chat_history: list[BaseMessage] # historial de mensajes
    intermediate_steps: Annotated[list[tuple[AgentAction, str]], operator.add] # pasos intermedios -> (acción, mensaje) -> la idea es ir agregando pasos en lugar de reemplazar

graph = StateGraph(AgentState)

graph.add_node("oracle", run_oracle)
# graph.add_node('QandAGenerationAgent', run_tool)
graph.add_node('QandAEvaluationAgent', run_tool)
graph.add_node('InteractionAgent', run_tool)
graph.add_node("qanda_chooser", run_tool)
graph.add_node("final_answer", run_tool)

graph.set_entry_point("oracle")

graph.add_conditional_edges( # a QandAGenerationAgent no debería haber un condicional desde oracle
    source="oracle",
    path=router,
)

for tool_obj in tools:
    if (tool_obj.name != "final_answer" and tool_obj.name != "qanda_chooser"):
        graph.add_edge(
            tool_obj.name,
            "oracle"
        )
    elif (tool_obj.name == "final_answer"):
        graph.add_edge(
            tool_obj.name,
            END
        )
    elif (tool_obj.name == "qanda_chooser"):
        graph.add_edge(
            tool_obj.name,
            "QandAEvaluationAgent"
        )

graph.remove_edge("oracle", "QandAEvaluationAgent")

runnable = graph.compile()

def generate_graph_image():
    i = runnable.get_graph().draw_png()
    with open("graph.png", "wb") as png:
        png.write(i)

generate_graph_image()

out = runnable.invoke({
    "input": "tengo dudas sobre la Resolución No. 051 de junio 24 de 2008",
    "chat_history": []
})

print(out)
