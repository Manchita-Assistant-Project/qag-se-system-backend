import os
import random
import importlib
from typing import Tuple

from langchain_openai import AzureChatOpenAI
from langchain_core.messages import AIMessage
from langchain.prompts import ChatPromptTemplate
from langchain_community.vectorstores import Chroma

import app.config as config
import app.graph.utils as utils
from app.graph.state import Story
import app.database.chroma_utils as chroma_utils
import app.database.sqlite_utils as sqlite_utils
from app.prompts.tools_prompts import QANDA_PROMPT, EVALUATE_PROMPT, \
                                      INTERACTION_PROMPT, \
                                      POINTS_RETRIEVAL_PROMPT, \
                                      FEEDBACK_PROMPT

from dotenv import load_dotenv
os.environ["OPENAI_API_KEY"] = config.OPENAI_API_KEY
os.environ["AZURE_OPENAI_ENDPOINT"] = config.AZURE_OPENAI_ENDPOINT
os.environ["OPENAI_API_TYPE"] = config.OPENAI_API_TYPE
os.environ["OPENAI_API_VERSION"] = config.OPENAI_API_VERSION
os.environ["OPENAI_DEPLOYMENT_NAME"] = config.OPENAI_DEPLOYMENT_NAME
load_dotenv()

embedding_function = chroma_utils.get_embedding_function()
db = Chroma(persist_directory=chroma_utils.CHROMA_PATH, embedding_function=embedding_function)

def qanda_generation() -> str:
    """
    Saves questions and answers to the JSON file.
    """
    query = ""
    json_path = utils.JSON_PATH

    model = AzureChatOpenAI(
        deployment_name=os.environ["OPENAI_DEPLOYMENT_NAME"],
        temperature=0.2
    )

    results = db.similarity_search_with_score(query, k=5)
    
    context_text = "\n\n---\n\n".join([doc.page_content for doc, _score in results])

    prompt_template = ChatPromptTemplate.from_template(QANDA_PROMPT)
    prompt = prompt_template.format(context=context_text)

    response_text = model.invoke(prompt).content

    utils.update_json(json_path, response_text.split('\n\n'))
    return response_text

def qanda_evaluation(input_data: str) -> str:
    """
    Evaluates the given answer to a question.
    """
    json_path = utils.JSON_PATH
    data = utils.load_json(json_path) 

    question, answer = input_data.split('|||')
    print(f"QUESTION: {question} | ANSWER: {answer}")
    
    context = [each_qanda for each_qanda in data[0]['questions'] if each_qanda['question'] == question]
    
    model = AzureChatOpenAI(
        deployment_name=os.environ["OPENAI_DEPLOYMENT_NAME"],
        temperature=0.2
    )
    
    context_string = utils.define_context_string(context)
    print(f"CONTEXT STRING: {context_string}")
    
    answer = answer if answer != '' else "****"
    
    prompt_template = ChatPromptTemplate.from_template(EVALUATE_PROMPT)
    prompt = prompt_template.format(context=context_string, answer=answer, question=question)
    response_text = model.invoke(prompt).content
    
    print(f"RESPONSE: {response_text}")
    return response_text

def rag_search(query: str) -> str:
    """
    Responds when asked about an specific topic about the context.
    """
    print(f"QUERY: {query}")
    model = AzureChatOpenAI(
        deployment_name=os.environ["OPENAI_DEPLOYMENT_NAME"],
        temperature=0
    )
    results = db.similarity_search_with_score(query, k=8)

    context_text = "\n\n---\n\n".join([doc.page_content for doc, _score in results])
    
    prompt_template = ChatPromptTemplate.from_template(INTERACTION_PROMPT)
    prompt = prompt_template.format(context=context_text, query=query)
    
    response_text = model.invoke(prompt).content

    return response_text

def qanda_chooser() -> str: # ¡¡acá falta el tema del modelo, para que retorne frases más bonitas y no solo la pregunta!!
    """
    It does not generate questions.
    Chooses a random question ONLY from the JSON file.
    """
    json_path = utils.JSON_PATH
    data = utils.load_json(json_path)
    questions = [each_qandas["question"] for each_qandas in data[0]['questions']]
    random_question = random.choice(questions)  
    
    return random_question

