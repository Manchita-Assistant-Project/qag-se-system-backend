import app.tests.utils as utils
from app.tests.tools import single_tools, qanda_chooser, qanda_evaluation
from app.tests.agents import single_tools_agent, qanda_chooser_agent, qanda_evaluation_agent
from app.tests.state import State

import uuid
import json
import functools
from typing import Literal

from langgraph.utils.runnable import Runnable
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_core.messages import ToolMessage, HumanMessage, AIMessage

# Funtools
single_tools_node = functools.partial(utils.agent_node, agent=single_tools_agent, name="Single Tools")
chooser_node = functools.partial(utils.agent_node, agent=qanda_chooser_agent, name="QandA Chooser")
evaluation_node = functools.partial(utils.agent_node, agent=qanda_evaluation_agent, name="QandA Evaluation")

single_tools_tool_node = ToolNode(single_tools)
chooser_tool_node = ToolNode([qanda_chooser])
# human_intermission_tool_node = ToolNode([human_intermission])
evaluation_tool_node = ToolNode([qanda_evaluation])

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
    if last_message.tool_calls and last_message.tool_calls[0]['name'] == 'rag_search':
        return "single_tools"
    
    return "chooser"

# def should_ask_question(state) -> Literal["chooser"]:
#     messages = state["messages"]
#     last_message = messages[-1]

#     # if the LLM makes a tool call, we route to the single tools node
#     print(f"last_message.tool_calls: {last_message.tool_calls}")
#     if last_message.tool_calls[0]['name'] == 'qanda_chooser':
#         return "chooser"


# building the graph
workflow = StateGraph(State)

# add nodes
workflow.add_node("simple_interaction", single_tools_node)
workflow.add_node("single_tools", single_tools_tool_node)
workflow.add_node("chooser", chooser_tool_node)
workflow.add_node("evaluation", evaluation_node)
workflow.add_node("evaluation_tools", evaluation_tool_node)

# add edges
workflow.set_entry_point("simple_interaction")
workflow.add_conditional_edges(
    "simple_interaction",
    should_use_single_tool
)
# workflow.add_conditional_edges(
#     "single_tools",
#     should_ask_question
# )

workflow.add_edge("single_tools", END)
workflow.add_edge("chooser", "evaluation")
workflow.add_edge("evaluation", "evaluation_tools")
workflow.add_edge("evaluation_tools", END)

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
    for event in graph.stream({"messages": [HumanMessage(content=query)]}, thread, stream_mode="values"):
        event['messages'][-1].pretty_print()
        
    # prueba de memoraia (sí tiene)
    # user_answer = input('Answer: ')
    # for event in graph.stream({'messages': [HumanMessage(content=user_answer)]}, thread, stream_mode="values"):
    #     event['messages'][-1].pretty_print()
    
    if snapshot.next != "single_tools":
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
        print(F"AFTER: {graph.get_state(thread).next}")
        
        for event in graph.stream(None, thread, stream_mode="values"):
            event['messages'][-1].pretty_print()

# builder = StateGraph(State)

# builder.add_node("assistant", Assistant(assistant_runnable))
# builder.add_node("single_tools", utils.create_tool_node_with_fallback(single_tools))
# builder.add_node("qanda_chooser", qanda_chooser)
# builder.add_node("qanda_evaluation", qanda_evaluation)

# def route_tools(state: QandAChooserState) -> Literal['single_tools', 'qanda_chooser', 'qanda_evaluation', '__end__']:
#     next_node = tools_condition(state)
    
#     if next_node == END:
#         return END
    
#     ai_message = state['messages'][-1]
    
#     first_tool_call = ai_message.tool_calls[0]
#     if first_tool_call['name'] == 'qanda_evaluation':
#         return 'qanda_evaluation'
#     elif first_tool_call['name'] == 'qanda_chooser':
#         return 'qanda_chooser'
    
#     return 'single_tools'

# builder.add_edge(START, "assistant")
# builder.add_conditional_edges(
#     'assistant',
#     route_tools,
# )
# builder.add_edge('single_tools', 'assistant')
# builder.add_edge('qanda_chooser', 'qanda_evaluation')
# builder.add_edge('qanda_evaluation', 'assistant')

# memory = MemorySaver()
# runnable = builder.compile(
#     checkpointer=memory,
#     # NEW: The graph will always halt before executing the "tools" node.
#     # The user can approve or reject (or even alter the request) before
#     # the assistant continues
#     interrupt_before=["qanda_evaluation"],
# )

       
# utils.generate_graph_image(runnable)

# # Update with the backup file so we can restart from the original place in each section
# thread_id = str(uuid.uuid4())

# thread = {
#     "configurable": {
#         # Checkpoints are accessed by thread_id
#         "thread_id": thread_id,
#     }
# }

# # query = 'háblame un poco sobre la Resolución No. 051 de junio 24 de 2008'
# questions = [
#     'hazme una pregunta!',
#     # 'háblame un poco sobre la Resolución No. 051 de junio 24 de 2008',
# ]

# for query in questions:
#     for event in runnable.stream({"messages": query}, thread, stream_mode="values"):
#         # print(event)
#         event['messages'][-1].pretty_print()
    
#     user_answer = input('Answer: ')
#     question = event['messages'][-1].content

#     runnable.update_state(thread, {'messages': [HumanMessage(content=f"{question}|||{user_answer}")]}, as_node='qanda_evaluation')
#     for event in runnable.stream(None, thread, stream_mode="values"):
#         # print(event)
#         event['messages'][-1].pretty_print()
