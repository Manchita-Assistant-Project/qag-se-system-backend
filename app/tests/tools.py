import os
import uuid
import random
from typing import Annotated, Callable, Optional
from typing_extensions import TypedDict

from langchain.tools import BaseTool
from langchain_core.tools import tool
from langchain_openai import AzureChatOpenAI
from langchain_core.messages import AIMessage
from langgraph.utils.runnable import Runnable
from langchain.prompts import ChatPromptTemplate
from langchain_community.vectorstores import Chroma
from langgraph.graph.message import AnyMessage, add_messages

import app.generator.utils as utils
import app.generator.config as config
import app.database.chroma_utils as chroma_utils
import app.database.sqlite_utils as sqlite_utils
from app.tests.prompts import QANDA_PROMPT, EVALUATE_PROMPT, INTERACTION_PROMPT, POINTS_RETRIEVAL_PROMPT

from dotenv import load_dotenv
os.environ["OPENAI_API_KEY"] = config.OPENAI_API_KEY
os.environ["AZURE_OPENAI_ENDPOINT"] = config.AZURE_OPENAI_ENDPOINT
os.environ["OPENAI_API_TYPE"] = config.OPENAI_API_TYPE
os.environ["OPENAI_API_VERSION"] = config.OPENAI_API_VERSION
os.environ["OPENAI_DEPLOYMENT_NAME"] = config.OPENAI_DEPLOYMENT_NAME
load_dotenv()

embedding_function = chroma_utils.get_embedding_function()
db = Chroma(persist_directory=chroma_utils.CHROMA_PATH, embedding_function=embedding_function)

@tool('qanda_generation')
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


# @tool('qanda_evaluation')
def qanda_evaluation(input_data: str) -> str:
    """
    Evaluates the given answer to a question.
    """
    json_path: str=utils.JSON_PATH
    data = utils.load_json(json_path)       

    question, answer = input_data.split('|||')
    
    model = AzureChatOpenAI(
        deployment_name=os.environ["OPENAI_DEPLOYMENT_NAME"],
        temperature=0.2
    )
    
    prompt_template = ChatPromptTemplate.from_template(EVALUATE_PROMPT)
    prompt = prompt_template.format(context=data, answer=answer, question=question)
    response_text = model.invoke(prompt).content

    return response_text


@tool('rag_search')
def rag_search(query: str) -> str:
    """
    Responds when asked about an specific topic about the context.
    """    
    model = AzureChatOpenAI(
        deployment_name=os.environ["OPENAI_DEPLOYMENT_NAME"],
        temperature=0.2
    )
    results = db.similarity_search_with_score(query, k=5)

    context_text = "\n\n---\n\n".join([doc.page_content for doc, _score in results])
    prompt_template = ChatPromptTemplate.from_template(INTERACTION_PROMPT)
    prompt = prompt_template.format(context=context_text)
    
    response_text = model.invoke(prompt).content

    return response_text


@tool('qanda_chooser')
def qanda_chooser() -> str:
    """
    It does not generate questions.
    Chooses a random question ONLY from the JSON file.
    """
    json_path = utils.JSON_PATH
    data = utils.load_json(json_path)
    questions = [each_qandas["question"] for each_qandas in data[0]['questions']]
    random_question = random.choice(questions)  
    
    return random_question

# @tool('points_updater')
def points_updater(user_id: str, points: int=1):
    """
    Updates the points of the user.
    """
    sqlite_utils.update_points(user_id, points)

@tool('points_retrieval')
def points_retrieval(user_id: str) -> int:
    """
    Returns the current points count.
    """
    user_id = 'a1efdbdc-5256-4980-ae8b-e72c2a2f024d'
    current_points = sqlite_utils.get_points(user_id)
    
    prompt_template = ChatPromptTemplate.from_template(POINTS_RETRIEVAL_PROMPT)
    prompt = prompt_template.format(points=current_points)

    model = AzureChatOpenAI(
        deployment_name=os.environ["OPENAI_DEPLOYMENT_NAME"],
        temperature=0.2
    )

    response_text = model.invoke(prompt).content
    return response_text
    
single_tools = [rag_search, qanda_chooser, points_retrieval]
