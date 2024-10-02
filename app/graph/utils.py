from langgraph.prebuilt import ToolNode
from langchain_core.messages import ToolMessage
from langchain_core.runnables import RunnableLambda
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder


from IPython.display import Image

def generate_graph_image(runnable):
    i = runnable.get_graph().draw_mermaid_png()
    with open("graph.png", "wb") as png:
        png.write(i)

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

def create_agent(llm, tools, systems_message: str):
    """
    Creates an agent.
    """
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "{systems_message}",
            ),
            MessagesPlaceholder(variable_name="messages"),
        ]
    )
    prompt = prompt.partial(systems_message=systems_message)
    if tools:
        return prompt | llm.bind_tools(tools)
    else:
        return prompt | llm
    
def create_goblin_agent(llm, tools, systems_message: str, goblins: list):
    """
    Creates a goblin agent.
    """
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "{systems_message}. Select one of: {goblins}",
            ),
            MessagesPlaceholder(variable_name="messages"),
        ]
    )
    prompt = prompt.partial(systems_message=systems_message, goblins=goblins)
    if tools:
        return prompt | llm.bind_tools(tools)
    else:
        return prompt | llm
    
def agent_node(state, agent, name):
    result = agent.invoke(state)
    return { # adds to messages because of the add_messages operator
        'messages': [result],
    }