def feedback_provider(question: str) -> str:
    """
    Provides feedback based on the given question.
    """
    model = AzureChatOpenAI(
        deployment_name=os.environ["OPENAI_DEPLOYMENT_NAME"],
        temperature=0.8
    )

    json_path = utils.JSON_PATH
    data = utils.load_json(json_path)

    context = [each_qanda for each_qanda in data[0]['questions'] if each_qanda['question'] == question]
    
    print(f"CONTEXT: {context}")

    prompt_template = ChatPromptTemplate.from_template(FEEDBACK_PROMPT)
    prompt = prompt_template.format(context=context[0], question=question)

    response_text = model.invoke(prompt).content

    return response_text

def points_updater(user_id: str, points: int=1):
    """
    Updates the points of the user.
    """
    sqlite_utils.update_points(user_id, points)

def points_retrieval(user_id: str) -> str:
    """
    Returns the current points count with a message from the LLM.
    """
    current_points = sqlite_utils.get_points(user_id)
    
    model = AzureChatOpenAI(
        deployment_name=os.environ["OPENAI_DEPLOYMENT_NAME"],
        temperature=0.2
    )
    
    prompt_template = ChatPromptTemplate.from_template(POINTS_RETRIEVAL_PROMPT)
    prompt = prompt_template.format(points=current_points)

    response_text = model.invoke(prompt).content
    return response_text

def points_only_retrieval(user_id: str) -> str:
    """
    Returns the current points count.
    """
    return sqlite_utils.get_points(user_id)

def asked_questions_updater(user_id: str):
    """
    Updates the number of questions asked to the user.
    """
    print(f"Current number of questions asked: {sqlite_utils.get_asked_questions(user_id)}")
    sqlite_utils.update_asked_questions(user_id)
    print("Asked questions updated!")
    print(f"Current number of questions asked: {sqlite_utils.get_asked_questions(user_id)}")
    
def asked_questions_retrieval(user_id: str) -> int:
    """
    Returns the current number of questions asked to the user.
    """
    return sqlite_utils.get_asked_questions(user_id)

def narrator_tool(current_story: str, step: int) -> str:
    """
    Narrates a story based on the chosen prompts.
    """
    print(f"Current step: {step}")
    
    model = AzureChatOpenAI(
        deployment_name=os.environ["OPENAI_DEPLOYMENT_NAME"],
        temperature=1
    )

    # si ya se escogió una historia
    if current_story is None:
        current_story = utils.choose_random_story()

    # construye el path dinámico según la carpeta seleccionada
    story_module_path = f"app.prompts.stories.{current_story}.{current_story}_narrator_prompts"

    narrator_prompts_module = importlib.import_module(story_module_path)

    # accede a los prompts como si estuvieran importados estáticamente
    narrator_prompts = [getattr(narrator_prompts_module, 'NARRATOR_ZERO_PROMPT'),
                        getattr(narrator_prompts_module, 'NARRATOR_TWO_PROMPT'),
                        getattr(narrator_prompts_module, 'NARRATOR_THREE_PROMPT'),
                        getattr(narrator_prompts_module, 'NARRATOR_FOUR_PROMPT')]

    prompt_template = ChatPromptTemplate.from_template(narrator_prompts[step])
    prompt = prompt_template.format(step=step)

    response_text = model.invoke(prompt).content
    return f"✒️  {response_text}", current_story

def verify_tool_call(message: AIMessage) -> bool:
    """
    Verifies if there was a tool call.
    """
    if isinstance(message, AIMessage):
        if message.additional_kwargs:
            if message.additional_kwargs["tool_calls"]:
                return True
            
    return False

single_tools = [rag_search, qanda_chooser, feedback_provider, points_retrieval, qanda_evaluation, narrator_tool]    

# ================== #
# STORIES GAME TOOLS #
# ================== #

def first_character(current_story: str):
    """
    Calls the first character and returns it's response.
    """
    question = qanda_chooser()
    
    model = AzureChatOpenAI(
        deployment_name=os.environ["OPENAI_DEPLOYMENT_NAME"],
        temperature=1
    )
    
    character_personality_prompts = utils.load_character_personalities(current_story, 'FIRST')
    character_prompt = utils.load_character_prompt(current_story, 'FIRST')[0]
    character_emoji = utils.find_character_emoji(current_story)
    
    character_personality = random.choice(character_personality_prompts)
    
    prompt_template = ChatPromptTemplate.from_template(character_prompt)
    prompt = prompt_template.format(personality=character_personality, question=question)

    response_text = model.invoke(prompt).content
    return f"{character_emoji}  {response_text}", character_personality, question

