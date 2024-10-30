import os
import random
import importlib
from typing import Tuple

from sklearn.metrics.pairwise import cosine_similarity

from langchain_core.messages import AIMessage
from langchain.prompts import ChatPromptTemplate
from langchain_community.vectorstores import Chroma
from langchain_openai import AzureChatOpenAI, ChatOpenAI

import app.config as config
import app.agent.utils as utils
from app.agent.state import Story
import app.database.chroma_utils as chroma_utils
import app.database.sqlite_utils as sqlite_utils
from app.prompts.tools_prompts import QANDA_PROMPT, EVALUATE_PROMPT, \
                                      INTERACTION_PROMPT, \
                                      POINTS_RETRIEVAL_PROMPT, \
                                      FEEDBACK_PROMPT, RESPONSE_CLASSIFIER_PROMPT

from dotenv import load_dotenv
os.environ["OPENAI_API_KEY"] = config.OPENAI_API_KEY
os.environ["AZURE_OPENAI_ENDPOINT"] = config.AZURE_OPENAI_ENDPOINT
os.environ["OPENAI_API_TYPE"] = config.OPENAI_API_TYPE
os.environ["OPENAI_API_VERSION"] = config.OPENAI_API_VERSION
os.environ["OPENAI_DEPLOYMENT_NAME"] = config.OPENAI_DEPLOYMENT_NAME
MODEL_NAME = config.OPENAI_MODEL_4OMINI
load_dotenv()

embedding_function = chroma_utils.get_embedding_function()
# db = Chroma(persist_directory=chroma_utils.CHROMA_PATH, embedding_function=embedding_function)

def qanda_generation(db: Chroma) -> str:
    """
    Saves questions and answers to the JSON file.
    """
    query = ""
    json_path = utils.JSON_PATH

    # model = AzureChatOpenAI(
    #     deployment_name=os.environ["OPENAI_DEPLOYMENT_NAME"],
    #     temperature=0.2
    # )
    
    model = ChatOpenAI(
        model=MODEL_NAME,
        temperature=0.2
    )

    results = db.similarity_search_with_score(query, k=5)
    
    context_text = "\n\n---\n\n".join([doc.page_content for doc, _score in results])

    prompt_template = ChatPromptTemplate.from_template(QANDA_PROMPT)
    prompt = prompt_template.format(context=context_text)

    response_text = model.invoke(prompt).content

    utils.update_json(json_path, response_text.split('\n\n'))
    return response_text

def qanda_evaluation(input_data: str, game_type: str, db_id: str) -> str:
    """
    Evaluates the given answer to a question.
    """
    # json_path = utils.JSON_PATH
    json_path = os.path.join(chroma_utils.DATABASES_PATH, db_id, 'q&as', 'qs.json')
    data = utils.load_json(json_path)
    
    question, answer = input_data.split('|||')
    print(f"QUESTION: {question} | ANSWER: {answer}")
    
    context = [each_qanda for each_qanda in data if each_qanda['question'] == question][0]
    
    # model = AzureChatOpenAI(
    #     deployment_name=os.environ["OPENAI_DEPLOYMENT_NAME"],
    #     temperature=0.2
    # )
    
    model = ChatOpenAI(
        model=MODEL_NAME,
        temperature=0.2
    )
    
    context_string, right_answer = utils.define_context_string(context, game_type)
    # db = chroma_utils.get_db(db_id)
    
    # results = db.similarity_search_with_score(question, k=5)
    # context_text = "\n\n---\n\n".join([doc.page_content for doc, _score in results])
    
    # context_string = context_string + '\n\n' + '--'*50 + '\n\n' + context_text
    
    print(f"CONTEXT STRING: {context_string}")
    
    answer = answer if answer != '' else "****"
    
    prompt_template = ChatPromptTemplate.from_template(EVALUATE_PROMPT)
    prompt = prompt_template.format(context=context_string, answer=answer, question=question)
    
    if game_type == "simple_quiz":
        prompt += f'\nSi la respuesta es incorrecta, responde "La respuesta es incorrecta..." y \
                    agrega la respuesta correcta: "{right_answer}". Debe ser una frase completa, \
                    no solo la respuesta.'
    
    response_text = model.invoke(prompt).content
    
    print(f"RESPONSE: {response_text}")
    return response_text

