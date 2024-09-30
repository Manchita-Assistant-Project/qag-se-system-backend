import functools

from app.tests.state import State
from app.tests.utils import agent_node
from app.tests.agents import single_tools_agent, qanda_chooser_agent
from app.tests.tools import single_tools, qanda_chooser, qanda_evaluation, \
                            points_retrieval, points_updater, rag_search, \
                            feedback_provider

from langgraph.prebuilt import ToolNode
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage

# Funtools
single_tools_node = functools.partial(agent_node, agent=single_tools_agent, name="Single Tools")
# chooser_node = functools.partial(agent_node, agent=qanda_chooser_agent, name="QandA Chooser")

# single_tools_tool_node = ToolNode(single_tools)
chooser_tool_node = ToolNode([qanda_chooser])

def single_tools_tool_node(state): 
    # el caso en que falla es cuando va directo a single_tools...
    # creo que es por lo que estoy retornando instantaneamente el mensaje contenido del
    # mensaje solamente... en el de chooser_node, estoy retornando lo que saca el LLM...
    # lo raro es que, cuando se llama solo a single_tools primera, todo bien.
    # el tema es cuando se llama en a veces en medio de la conversación...
    user_message = state["messages"][0]
    ai_message = state["messages"][-1]
    thread_id = state["thread_id"]
    last_question = state["last_question"] if "last_question" in state else None
    tool_call = ai_message.additional_kwargs["tool_calls"][0]["function"]["name"]
    tool_call_id = ai_message.additional_kwargs["tool_calls"][0]["id"] 

    # get last user message
    for each_message in state["messages"][::-1]:
        if isinstance(each_message, HumanMessage):
            user_message = each_message
            break
    
    # get last ai message
    for each_message in state["messages"][::-1]:
        if isinstance(each_message, AIMessage):
            ai_message = each_message
            break
    
    if tool_call == "points_retrieval":
        result = points_retrieval(thread_id)
        print(f"Result from points_retrieval: {result}")

    elif tool_call == "rag_search":
        print('RAG SEARCH')
        result = rag_search(f"{user_message.content} ({ai_message.tool_calls[0]['args']['query']})")
        print(f"Result from rag_search: {result}")

    elif tool_call == "feedback_provider":
        result = feedback_provider(last_question)
        print(f"Result from feedback_provider: {result}")

    else:
        # Si no hay un tool_call válido, devolvemos un mensaje predeterminado
        result = AIMessage(content="Lo siento, no pude procesar tu solicitud.")
        print(f"Fallback result: {result}")
    
    # Asegurarse de que siempre haya un mensaje de respuesta válido
    tool_result = ToolMessage(content=result, name=tool_call, tool_call_id=tool_call_id)
    response = {"messages": [tool_result] if result else {"messages": [user_message]}}
    # response = {"messages": [result]}
    print(f"Final response: {response}")

    return response

def human_interaction(state):
    pass

def evaluation_tool_node(state):
    """
    Evaluates the user's response.
    """
    last_message = state["messages"][-1]
    print(f"[EVALUATION_NODE] last_message: {last_message.content}")

    evaluation = qanda_evaluation(last_message.content)
    print(f"[EVALUATION_NODE] response: {last_message.content}")

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
