import os
import uuid
import random
from typing import Annotated, Callable, Optional
from typing_extensions import TypedDict

from langchain.tools import BaseTool
from langchain_core.tools import tool
from langchain_openai import AzureChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain_community.vectorstores import Chroma
from langgraph.graph.message import AnyMessage, add_messages

import app.generator.config as config
import app.database.db_utils as db_utils
import app.generator.utils as utils
from app.tests.prompts import QANDA_PROMPT, EVALUATE_PROMPT, INTERACTION_PROMPT

from dotenv import load_dotenv
os.environ["OPENAI_API_KEY"] = config.OPENAI_API_KEY
os.environ["AZURE_OPENAI_ENDPOINT"] = config.AZURE_OPENAI_ENDPOINT
os.environ["OPENAI_API_TYPE"] = config.OPENAI_API_TYPE
os.environ["OPENAI_API_VERSION"] = config.OPENAI_API_VERSION
os.environ["OPENAI_DEPLOYMENT_NAME"] = config.OPENAI_DEPLOYMENT_NAME
load_dotenv()

embedding_function = db_utils.get_embedding_function()
db = Chroma(persist_directory=db_utils.CHROMA_PATH, embedding_function=embedding_function)

class State(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]
    last_question: Optional[str]
    last_tool_call_id: Optional[str]

@tool('qanda_generation')
def qanda_generation():
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



@tool('qanda_evaluation')
def qanda_evaluation(input_data: str):
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
def rag_search(query: str):
    """
    Responds when asked about an specific topic about the context.
    """
    # ======================================================================================================= #
    # TOCA CAMBIAR ESTE... TOCA QUE EL FEEDBACK SEA EN EVALUATE_AGENT Y ESTE SEA SOLO PARA INTERACCIÓN RAG... #
    # ======================================================================================================= #
    
    model = AzureChatOpenAI(
        deployment_name=os.environ["OPENAI_DEPLOYMENT_NAME"],
        temperature=0.2
    )
    results = db.similarity_search_with_score(query, k=5)
    
    context_text = "\n\n---\n\n".join([doc.page_content for doc, _score in results])
    prompt_template = ChatPromptTemplate.from_template(INTERACTION_PROMPT)
    prompt = prompt_template.format(topic=context_text)
    
    response_text = model.invoke(prompt).content
    print(f"INTERACTION_AGENT_RESPONSE: {response_text}")
    return response_text


@tool('qanda_chooser')
def qanda_chooser(state: State):
    """
    It does not generate questions.
    Chooses a random question ONLY from the JSON file.
    """
    json_path: str=utils.JSON_PATH
    data = utils.load_json(json_path)
    questions = [each_qandas["question"] for each_qandas in data[0]['questions']]
    random_question = random.choice(questions)  
    
    state["last_question"] = random_question
    
    tool_call_data = {
        "name": "qanda_evaluation",
        "args": {
            "input_data": random_question + '|||response_placeholder'
        },
        "id": str(uuid.uuid4()),
    }

    return {
        "content": random_question,
        "tool_calls": [tool_call_data],
    }
