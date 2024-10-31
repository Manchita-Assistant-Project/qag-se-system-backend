import os
import re
import json
import random
import importlib
from IPython.display import Image

from langgraph.prebuilt import ToolNode
from langchain_core.messages import ToolMessage
from langchain_core.runnables import RunnableLambda
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
QS_PATH = os.path.join(base_dir, "generator", "q&as")
JSON_PATH = os.path.join(base_dir, "generator", "q&as", "qs.json")

def load_json(path: str):
    with open(path, 'r', encoding='utf-8') as f:
        content = json.load(f)

    return content['content']

def update_json(path: str, data: list):
    with open(path, 'r') as f:
        json_dict = json.load(f)

    parsed_data = [json.loads(item) for item in data]

    json_dict.update({"content": parsed_data})

    with open(path, 'w', encoding='utf-8') as f:
        json.dump(json_dict, f, ensure_ascii=False, indent=4)

def generate_graph_image(runnable):
    i = runnable.get_graph().draw_mermaid_png()
    with open("app/agent/graph.png", "wb") as png:
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
    
def create_character_agent(llm, tools, systems_message: str, characters: list):
    """
    Creates a character agent.
    """
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                # "{systems_message}. Select one of: {characters}",
                "{systems_message}.",
            ),
            MessagesPlaceholder(variable_name="messages"),
        ]
    )
    # prompt = prompt.partial(systems_message=systems_message, characters=characters)
    prompt = prompt.partial(systems_message=systems_message)
    if tools:
        return prompt | llm.bind_tools(tools, tool_choice="auto")
    else:
        return prompt | llm
    
def agent_node(state, agent, name):
    result = agent.invoke(state)
    return { # adds to messages because of the add_messages operator
        'messages': [result],
    }
    
def agent_w_tools_node(state, agent, name):
    # mensaje de regaño si no se hizo un tool call
    instruction_message = """
    ¡No hiciste un tool call! ¡Haz el respectivo tool call! No generes texto, solo haz el tool call.
    """
    contador_regaño = 0  # Inicializamos un contador para los mensajes de regaño
    
    while True:
        result = agent.invoke(state)

        # verifica si se hizo un tool call
        if hasattr(result, 'additional_kwargs') and ('tool_calls' in result.additional_kwargs):
            # si hubo tool_call, eliminar exactamente el número de mensajes de regaño
            # print(f"MESSAGES: {state['messages']}")

            # Elimina los últimos 'contador_regaño' mensajes de regaño
            while contador_regaño > 0 and state["messages"][-1] == instruction_message:
                state["messages"].pop()
                contador_regaño -= 1  # Decrementa el contador

            break

        # si no hizo el tool call, agrega la instrucción para que lo haga
        state["messages"].append(instruction_message)
        contador_regaño += 1  # Incrementamos el contador por cada iteración sin tool call

        print(f"Waiting for agent {name} to do a tool call...")

    return {
        'messages': [result],
    }

def define_context_string(context: list, game_type: str):
    answer_choice = context["answer"]
    answer_string = ""

    final_evaluation_string = ""
    if game_type == "simple_quiz":    
        if len(answer_choice) == 1:
            answer_string = [context["choices"][choice] for choice in context["choices"].keys() if choice == answer_choice][0]
        elif answer_choice[0].lower() in ['a', 'b', 'c', 'd'] and answer_choice[1] in ['.', ')']:
            answer_string = answer_choice[2:]
        else:
            answer_string = answer_choice
        
        final_evaluation_string = f"PREGUNTA: {context['question']}\n Hay dos respuestas correctas que debes aceptar: \n- La frase/palabra: '{answer_string.lower()}'\n- La letra: '{answer_choice}' en mayúsculas o minúsculas"
    elif game_type == "story":
        answer_list = [context["choices"][choice] for choice in context["choices"]]
        for each_answer in answer_list:
            answer_string += f"- {each_answer}\n"
            
        final_evaluation_string = f"PREGUNTA: {context['question']} | RESPUESTAS: \n{answer_string.lower()}"
            
    return final_evaluation_string, answer_string.lower()

def summarize_answers(model, context: str):
    prompt_template = """
    Resume en un par de frases el contenido de la siguiente información:
    
    "{context}"    
    """
    prompt = prompt_template.format(context=context)
    response_text = model.invoke(prompt).content
    
    return response_text

def choose_random_story():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    stories_dir = os.path.join(base_dir, "prompts", "stories")
    
    stories = [story for story in os.listdir(stories_dir) if os.path.isdir(os.path.join(stories_dir, story))]

    random_story = random.choice(stories)
    print(f"AVAILABLE STORIES: {stories}\nRANDOM STORY: {random_story}")
    
    return random_story