def second_character(current_story: str):
    """
    Calls the second character and returns it's response.
    """
    question = qanda_chooser()
    
    model = AzureChatOpenAI(
        deployment_name=os.environ["OPENAI_DEPLOYMENT_NAME"],
        temperature=1
    )
    
    character_personality_prompts = utils.load_character_personalities(current_story, 'SECOND')
    character_prompt = utils.load_character_prompt(current_story, 'SECOND')[0]
    character_emoji = utils.find_character_emoji(current_story)
    
    character_personality = random.choice(character_personality_prompts)
    
    prompt_template = ChatPromptTemplate.from_template(character_prompt)
    prompt = prompt_template.format(personality=character_personality, question=question)
    
    response_text = model.invoke(prompt).content
    return f"{character_emoji}  {response_text}", character_personality, question

def third_character(current_story: str):
    """
    Calls the third character and returns it's response.
    """
    question = qanda_chooser()
    
    model = AzureChatOpenAI(
        deployment_name=os.environ["OPENAI_DEPLOYMENT_NAME"],
        temperature=1
    )
    
    character_personality_prompts = utils.load_character_personalities(current_story, 'THIRD')
    character_prompt = utils.load_character_prompt(current_story, 'THIRD')[0]
    character_emoji = utils.find_character_emoji(current_story)
    
    character_personality = random.choice(character_personality_prompts)
    
    prompt_template = ChatPromptTemplate.from_template(character_prompt)
    prompt = prompt_template.format(personality=character_personality, question=question)
    
    response_text = model.invoke(prompt).content
    return f"{character_emoji}  {response_text}", character_personality, question 

def lifes_updater(user_id: str, reset: bool=False):
    """
    Updates the lifes of the user in the story game.
    """
    sqlite_utils.update_lifes(user_id, reset)

def lifes_retrieval(user_id: str, current_story: Story, lost_live: bool) -> Tuple[str, int]:
    """
    Returns the current lifes count of the user in the story game.
    """
    current_lifes = sqlite_utils.get_lifes(user_id)
    
    name = current_story["name"]
    question = current_story["to_evaluate"]
    step = current_story["step"]
    personality = current_story["character_personality"]
    
    model = AzureChatOpenAI(
        deployment_name=os.environ["OPENAI_DEPLOYMENT_NAME"],
        temperature=1
    )
    
    character_emoji = utils.find_character_emoji(name)
    auxiliar_prompts = utils.load_character_auxiliar_prompts(name, step)    
    # success_steps_prompts = [BRIDGE_GOBLIN_SUCCESS_PROMPT, GOBLIN_AT_HOME_SUCCESS_PROMPT, CASTLE_GOBLIN_SUCCESS_PROMPT]
    # lost_life_steps_prompts = [BRIDGE_GOBLIN_LIFES_LOST_PROMPT, GOBLIN_AT_HOME_LIFES_LOST_PROMPT, CASTLE_GOBLIN_LIFES_LOST_PROMPT]
    # failure_steps_prompts = [BRIDGE_GOBLIN_FAILURE_PROMPT, GOBLIN_AT_HOME_FAILURE_PROMPT, CASTLE_GOBLIN_FAILURE_PROMPT]
    success_steps_prompts = [auxiliar_prompts['SUCCESS'], auxiliar_prompts['SUCCESS'], auxiliar_prompts['SUCCESS']]
    lost_life_steps_prompts = [auxiliar_prompts['LIFES_LOST'], auxiliar_prompts['LIFES_LOST'], auxiliar_prompts['LIFES_LOST']]
    failure_steps_prompts = [auxiliar_prompts['FAILURE'], auxiliar_prompts['FAILURE'], auxiliar_prompts['FAILURE']]

    kind = 1
    prompt = success_steps_prompts[step - 1]
    if lost_live:
        print("User lost a life!")
        if current_lifes == 0:
            kind = 1
            prompt = failure_steps_prompts[step - 1]
        else:
            kind = 2
            prompt = lost_life_steps_prompts[step - 1]
    
    print(f"INDEX: {step - 1}")
    prompt_template = ChatPromptTemplate.from_template(prompt)
    prompt = prompt_template.format(personality=personality, question=question, lifes=current_lifes)

    response_text = model.invoke(prompt).content
    return f"{character_emoji}  {response_text}", current_lifes, kind