def rag_search(query: str, db_id: str) -> str:
    """
    Responds when asked about an specific topic about the context.
    """
    print(f"QUERY: {query}")

    db = chroma_utils.get_db(db_id)

    # model = AzureChatOpenAI(
    #     deployment_name=os.environ["OPENAI_DEPLOYMENT_NAME"],
    #     temperature=0
    # )
    
    model = ChatOpenAI(
        model=MODEL_NAME,
        temperature=0.2
    )

    results = db.similarity_search_with_score(query, k=8)

    context_text = "\n\n---\n\n".join([doc.page_content for doc, _score in results])
    
    prompt_template = ChatPromptTemplate.from_template(INTERACTION_PROMPT)
    prompt = prompt_template.format(context=context_text, query=query)
    
    response_text = model.invoke(prompt).content

    return response_text

def qanda_chooser(game_type: str, db_id: str) -> str:
    """
    Chooses a random question from the JSON file based on the game type.
    """
    json_path = os.path.join(chroma_utils.DATABASES_PATH, db_id, 'q&as', 'qs.json')             
    data = utils.load_json(json_path)
    
    if game_type == "story":
        questions = [item["question"] for item in data if item["type"] == "OEQ"]
    elif game_type == "simple_quiz":
        questions = [item for item in data if item["type"] == "MCQ" or item["type"] == "TFQ"]
            
    random_question = random.choice(questions)
    
    return random_question

def feedback_provider(question: str, db_id: str) -> str:
    """
    Provides feedback based on the given question.
    """
    
    # model = AzureChatOpenAI(
    #     deployment_name=os.environ["OPENAI_DEPLOYMENT_NAME"],
    #     temperature=0.8
    # )
    
    model = ChatOpenAI(
        model=MODEL_NAME,
        temperature=0.8
    )

    json_path = os.path.join(chroma_utils.DATABASES_PATH, db_id, 'q&as', 'qs.json')
    data = utils.load_json(json_path)

    context = [each_qanda for each_qanda in data if each_qanda['question'] == question]
    
    print(f"CONTEXT: {context}")

    prompt_template = ChatPromptTemplate.from_template(FEEDBACK_PROMPT)
    prompt = prompt_template.format(context=context[0], question=question)

    response_text = model.invoke(prompt).content

    return response_text

def points_updater(user_id: str, db_id: str, points: int=1):
    """
    Updates the points of the user.
    """
    sqlite_utils.update_points(user_id, db_id, points)

def points_retrieval(user_id: str, db_id: str) -> str:
    """
    Returns the current points count with a message from the LLM.
    """
    current_points = sqlite_utils.get_points(user_id, db_id)
    
    # model = AzureChatOpenAI(
    #     deployment_name=os.environ["OPENAI_DEPLOYMENT_NAME"],
    #     temperature=0.2
    # )
    
    model = ChatOpenAI(
        model=MODEL_NAME,
        temperature=0.2
    )
    
    prompt_template = ChatPromptTemplate.from_template(POINTS_RETRIEVAL_PROMPT)
    prompt = prompt_template.format(points=current_points)

    response_text = model.invoke(prompt).content
    return response_text

def points_only_retrieval(user_id: str, db_id: str) -> str:
    """
    Returns the current points count.
    """
    return sqlite_utils.get_points(user_id, db_id)

def asked_questions_updater(user_id: str, db_id: str):
    """
    Updates the number of questions asked to the user.
    """
    print(f"Current number of questions asked: {sqlite_utils.get_asked_questions(user_id, db_id)}")
    sqlite_utils.update_asked_questions(user_id, db_id)
    print("Asked questions updated!")
    print(f"Current number of questions asked: {sqlite_utils.get_asked_questions(user_id, db_id)}")
    
def asked_questions_retrieval(user_id: str, db_id) -> int:
    """
    Returns the current number of questions asked to the user.
    """
    return sqlite_utils.get_asked_questions(user_id, db_id)

