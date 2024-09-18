from app.generator.qanda_chooser_agent import qanda_chooser_runnable, QandAChooserAgent
from app.generator.agents_graph import State
from app.generator.assistant import State, Assistant, assistant_runnable, single_tools, loop_tools, loop_tool_names

import json
from typing import Literal

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import tools_condition

from langchain_core.messages import ToolMessage
from langchain_core.runnables import RunnableLambda

from langgraph.prebuilt import ToolNode

builder = StateGraph(State)

def handle_tool_error(state) -> dict:
    error = state.get("error")
    tool_calls = state["messages"][-1].tool_calls
    return {
        "messages": [
            ToolMessage(
                content=f"Error: {repr(error)}\n please fix your mistakes.",
                tool_call_id=tc["id"],
            )
            for tc in tool_calls
        ]
    }

def create_tool_node_with_fallback(tools: list) -> dict:
    return ToolNode(tools).with_fallbacks(
        [RunnableLambda(handle_tool_error)], exception_key="error"
    )
    
def _print_event(event: dict, _printed: set, max_length=1500):
    current_state = event.get("dialog_state")
    if current_state:
        print("Currently in: ", current_state[-1])
    message = event.get("messages")
    if message:
        if isinstance(message, list):
            message = message[-1]
        if message.id not in _printed:
            msg_repr = message.pretty_repr(html=True)
            if len(msg_repr) > max_length:
                msg_repr = msg_repr[:max_length] + " ... (truncated)"
            print(msg_repr)
            _printed.add(message.id)

# NEW: The fetch_user_info node runs first, meaning our assistant can see the user's flight information without
# having to take an action
# builder.add_edge(START, "assistant")
# builder.add_node("assistant", Assistant(assistant_runnable))
# builder.add_node("single_tools", create_tool_node_with_fallback(single_tools))
builder.add_edge(START, "qanda_chooser")

builder.add_node("qanda_chooser", QandAChooserAgent(qanda_chooser_runnable))
builder.add_node(
    "loop_tools", create_tool_node_with_fallback(loop_tools)
)
# builder.add_node("qanda_chooser", create_tool_node_with_fallback([tool for tool in single_tools if tool.name == "qanda_chooser"]))
# Define logic
# builder.add_edge("fetch_user_info", "assistant")

# def route_tools(state: State) -> Literal["qanda_chooser", "loop_tools", "__end__"]:
def route_tools(state: State) -> Literal["loop_tools", "__end__"]:
    next_node = tools_condition(state)
    
    if next_node == END:
        print("No tools invoked. Ending flow.")
        return END

    ai_message = state["messages"][-1]

    first_tool_call = ai_message.tool_calls[0]
    print(f"Tool call found: {first_tool_call['name']}")
    
    if first_tool_call["name"] == "qanda_evaluation":
        print("Proceeding to 'loop_tools' for qanda_evaluation.")
        return "loop_tools"
    
    return "qanda_chooser"


# builder.add_conditional_edges(
#     "assistant",
#     route_tools,
# )
builder.add_conditional_edges(
    "qanda_chooser",
    route_tools,
)
# builder.add_edge("single_tools", "assistant")
builder.add_edge("loop_tools", "qanda_chooser")
builder.add_edge("qanda_chooser", "loop_tools")

memory = MemorySaver()
runnable = builder.compile(
    checkpointer=memory,
    # NEW: The graph will always halt before executing the "tools" node.
    # The user can approve or reject (or even alter the request) before
    # the assistant continues
    interrupt_before=["loop_tools"],
)

from IPython.display import Image

def generate_graph_image():
    i = runnable.get_graph().draw_png()
    with open("graph.png", "wb") as png:
        png.write(i)
        
generate_graph_image()

import shutil
import uuid

# Update with the backup file so we can restart from the original place in each section
thread_id = str(uuid.uuid4())

config = {
    "configurable": {
        # Checkpoints are accessed by thread_id
        "thread_id": thread_id,
    }
}

# query = 'háblame un poco sobre la Resolución No. 051 de junio 24 de 2008'
questions = [
    'hazme una pregunta!',
]

_printed = set()

for query in questions:
    events = runnable.stream(
        {"messages": ("user", query)},
        config,
        stream_mode="values"
    )

    for event in events:
        # print(f"Event: {event['messages']}")
        _print_event(event, _printed)

    snapshot = runnable.get_state(config)
    while snapshot.next:
        print('¡Interrupción detectada! El agente ha hecho una pregunta.')
        user_input = input('Responde la pregunta: ')
        if user_input.strip():
            question = config["configurable"].get("last_question", "")
            formatted_input = f"{question}|||{user_input}"

            # calls_dict = json.loads(event['messages'][-1].content)
            calls_dict = event['messages'][-1]
            print(f"Tool calls: {calls_dict.additional_kwargs}")

            kwargs = calls_dict.additional_kwargs
            # Validar si existe una llamada a la herramienta previamente
            if 'tool_calls' in kwargs:
                tool_call = kwargs['tool_calls'][0]
                # tool_call["function"]["arguments"] = formatted_input
                
                # Invocamos solo si existe una tool_call previa
                result = runnable.invoke(
                    {
                        "messages": [
                            ToolMessage(
                                tool_call_id=tool_call["id"],
                                content=formatted_input
                            )
                        ]
                    },
                    config
                )
            else:
                print("No tool call found. Ending flow.")
                break

        else:
            print("No user response. Ending the flow.")
            break
        
        snapshot = runnable.get_state(config)
