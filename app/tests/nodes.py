import functools

from app.tests.state import State
from app.tests.utils import agent_node
from app.tests.tools import single_tools, qanda_chooser, qanda_evaluation, points_retrieval, points_updater
from app.tests.agents import single_tools_agent, qanda_chooser_agent, qanda_evaluation_agent, points_updater_agent

from langgraph.prebuilt import ToolNode

# Funtools
single_tools_node = functools.partial(agent_node, agent=single_tools_agent, name="Single Tools")
chooser_node = functools.partial(agent_node, agent=qanda_chooser_agent, name="QandA Chooser")
evaluation_node = functools.partial(agent_node, agent=qanda_evaluation_agent, name="QandA Evaluation")
points_updater_node = functools.partial(agent_node, agent=points_updater_agent, name="Points Updater")

single_tools_tool_node = ToolNode(single_tools)
chooser_tool_node = ToolNode([qanda_chooser])
evaluation_tool_node = ToolNode([qanda_evaluation])

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