def narrator_tool(current_story: str, step: int, db_id: str) -> str:
    """
    Narrates a story based on the chosen prompts.
    """
    print(f"Current step: {step}")
    
    # model = AzureChatOpenAI(
    #     deployment_name=os.environ["OPENAI_DEPLOYMENT_NAME"],
    #     temperature=1
    # )
    
    model = ChatOpenAI(
        model=MODEL_NAME,
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

    print(f"STEP NARRATOR TOOL: {step}")
    prompt_template = ChatPromptTemplate.from_template(narrator_prompts[step - 1])
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

single_tools = [rag_search, qanda_chooser, feedback_provider, points_retrieval, narrator_tool] # qanda_evaluation    

# ================== #
# STORIES GAME TOOLS #
# ================== #

def character_first_interaction(current_story_dict: Story, db_id: str):
    """
    Tool that has to be called only when it's the first interaction of a character.
    """
    
    question = qanda_chooser("story", db_id)
    
    # model = AzureChatOpenAI(
    #     deployment_name=os.environ["OPENAI_DEPLOYMENT_NAME"],
    #     temperature=1
    # )
    
    model = ChatOpenAI(
        model=MODEL_NAME,
        temperature=1
    )
    
    step = current_story_dict["step"]
    current_story = current_story_dict["name"]
    character_personality = current_story_dict["character_personality"]
        
    character_emoji = utils.find_character_emoji(current_story)
    
    character_personality_prompts = utils.load_character_personalities(current_story, step)
    character_personality = random.choice(character_personality_prompts)
    
    character_prompt = utils.load_character_prompt(current_story, step)[0]

    prompt_template = ChatPromptTemplate.from_template(character_prompt)
    prompt = prompt_template.format(personality=character_personality, question=question)

    response_text = model.invoke(prompt).content
    return f"{character_emoji}  {response_text}", character_personality, question

def character_success_or_failure(current_story_dict: Story, current_lives: int, db_id: str):
    model = ChatOpenAI(
        model=MODEL_NAME,
        temperature=1
    )
    
    question = current_story_dict["to_evaluate"]
    
    json_path = os.path.join(chroma_utils.DATABASES_PATH, db_id, 'q&as', 'qs.json')
    questions_dict = utils.load_json(json_path)

    context = [each_qanda for each_qanda in questions_dict if each_qanda['question'] == question][0]  
    context_string, right_answer = utils.define_context_string(context, "story")
    
    right_answer = utils.summarize_answers(model, context_string)
    
    step = current_story_dict["step"]
    current_story = current_story_dict["name"]
    character_personality = current_story_dict["character_personality"]
    
    character_emoji = utils.find_character_emoji(current_story)
    
    auxiliar_prompts = utils.load_character_auxiliar_prompts(current_story, step)
    success_character_prompt = auxiliar_prompts['SUCCESS']
    failure_character_prompt = auxiliar_prompts['FAILURE']
    
    character_prompt = success_character_prompt if current_lives > 0 else failure_character_prompt
    # print(f"CHARACTER PROMPT: {character_prompt}")
    prompt_template = ChatPromptTemplate.from_template(character_prompt)
    prompt = prompt_template.format(personality=character_personality, right_answer=right_answer)

    response_text = model.invoke(prompt).content + ('\n\n¡Escribe "¡Sigue!" para continuar con la historia!' if current_lives > 0 else '')
    return f"{character_emoji}  {response_text}"

def character_life_lost(current_story_dict: Story, current_lives: int):
    model = ChatOpenAI(
        model=MODEL_NAME,
        temperature=1
    )
    
    step = current_story_dict["step"]
    current_story = current_story_dict["name"]
    question = current_story_dict["to_evaluate"]
    character_personality = current_story_dict["character_personality"]
    
    character_emoji = utils.find_character_emoji(current_story)
    
    auxiliar_prompts = utils.load_character_auxiliar_prompts(current_story, step)
    
    character_prompt = auxiliar_prompts['LIVES_LOST']

    prompt_template = ChatPromptTemplate.from_template(character_prompt)
    prompt = prompt_template.format(personality=character_personality, question=question, lives=current_lives)

    response_text = model.invoke(prompt).content

    return f"{character_emoji}  {response_text}", question

def character_loop_interaction(current_story_dict: Story, response: str):
    model = ChatOpenAI(
        model=MODEL_NAME,
        temperature=1
    )
    
    step = current_story_dict["step"]
    current_story = current_story_dict["name"]
    question = current_story_dict["to_evaluate"]
    character_personality = current_story_dict["character_personality"]
    
    character_emoji = utils.find_character_emoji(current_story)
    
    auxiliar_prompts = utils.load_character_auxiliar_prompts(current_story, step)
    
    character_prompt = auxiliar_prompts['LOOP']

    prompt_template = ChatPromptTemplate.from_template(character_prompt)
    prompt = prompt_template.format(personality=character_personality, response=response, question=question)

    response_text = model.invoke(prompt).content

    return f"{character_emoji}  {response_text}"

def response_classifier(question: str, query: str, db_id: str):   
    model = ChatOpenAI(
        model=MODEL_NAME,
        temperature=0.2
    )
        
    prompt_template = ChatPromptTemplate.from_template(RESPONSE_CLASSIFIER_PROMPT)
    prompt = prompt_template.format(response=query, question=question)

    response_text = model.invoke(prompt).content
    return True if response_text == "True" else False

# def response_classifier(question: str, query: str, db_id: str):
#     embedding_model = chroma_utils.get_embedding_function()
    
#     json_path = os.path.join(chroma_utils.DATABASES_PATH, db_id, 'q&as', 'qs.json')
#     questions_dict = utils.load_json(json_path)
#     choices_list = [list(each_qanda['choices'].values()) for each_qanda in questions_dict if each_qanda['question'] == question][0]
    
#     response_embedded = embedding_model.embed_query(query)
#     print(f"CHOICES: {choices_list}")
#     how_many = 0
#     for each_choice in choices_list:
#         each_choice_embedded = embedding_model.embed_query(each_choice)
#         similarity = cosine_similarity([response_embedded], [each_choice_embedded])[0][0]
#         print(f"SIMILARITY: {similarity}")
#         if similarity <= 0.8:
#             how_many += 1
            
#     if how_many == len(choices_list): # significa que no tiene similitud con ninguna de las opciones
#         return False
    
#     return True

def lives_updater(user_id: str, db_id: str, reset: bool=False):
    """
    Updates the lives of the user in the story game.
    """
    sqlite_utils.update_lives(user_id, db_id, reset)

def lives_retrieval(user_id: str, db_id: str, current_story: Story, lost_life: bool) -> Tuple[str, int]:
    """
    Returns the current lives count of the user in the story game.
    """
    current_lives = sqlite_utils.get_lives(user_id, db_id)
    
    name = current_story["name"]
    question = current_story["to_evaluate"]
    step = current_story["step"]
    personality = current_story["character_personality"]
    
    # model = AzureChatOpenAI(
    #     deployment_name=os.environ["OPENAI_DEPLOYMENT_NAME"],
    #     temperature=1
    # )
    
    # model = ChatOpenAI(
    #     model=MODEL_NAME,
    #     temperature=1
    # )
    
    # character_emoji = utils.find_character_emoji(name)
    # auxiliar_prompts = utils.load_character_auxiliar_prompts(name, step)    
    # success_steps_prompts = [auxiliar_prompts['SUCCESS'], auxiliar_prompts['SUCCESS'], auxiliar_prompts['SUCCESS']]
    # lost_life_steps_prompts = [auxiliar_prompts['LIVES_LOST'], auxiliar_prompts['LIVES_LOST'], auxiliar_prompts['LIVES_LOST']]
    # failure_steps_prompts = [auxiliar_prompts['FAILURE'], auxiliar_prompts['FAILURE'], auxiliar_prompts['FAILURE']]

    # prompt = success_steps_prompts[step - 1]
    success = True if lost_life == False else False # True si se completó la evaluación, False si se perdió una vida
    
    print(f"INDEX: {step - 1}")
    # prompt_template = ChatPromptTemplate.from_template(prompt)
    # prompt = prompt_template.format(personality=personality, question=question, lives=current_lives)

    # response_text = model.invoke(prompt).content
    return current_lives, success

