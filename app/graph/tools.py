import os
import random
from typing import Tuple

from langchain_openai import AzureChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain_community.vectorstores import Chroma

import app.graph.utils as utils
import app.generator.config as config
import app.database.chroma_utils as chroma_utils
import app.database.sqlite_utils as sqlite_utils

from app.prompts.tools_prompts import QANDA_PROMPT, EVALUATE_PROMPT, \
                                      INTERACTION_PROMPT, \
                                      POINTS_RETRIEVAL_PROMPT, \
                                      FEEDBACK_PROMPT

from app.prompts.stories.goblins.goblins_narrator_prompts import NARRATOR_ZERO_PROMPT, \
                                                                 NARRATOR_TWO_PROMPT, \
                                                                 NARRATOR_THREE_PROMPT, \
                                                                 NARRATOR_FOUR_PROMPT

from app.prompts.stories.goblins.golbins_characters_prompts import BRIDGE_GOBLIN_ONE_PROMPT, BRIDGE_GOBLIN_LIVES_LOST_PROMPT, \
                                                                   BRIDGE_GOBLIN_SUCCESS_PROMPT, BRIDGE_GOBLIN_FAILURE_PROMPT, \
                                                                   GOBLIN_AT_HOME_ONE_PROMPT, GOBLIN_AT_HOME_LIVES_LOST_PROMPT, \
                                                                   GOBLIN_AT_HOME_SUCCESS_PROMPT, GOBLIN_AT_HOME_FAILURE_PROMPT, \
                                                                   CASTLE_GOBLIN_ONE_PROMPT, CASTLE_GOBLIN_LIVES_LOST_PROMPT, \
                                                                   CASTLE_GOBLIN_SUCCESS_PROMPT, CASTLE_GOBLIN_FAILURE_PROMPT

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
    Returns the current points count.
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
    
def narrator_tool(step: str) -> str:
    """
    Narrates the goblin story.
    """
    print(f"Current step: {step}")
    
    model = AzureChatOpenAI(
        deployment_name=os.environ["OPENAI_DEPLOYMENT_NAME"],
        temperature=1
    )
    
    narrator_prompts = [NARRATOR_ZERO_PROMPT, NARRATOR_TWO_PROMPT, NARRATOR_THREE_PROMPT, NARRATOR_FOUR_PROMPT]
    
    prompt_template = ChatPromptTemplate.from_template(narrator_prompts[int(step)])
    prompt = prompt_template.format(step=step)

    response_text = model.invoke(prompt).content
    return f"🍀 {response_text}"

single_tools = [rag_search, qanda_chooser, feedback_provider, points_retrieval, qanda_evaluation, narrator_tool]    

# ================= #
# GOBLIN GAME TOOLS #
# ================= #

def bridge_goblin():
    """
    Calls the bridge goblin and returns it's response.
    """
    question = qanda_chooser()
    
    model = AzureChatOpenAI(
        deployment_name=os.environ["OPENAI_DEPLOYMENT_NAME"],
        temperature=1
    )
    
    narrator_prompts = [BRIDGE_GOBLIN_ONE_PROMPT]
    goblin_personality = random.choice(narrator_prompts)
    
    prompt_template = ChatPromptTemplate.from_template(goblin_personality)
    prompt = prompt_template.format(question=question)
    
    response_text = model.invoke(prompt).content
    return f"🧌 {response_text}", question

def goblin_at_home():
    """
    Calls the goblin at home and returns it's response.
    """
    question = qanda_chooser()
    
    model = AzureChatOpenAI(
        deployment_name=os.environ["OPENAI_DEPLOYMENT_NAME"],
        temperature=1
    )
    
    narrator_prompts = [GOBLIN_AT_HOME_ONE_PROMPT]
    goblin_personality = random.choice(narrator_prompts)
    
    prompt_template = ChatPromptTemplate.from_template(goblin_personality)
    prompt = prompt_template.format(question=question)
    
    response_text = model.invoke(prompt).content
    return f"🧌 {response_text}", question

def castle_goblin():
    """
    Calls the castle goblin and returns it's response.
    """
    question = qanda_chooser()
    
    model = AzureChatOpenAI(
        deployment_name=os.environ["OPENAI_DEPLOYMENT_NAME"],
        temperature=1
    )
    
    narrator_prompts = [CASTLE_GOBLIN_ONE_PROMPT]
    goblin_personality = random.choice(narrator_prompts)
    
    prompt_template = ChatPromptTemplate.from_template(goblin_personality)
    prompt = prompt_template.format(question=question)
    
    response_text = model.invoke(prompt).content
    return f"🧌 {response_text}", question  

def lives_updater(user_id: str, reset: bool=False):
    """
    Updates the lives of the user in the goblin game.
    """
    sqlite_utils.update_lives(user_id, reset)

def lives_retrieval(user_id: str, question: str, lost_live: bool, step: int) -> Tuple[str, int]:
    """
    Returns the current lives count of the user in the goblin game.
    """
    current_lives = sqlite_utils.get_lives(user_id)
    
    model = AzureChatOpenAI(
        deployment_name=os.environ["OPENAI_DEPLOYMENT_NAME"],
        temperature=1
    )
    
    success_steps_prompts = [BRIDGE_GOBLIN_SUCCESS_PROMPT, GOBLIN_AT_HOME_SUCCESS_PROMPT, CASTLE_GOBLIN_SUCCESS_PROMPT]
    lost_live_steps_prompts = [BRIDGE_GOBLIN_LIVES_LOST_PROMPT, GOBLIN_AT_HOME_LIVES_LOST_PROMPT, CASTLE_GOBLIN_LIVES_LOST_PROMPT]
    failure_steps_prompts = [BRIDGE_GOBLIN_FAILURE_PROMPT, GOBLIN_AT_HOME_FAILURE_PROMPT, CASTLE_GOBLIN_FAILURE_PROMPT]

    prompt = success_steps_prompts[step - 1]
    if lost_live:
        print("User lost a life!")
        if current_lives == 0:
            prompt = failure_steps_prompts[step - 1]
        else:
            prompt = lost_live_steps_prompts[step - 1]
    
    print(f"INDEX: {step - 1}")
    prompt_template = ChatPromptTemplate.from_template(prompt)
    prompt = prompt_template.format(question=question, lifes=current_lives)

    response_text = model.invoke(prompt).content
    return f"🧌 {response_text}", current_lives
