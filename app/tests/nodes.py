import functools

from app.tests.state import State
from app.tests.utils import agent_node
from app.tests.agents import single_tools_agent, qanda_chooser_agent
from app.tests.tools import single_tools, qanda_chooser, qanda_evaluation, points_retrieval, points_updater, rag_search

from langgraph.prebuilt import ToolNode

# Funtools
single_tools_node = functools.partial(agent_node, agent=single_tools_agent, name="Single Tools")
chooser_node = functools.partial(agent_node, agent=qanda_chooser_agent, name="QandA Chooser")

# single_tools_tool_node = ToolNode(single_tools)
chooser_tool_node = ToolNode([qanda_chooser])

def single_tools_tool_node(state):
    user_message = state["messages"][0]
    ai_message = state["messages"][-1]
    thread_id = state["thread_id"]
    tool_call = ai_message.additional_kwargs["tool_calls"][0]["function"]["name"]
    
    if tool_call == "points_retrieval":
        result = points_retrieval(thread_id)
        return {"messages": [result]}
    elif tool_call == "rag_search":
        result = rag_search(user_message.content)
        return {"messages": [result]}
    
    return {"messages": [user_message]}

def evaluation_tool_node(state):
    """
    Evaluates the user's response.
    """
    last_message = state["messages"][-1]
    print(f"last_message: {last_message.content}")

    evaluation = qanda_evaluation(last_message.content)

    return {"messages": [evaluation]}

def points_updater_tool_node(state):
    """
    Takes the current thread_id and updates the points of the user.
    Returns the last message.
    """
    last_message = state["messages"][-1]
    print(f"last_message: {last_message.content}")

    if "incorrecta" not in (last_message.content).lower():
        points_updater(state["thread_id"], points=1)
    
    return {"messages": [last_message]} # retorna el mensaje original.
                                        # esta función no genera mensajes, solo
                                        # actualiza los puntos del usuario.
