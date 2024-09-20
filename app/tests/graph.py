import app.tests.utils as utils
from app.tests.state import State
from app.tests.nodes import single_tools_node, single_tools_tool_node, chooser_tool_node, evaluation_node, evaluation_tool_node, points_updater_tool_node

import uuid
from typing import Literal

from langgraph.utils.runnable import Runnable
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import ToolMessage, HumanMessage, AIMessage


single_use_tools = [
    'rag_search',
    'qanda_generation',
    'points_retrieval',
]

# routing function
def should_use_single_tool(state) -> Literal["chooser", "single_tools", "__end__"]:
    messages = state["messages"]
    last_message = messages[-1]
    
    if last_message.content == "end":
        return END

    # if the LLM makes a tool call, we route to the single tools node
    print(f"last_message.tool_calls: {last_message.tool_calls}")
    # if last_message.tool_calls:
    #     return "single_tools"
    if last_message.tool_calls and last_message.tool_calls[0]['name'] in single_use_tools:
        return "single_tools"
    
    return "chooser"

def should_evaluate_answer(state) -> Literal["evaluation_tools", "points_updater_tools", "__end__"]:
    messages = state["messages"]
    last_message = messages[-1]

    print(f"last_message.tool_calls: {last_message.tool_calls}")
    if last_message.tool_calls[0]["name"] == "points_updater_tools":
        return "points_updater_tools"

    return "evaluation_tools"

# building the graph
workflow = StateGraph(State)

# add nodes
workflow.add_node("simple_interaction", single_tools_node)
workflow.add_node("single_tools", single_tools_tool_node)
workflow.add_node("chooser", chooser_tool_node)
workflow.add_node("evaluation", evaluation_node)
workflow.add_node("evaluation_tools", evaluation_tool_node)
# workflow.add_node("points_updater", points_updater_node)
workflow.add_node("points_updater_tools", points_updater_tool_node)

# add edges
workflow.set_entry_point("simple_interaction")
workflow.add_conditional_edges(
    "simple_interaction",
    should_use_single_tool
)
# workflow.add_conditional_edges(
#     "evaluation",
#     should_evaluate_answer
# )

workflow.add_edge("single_tools", END)
workflow.add_edge("chooser", "evaluation")
workflow.add_edge("evaluation", "evaluation_tools")
# workflow.add_edge("evaluation_tools", "evaluation")
# workflow.add_edge("evaluation", END)
workflow.add_edge("evaluation_tools", "points_updater_tools")
# workflow.add_edge("points_updater", "points_updater_tools")
workflow.add_edge("points_updater_tools", END)

# compile the graph
checkpointer = MemorySaver()
graph = workflow.compile(
    checkpointer=checkpointer,
    interrupt_before=["evaluation"],
)

# generate a graph image
utils.generate_graph_image(graph)

thread_id = str(uuid.uuid4())
thread = {
    "configurable": {
        "thread_id": thread_id,
    }
}

questions = [
    # 'me llamo nicolás'
    'hazme una pregunta!',
    # 'háblame un poco sobre la Resolución No. 051 de junio 24 de 2008',
]

# while True:
for query in questions:
    # query = input("You: ")
    snapshot = graph.get_state(thread)
    graph.update_state(thread, {"thread_id": thread_id})
    for event in graph.stream({"messages": [HumanMessage(content=query)]}, thread, stream_mode="values"):
        event['messages'][-1].pretty_print()
        
    # prueba de memoria (sí tiene)
    # user_answer = input('Answer: ')
    # for event in graph.stream({'messages': [HumanMessage(content=user_answer)]}, thread, stream_mode="values"):
    #     event['messages'][-1].pretty_print()

    if snapshot.next == (): # interruption for the quiz way
        user_answer = input('You: ')
        question = event['messages'][-1].content
        
        combined_input = f"{question}|||{user_answer}"
        print(combined_input)

        # Actualizar el estado con la pregunta y la respuesta combinada para que el nodo 'evaluation' lo reciba
        graph.update_state(
            thread, 
            {
                'messages': [
                    HumanMessage(content=combined_input),
                ]
            }
        )
        print(f"AFTER: {graph.get_state(thread).next}")
        
        for event in graph.stream(None, thread, stream_mode="values"):
            event['messages'][-1].pretty_print()