def load_character_prompt(current_story: str, step: int):
    """
    Carga todos los prompts que cumplen con el patrón {character}_CHARACTER_PROMPT
    desde un módulo dinámicamente.
    Lanza un AttributeError si no se encuentran prompts.
    """
    
    step_to_kind = {
        1: 'FIRST',
        2: 'SECOND',
        3: 'THIRD'
    }
    
    print(f"STEP: {step} - {step_to_kind[step]}")
    
    characters_module_path = f"app.prompts.stories.{current_story}.{current_story}_characters_prompts"
    
    # Importar el módulo dinámicamente
    module = importlib.import_module(characters_module_path)
    
    # Obtener todos los nombres de atributos del módulo
    all_attributes = dir(module)
    
    # Filtrar los prompts que cumplen con el patrón
    formatted_string = f"{step_to_kind[step]}_CHARACTER_PROMPT"
    personality_prompts = [attr for attr in all_attributes if re.match(formatted_string + r'', attr)]
    
    if not personality_prompts:
        raise AttributeError(f"No se encontraron constantes que cumplan con el patrón '{character}_CHARACTER_PROMPT' en el módulo {characters_module_path}")
    
    # Obtener los valores de los atributos filtrados
    loaded_prompts = [getattr(module, attr) for attr in personality_prompts]
    
    return loaded_prompts

def load_character_personalities(current_story: str, step: int):
    """
    Carga todos los prompts que cumplen con el patrón {character}_CHARACTER_PERSONALITY_.*
    desde un módulo dinámicamente.
    Lanza un AttributeError si no se encuentran prompts.
    """
    
    step_to_kind = {
        1: 'FIRST',
        2: 'SECOND',
        3: 'THIRD'
    }
    
    characters_module_path = f"app.prompts.stories.{current_story}.{current_story}_characters_personalities"
    
    # Importar el módulo dinámicamente
    module = importlib.import_module(characters_module_path)
    
    # Obtener todos los nombres de atributos del módulo
    all_attributes = dir(module)
    
    # Filtrar los prompts que cumplen con el patrón
    formatted_string = f"{step_to_kind[step]}_CHARACTER_PERSONALITY"
    personality_prompts = [attr for attr in all_attributes if re.match(formatted_string + r'.*', attr)]
    
    if not personality_prompts:
        raise AttributeError(f"No se encontraron constantes que cumplan con el patrón '{character}_CHARACTER_PERSONALITY_.*' en el módulo {characters_module_path}")
    
    # Obtener los valores de los atributos filtrados
    loaded_prompts = [getattr(module, attr) for attr in personality_prompts]
    
    return loaded_prompts

def find_character_emoji(current_story: str):
    """
    Encuentra el primer atributo que cumple con el patrón 'CHARACTERS_EMOJI' en un módulo.
    """
    characters_module_path = f"app.prompts.stories.{current_story}.{current_story}_characters_personalities"

    module = importlib.import_module(characters_module_path)
    
    all_attributes = dir(module)
    
    emoji_attribute = next((attr for attr in all_attributes if re.search(r'CHARACTERS_EMOJI', attr)), None)
    
    if emoji_attribute:
        emoji_value = getattr(module, emoji_attribute)
        return emoji_value
    else:
        raise AttributeError(f"No se encontró constante con el nombre 'CHARACTERS_EMOJI' en el módulo {characters_module_path}")

def load_character_auxiliar_prompts(current_story: str, step: int):
    """
    Carga todos los prompts que cumplen con el patrón:
    {character}_CHARACTER_{kind}_PROMPT
    donde kind puede ser:
        - SUCCESS
        - LIVES_LOST
        - FAILURE
    desde un módulo dinámicamente.
    Lanza un AttributeError si no se encuentran prompts.
    """
    step_to_kind = {
        1: 'FIRST',
        2: 'SECOND',
        3: 'THIRD'
    }
    
    print(f"STEP: {step} - {step_to_kind[step]}")
    
    characters_module_path = f"app.prompts.stories.{current_story}.{current_story}_characters_prompts"
    
    module = importlib.import_module(characters_module_path)
    
    all_attributes = dir(module)
    
    kinds = ['SUCCESS', 'LIVES_LOST', 'FAILURE', 'LOOP']
    
    loaded_prompts = {}
    
    formatted_string = f"{step_to_kind[step]}_CHARACTER"

    for kind in kinds:        
        formatted_kind_string = f"{formatted_string}_{kind}"
        matching_prompts = [attr for attr in all_attributes if re.match(formatted_kind_string + r'_PROMPT', attr)]
        
        if not matching_prompts:
            raise AttributeError(f"No se encontraron constantes que cumplan con el patrón '{step_to_kind[step]}_CHARACTER_{kind}_PROMPT' en el módulo {characters_module_path}")
        
        for attr in matching_prompts:
            loaded_prompts[kind] = getattr(module, attr)
    
    return loaded_prompts
