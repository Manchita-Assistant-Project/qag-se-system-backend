import re
import functools

import app.agent.tools as tools
from app.agent.state import Story
from app.agent.utils import agent_node, agent_w_tools_node
from app.agent.agents import single_tools_agent

from langgraph.prebuilt import ToolNode
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage

# Funtools
single_tools_node = functools.partial(agent_node, agent=single_tools_agent, name="Single Tools")
# chooser_node = functools.partial(agent_node, agent=qanda_chooser_agent, name="QandA Chooser")

# character_node = functools.partial(agent_w_tools_node, agent=character_agent, name="Character")

# single_tools_tool_node = ToolNode(single_tools)
# chooser_tool_node = ToolNode([tools.qanda_chooser])

def single_tools_tool_node(state): 
    user_message = state["messages"][0]
    ai_message = state["messages"][-1]
    thread_id = state["thread_id"]
    last_question = state["last_question"] if "last_question" in state else None
    tool_call = ai_message.additional_kwargs["tool_calls"][0]["function"]["name"]
    tool_call_id = ai_message.additional_kwargs["tool_calls"][0]["id"] 

    db_id_chroma = state["db_chroma"]
    db_id_sqlite = state["db_sqlite"]

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
        result = tools.points_retrieval(thread_id, db_id_sqlite)
        print(f"Result from points_retrieval: {result}")

    elif tool_call == "rag_search":
        print('RAG SEARCH')
        result = tools.rag_search(f"{user_message.content} ({ai_message.tool_calls[0]['args']['query']})", db_id_chroma)
        print(f"Result from rag_search: {result}")

    elif tool_call == "feedback_provider":
        result = tools.feedback_provider(last_question, db_id_sqlite)
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

def chooser_tool_node(state):
    ai_message = state["messages"][-1]
    tool_call = ai_message.additional_kwargs["tool_calls"][0]["function"]["name"]
    tool_call_id = ai_message.additional_kwargs["tool_calls"][0]["id"]
    
    db_id = state["db_chroma"]
    
    question = tools.qanda_chooser("simple_quiz", db_id)
    choices_string = ''
    for key, value in question['choices'].items():
        choices_string += f"{key}: {value}\n"
        
    question_string = f"{question['question']}\n{choices_string}"
    tool_result = ToolMessage(content=question_string, name=tool_call, tool_call_id=tool_call_id)
    
    return {"messages": [tool_result], "last_question": question["question"]}

def human_interaction(state):
    pass

def evaluation_tool_node(state):
    """
    Evaluates the user's response.
    """
    last_message = state["messages"][-1].content
    print(f"[EVALUATION_NODE] last_message: {last_message}")
    
    db_id = state["db_chroma"]
    
    game_type = "simple_quiz" if state["from_story"] == False else "story"
    
    evaluation = tools.qanda_evaluation(last_message, game_type, db_id)
        
    print(f"[EVALUATION_NODE] response: {evaluation}")

    return {"messages": [evaluation]}

