import os
import re
import json
import random
import string
import numpy as np
import pandas as pd
from typing import Dict, List, TypedDict

from pydantic import BaseModel

import app.config as config
import app.generator.utils as utils
import app.database.chroma_utils as chroma_utils

from sklearn.metrics.pairwise import cosine_similarity

from langchain_ollama import OllamaLLM
from langchain_community.llms.ollama import Ollama
from langchain_openai import AzureChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain_community.llms.ollama import Ollama
from langchain_community.vectorstores import Chroma

from app.prompts.qandas_prompts import Q_MCQ_PROMPT, Q_OAQ_PROMPT, Q_TFQ_PROMPT, \
                                       HARDER_Q_PROMPT, \
                                       A_MCQ_PROMPT, A_OAQ_PROMPT, A_TFQ_PROMPT, \
                                       Q_EVALUATION_PROMPT, TEN_Q_MCQ_PROMPT, TEN_Q_TFQ_PROMPT

def get_context(query: str="", k: int=90):
    embedding_function = chroma_utils.get_embedding_function()
    db = Chroma(persist_directory=chroma_utils.CHROMA_PATH, embedding_function=embedding_function)
    
    # Search the DB -> top k most relevant chunks to the query.
    results = db.similarity_search_with_score(query, k)

    context_text = "\n\n---\n\n".join([doc.page_content for doc, _score in results])

    return context_text

def question_generator_tool(question_type: int, difficulty: str, context: str):
    files = ['mcqs', 'oaqs', 'tfqs']
    correct_file = files[question_type - 1]
    generated_questions_list = utils.load_json(correct_file)

    generated_questions = [question["question"] for question in generated_questions_list]

    # print(f"generated_questions: {generated_questions}")
    
    generated_questions_string = utils.structure_generated_questions_string(generated_questions)

    # llm = AzureChatOpenAI(
    #     deployment_name=os.environ["OPENAI_DEPLOYMENT_NAME"],
    #     temperature=0.8
    # )
    
    llm = Ollama(
        model='llama3.1',
        temperature=0.8,
        base_url='http://ollama-container:11434'
    )
    
    types = [Q_MCQ_PROMPT, Q_OAQ_PROMPT, Q_TFQ_PROMPT]
    # types = [QANDA_MCQ_PROMPT, QANDA_OAQ_PROMPT, QANDA_TFQ_PROMPT]
    
    prompt_template = ChatPromptTemplate.from_template(types[question_type - 1])
    prompt = prompt_template.format(context=context, difficulty=difficulty, harder_prompt="", generated_questions=generated_questions_string)

    # response_text = llm.invoke(prompt).content
    response_text = llm.invoke(prompt)
    print(f"response_text: {response_text}")
    
    if difficulty == 'Difícil':
        rand_int = random.randint(2, 5) # cinco niveles de dificultad
        print(f"rand_int: {rand_int}")
        harder_prompt_template = ChatPromptTemplate.from_template(HARDER_Q_PROMPT)
        question_type_to_string = {
            1: "Opción Múltiple",
            2: "Respuesta Abierta",
            3: "Verdadero o Falso"
        }
        for _ in range(rand_int): # iterar para hacer la pregunta para hacerla más difícil
            harder_prompt = harder_prompt_template.format(question=response_text, context=context, question_type=question_type_to_string[question_type])
            # response_text = llm.invoke(harder_prompt).content
            response_text = llm.invoke(harder_prompt)
            print(f"response_text: {response_text}")
    
    return response_text                                       

context = get_context("")
print("Got Context!")
print(question_generator_tool(1, 1, context))

