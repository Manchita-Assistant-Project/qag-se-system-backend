import re
import functools

from app.graph.state import Story
from app.graph.utils import agent_node, agent_w_tools_node
from app.graph.agents import single_tools_agent, character_agent
import app.graph.tools as tools

from langgraph.prebuilt import ToolNode
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage

# Funtools
single_tools_node = functools.partial(agent_node, agent=single_tools_agent, name="Single Tools")
# chooser_node = functools.partial(agent_node, agent=qanda_chooser_agent, name="QandA Chooser")

character_node = functools.partial(agent_w_tools_node, agent=character_agent, name="Character")

# single_tools_tool_node = ToolNode(single_tools)
chooser_tool_node = ToolNode([tools.qanda_chooser])

def single_tools_tool_node(state): 
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
        result = tools.points_retrieval(thread_id)
        print(f"Result from points_retrieval: {result}")

    elif tool_call == "rag_search":
        print('RAG SEARCH')
        result = tools.rag_search(f"{user_message.content} ({ai_message.tool_calls[0]['args']['query']})")
        print(f"Result from rag_search: {result}")

    elif tool_call == "feedback_provider":
        result = tools.feedback_provider(last_question)
        print(f"Result from feedback_provider: {result}")

    else:
        # si no hay un tool_call válido, devolvemos un mensaje predeterminado
        result = AIMessage(content="Lo siento, no pude procesar tu solicitud.")
        print(f"Fallback result: {result}")
    
    # asegurarse de que siempre haya un mensaje de respuesta válido
    tool_result = ToolMessage(content=result, name=tool_call, tool_call_id=tool_call_id)
    response = {"messages": [tool_result] if result else {"messages": [user_message]}, "from_story": False}

    print(f"Final response: {response}")

    return response

def human_interaction(state):
    pass

def evaluation_tool_node(state):
    """
    Evaluates the user's response.
    """
    last_message = state["messages"][-1].content
    print(f"[EVALUATION_NODE] last_message: {last_message}")
    
    evaluation = tools.qanda_evaluation(last_message)    
        
    print(f"[EVALUATION_NODE] response: {evaluation}")

    return {"messages": [evaluation]}

def points_updater_tool_node(state):
    """
    Takes the current thread_id and updates the points of the user.
    Returns the last message.
    """
    last_message = state["messages"][-1]
    print(f"last_message: {last_message.content}")

    if "incorrecta" not in (last_message.content).lower():
        tools.points_updater(state["thread_id"], points=1)
    
    return {"messages": [last_message], "from_story": False} # retorna el mensaje original.
                                                             # esta función no genera mensajes, solo
                                                             # actualiza los puntos del usuario.

def narrator_node(state):
    """
    Narrates the goblin story.
    """
    ai_message = state["messages"][-1]
    tool_call = ai_message.additional_kwargs["tool_calls"][0]["function"]["name"]
    tool_call_id = ai_message.additional_kwargs["tool_calls"][0]["id"] 
    
    current_story = state["current_story"] if "current_story" in state else None
    
    current_story_name = current_story["name"] if "current_story" in state else None
    
    # step = state["step"] if "step" in state else 0
    step = current_story["step"] if "current_story" in state else 0
    print(f"[NARRATOR_NODE] step: {step} | {type(step)}")

    result, story_name = tools.narrator_tool(current_story_name, step)
    
    if current_story_name:
        current_story["name"] = story_name if step <= 4 else None
        current_story["step"] = step + 1
        current_story["to_evaluate"] = None
        current_story["character_personality"] = None
    else:
        current_story = Story(
            name=story_name,
            step=step + 1,
            to_evaluate=None,
            character_personality=None
        )

    tool_result = ToolMessage(content=result, name=tool_call, tool_call_id=tool_call_id)
    
    return { "messages": [tool_result], "current_story": current_story }