def points_updater_tool_node(state):
    """
    Takes the current thread_id and updates the points of the user.
    Returns the last message.
    """
    last_message = state["messages"][-1]
    print(f"last_message: {last_message.content}")

    db_id = state["db_sqlite"]

    if "incorrecta" not in (last_message.content).lower():
        tools.points_updater(state["thread_id"], db_id, points=1)
        # print(f"CURRENT POINTS: {tools.points_retrieval(state['thread_id'])}")
        
    # en cualquier caso, aumentar 1 al número de preguntas hechas.
    tools.asked_questions_updater(state["thread_id"], db_id)
    
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
    step = current_story["step"] if "current_story" in state else 1
    
    db_id = state["db_chroma"]
    
    print(f"[NARRATOR_NODE] step: {step} | {type(step)}")

    result, story_name = tools.narrator_tool(current_story_name, step, db_id)
    
    if current_story_name:
        current_story["name"] = story_name if step <= 4 else None
        current_story["step"] = step
        current_story["to_evaluate"] = None
        current_story["character_personality"] = None
    else:
        current_story = Story(
            name=story_name,
            step=1,
            prompt_type="start",
            step_in_step=1,
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

"""
- character_node -> nodo principal al que llega el flujo y tiene los condicionales para desprender el flujo.
- character_first_interaction_node -> primer mensaje y pregunta.
- character_success_or_failure_node -> evaluar respuesta y si es correcta, prompt y END | si es incorrecta y pierde, prompt y END.
- character_lost_life_node -> evaluar respuesta y si es incorrecta, prompts y human_interaction.
- character_loop_interaction_node -> si se evalúa que lo que dijo el usuario en "huma_interaction" no es una posible respuesta, se va a este nodo.
No lo voy a hacer con el agente, solo ifs para condicionales (para el agente toca hacer verificaciones, y esas verificaciones son un if que se puede dejar simple, sin AI).
"""

def character_node(state):
    pass

def character_first_interaction_node(state):
    """
    The first interaction with a character.
    """
    # ai_message = state["messages"][-1]
    # tool_call = ai_message.additional_kwargs["tool_calls"][0]["function"]["name"]
    # tool_call_id = ai_message.additional_kwargs["tool_calls"][0]["id"]

    last_human_message = state["messages"][-1].content
    narrator_message = last_human_message

    db_id = state["db_chroma"]
    current_story = state["current_story"]

    result, personality, question = tools.character_first_interaction(current_story, db_id)
    
    response = f"{narrator_message}\n\n{result}"
    
    current_story["to_evaluate"] = question
    current_story["character_personality"] = personality
    
    # tool_result = ToolMessage(content=response, name=tool_call, tool_call_id=tool_call_id)
    
    return { "messages": [response], "current_story": current_story, "from_story": True }

def character_life_lost_node(state):
    current_story = state["current_story"]    
    
    last_message = state["messages"][-1].content
    current_lives = int(last_message.split("|||")[0])
    
    response = tools.character_life_lost(current_story, current_lives)[0]

    return { "messages": [response], "from_story": True }

def character_success_or_failure_node(state):
    db_id = state["db_chroma"]
    
    current_story = state["current_story"]
    step = current_story["step"]
    
    last_message = state["messages"][-1].content
    
    current_lives = int(last_message.split("|||")[0])
    
    response = tools.character_success_or_failure(current_story, current_lives, db_id)
    
    if current_lives == 0: # si el usuario se queda sin vidas, se reinicia el juego desde el principio.
        current_story["name"] = None
        current_story["step"] = 0
        current_story["to_evaluate"] = None
        current_story["character_personality"] = None
    else:
        current_story["step"] = step + 1

    print(f"[CHARACTER SUCCESS OR FAILURE NODE] step: {current_story['step']}")
    current_story["step_in_step"] = 1
    return { "messages": [response], "current_story": current_story, "from_story": False } # se reinicia también from_story
                                                                                           # por por si el usuario quiere
                                                                                           # preguntas normales u otra cosa
                                                                                           # en lugar de seguir con el juego.

def character_loop_interaction_node(state):
    current_story = state["current_story"]    
    
    last_message = state["messages"][-1].content
    
    response = tools.character_loop_interaction(current_story, last_message)

    return { "messages": [response], "from_story": True }

def response_classifier_node(state):
    # DEBE RETORNAR STEP_IN_STEP == 4 SI ES INTERACCIÓN,
    # DEBE RETORNAR STEP_IN_STEP == 2 SI ES RESPUESTA.
    
    ai_message = state["messages"][-2]
    # print(f"[RESPONSE CLASSIFIER NODE] ai_message: {ai_message} - {type(ai_message) == ToolMessage}")
    tool_call = ai_message.name if type(ai_message) == ToolMessage else None
    # print(f"[RESPONSE CLASSIFIER NODE] tool_call: {tool_call}")
    last_message = state["messages"][-1].content
    
    if tool_call == None:
        db_id = state["db_chroma"]
        current_story = state["current_story"]
        question = current_story["to_evaluate"]
        
        opinion = tools.response_classifier(question, last_message, db_id)
        print(f"[RESPONSE CLASSIFIER NODE] opinion: {opinion}")
        if opinion == True:
            current_story["step_in_step"] = 2 # para que esté listo para el nodo de lives lost.
        else:
            current_story["step_in_step"] = 4
    else:
        return { "messages": [last_message] }
    
    return { "messages": [last_message], "current_story": current_story, "from_story": True }

def lives_updater_tool_node(state):
    """
    Takes the current thread_id and updates the lives of the user.
    Returns the last message.
    """
    last_message = state["messages"][-1]
    db_id = state["db_sqlite"]
    current_story = state["current_story"]
    # step = state["step"]
    # question = state["to_evaluate"]
    step = current_story["step"]
    question = current_story["to_evaluate"]
    from_story = True
    print(f"[LIVES UPDATER NODE] last_message: {last_message.content}")

    lost_live = False
    if "incorrecta" in (last_message.content).lower():
        tools.lives_updater(state["thread_id"], db_id)
        lost_live = True
        
    current_lives, success = tools.lives_retrieval(state["thread_id"], db_id, current_story, lost_live)
    # response, current_lives, success = tools.lives_retrieval(state["thread_id"], current_story, lost_live)
    print(f"[LIVES UPDATER NODE] response: {current_lives} - {success}")
    
    if current_lives <= 0: # si el usuario se queda sin vidas, se reinicia el juego desde el principio.
        #step = 0
        #from_story = False
        tools.lives_updater(state["thread_id"], db_id, reset=True)
        #current_story["name"] = None
    # elif success == True: # si hubo success en la pregunta
        # response += '\n\n¡Escribe "Sigue!" para continuar con la historia!'
        # from_story = False # esto es por si el usuario quiere preguntas normales u otra cosa en lugar de seguir con el juego
    
    # current_story["step"] = step
    # current_story["prompt_type"] = "evaluation"
    # current_story["to_evaluate"] = question
    
    current_story["step_in_step"] = 2 if current_lives > 0 and success == False else 3
    
    return { "messages": [f"{current_lives}|||{success}"], "current_story": current_story }