def verify_tool_call_node(state):
    """
    Verifies if there was a tool call.
    """
    last_message = state["message"][-1]
    was_tool_call = tools.verify_tool_call(last_message)
    
    return { "messages": [last_message.content], "was_tool_call": was_tool_call }

def first_character_node(state):
    """
    Encounters first_character.
    """
    ai_message = state["messages"][-1]
    tool_call = ai_message.additional_kwargs["tool_calls"][0]["function"]["name"]
    tool_call_id = ai_message.additional_kwargs["tool_calls"][0]["id"]

    current_story = state["current_story"]
    narrator_message = state["messages"][-2].content
    
    result, personality, question = tools.first_character(current_story["name"])
    
    response = f"{narrator_message}\n\n{result}"
    
    current_story["step"] = 1
    current_story["to_evaluate"] = question
    current_story["character_personality"] = personality
    
    tool_result = ToolMessage(content=response, name=tool_call, tool_call_id=tool_call_id)
    
    return { "messages": [tool_result], "current_story": current_story, "from_story": True }

def second_character_node(state):
    """
    Encounters second_character.
    """
    ai_message = state["messages"][-1]
    tool_call = ai_message.additional_kwargs["tool_calls"][0]["function"]["name"]
    tool_call_id = ai_message.additional_kwargs["tool_calls"][0]["id"] 
    
    current_story = state["current_story"]
    narrator_message = state["messages"][-2].content
    
    result, personality, question = tools.second_character(current_story["name"])
    
    response = f"{narrator_message}\n\n{result}"
    
    current_story["step"] = 2
    current_story["to_evaluate"] = question
    current_story["character_personality"] = personality
    
    tool_result = ToolMessage(content=response, name=tool_call, tool_call_id=tool_call_id)
    
    return { "messages": [tool_result], "current_story": current_story, "from_story": True }

def third_character_node(state):
    """
    Encounters third_character.
    """
    ai_message = state["messages"][-1]
    tool_call = ai_message.additional_kwargs["tool_calls"][0]["function"]["name"]
    tool_call_id = ai_message.additional_kwargs["tool_calls"][0]["id"] 
    
    current_story = state["current_story"]
    narrator_message = state["messages"][-2].content
    
    result, personality, question = tools.third_character(current_story["name"])
    
    response = f"{narrator_message}\n\n{result}"
    
    current_story["step"] = 3
    current_story["to_evaluate"] = question
    current_story["character_personality"] = personality
    
    tool_result = ToolMessage(content=response, name=tool_call, tool_call_id=tool_call_id)
    
    return { "messages": [tool_result], "current_story": current_story, "from_story": True }

def lifes_updater_tool_node(state):
    """
    Takes the current thread_id and updates the lifes of the user.
    Returns the last message.
    """
    last_message = state["messages"][-1]
    current_story = state["current_story"]
    # step = state["step"]
    # question = state["to_evaluate"]
    step = current_story["step"]
    question = current_story["to_evaluate"]
    from_story = True
    print(f"[LIFES UPDATER NODE] last_message: {last_message.content}")

    lost_live = False
    if "incorrecta" in (last_message.content).lower():
        tools.lifes_updater(state["thread_id"])
        lost_live = True
        
    response, current_lifes, kind = tools.lifes_retrieval(state["thread_id"], current_story, lost_live)
    print(f"[LIFES UPDATER NODE] response: {response}")
    
    if current_lifes <= 0: # si el usuario se queda sin vidas, se reinicia el juego desde el principio.
        step = 0
        from_story = False
        tools.lifes_updater(state["thread_id"], reset=True)
        current_story["name"] = None
    elif kind == 1: # si hubo success en la pregunta
        response += '\n\n¡Escribe "Sigue!" para continuar con la historia!'
        from_story = False # esto es por si el usuario quiere preguntas normales u otra cosa en lugar de seguir con el juego
    
    current_story["step"] = step
    current_story["to_evaluate"] = question
    
    return { "messages": [f"{response}|||{current_lifes}"], "current_story": current_story, "from_story": from_story }
