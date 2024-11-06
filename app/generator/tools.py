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

from langchain.prompts import ChatPromptTemplate
from langchain_community.vectorstores import Chroma
from langchain_openai import AzureChatOpenAI, ChatOpenAI

from app.prompts.qandas_prompts import Q_MCQ_PROMPT, Q_OEQ_PROMPT, Q_TFQ_PROMPT, \
                                       HARDER_Q_PROMPT, Q_REFINER_PROMPT, \
                                       A_MCQ_PROMPT, A_OEQ_PROMPT, A_TFQ_PROMPT, \
                                       Q_EVALUATION_PROMPT, TEN_Q_MCQ_PROMPT, \
                                       TEN_Q_TFQ_PROMPT, TEN_Q_OEQ_PROMPT
                                       

from dotenv import load_dotenv
os.environ["OPENAI_API_KEY"] = config.OPENAI_API_KEY
os.environ["AZURE_OPENAI_ENDPOINT"] = config.AZURE_OPENAI_ENDPOINT
os.environ["OPENAI_API_TYPE"] = config.OPENAI_API_TYPE
os.environ["OPENAI_API_VERSION"] = config.OPENAI_API_VERSION
os.environ["OPENAI_DEPLOYMENT_NAME"] = config.OPENAI_DEPLOYMENT_NAME
MODEL_NAME = config.OPENAI_MODEL_4OMINI
load_dotenv()

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
QANDAS_EVALUATION_DATASET = os.path.join(base_dir, 'generator', 'datasets', 'qandas_dataset.csv')
QANDAS_JSONS = os.path.join(base_dir, 'generator', 'q&as')

class FullQuestionOutput(TypedDict):
    question: str
    choices: List[str]
    answer: str
    
class QuestionOutput(BaseModel):
    question: str
    difficulty: str

class QuestionsOutputList(BaseModel):
    questions: List[QuestionOutput]

def load_dataset(path: str) -> pd.DataFrame:
    return pd.read_csv(path, sep=";")

def get_context(db_id: str, query: str="", k: int=90):
    db = chroma_utils.get_db(db_id)
    # embedding_function = chroma_utils.get_embedding_function()
    # db = Chroma(persist_directory=chroma_utils.CHROMA_PATH, embedding_function=embedding_function)
    
    # Search the DB -> top k most relevant chunks to the query.
    results = db.similarity_search_with_score(query, k)

    context_text = "\n\n---\n\n".join([doc.page_content for doc, _score in results])

    return context_text

def get_context_tool(db_id: str, query: str="", k: int=90):
    context = get_context(db_id, query, k)
    return context

def question_generator_tool(question_type: int, difficulty: str, context: str):
    files = ['mcqs', 'oeqs', 'tfqs']
    correct_file = files[question_type - 1]
    generated_questions_list = utils.load_json(correct_file)

    generated_questions = [question["question"] for question in generated_questions_list]

    # print(f"generated_questions: {generated_questions}")
    
    generated_questions_string = utils.structure_generated_questions_string(generated_questions)

    llm = AzureChatOpenAI(
        deployment_name=os.environ["OPENAI_DEPLOYMENT_NAME"],
        temperature=0.8
    )
    
    types = [Q_MCQ_PROMPT, Q_OEQ_PROMPT, Q_TFQ_PROMPT]
    # types = [QANDA_MCQ_PROMPT, QANDA_OEQ_PROMPT, QANDA_TFQ_PROMPT]
    
    prompt_template = ChatPromptTemplate.from_template(types[question_type - 1])
    prompt = prompt_template.format(context=context, difficulty=difficulty, harder_prompt="", generated_questions=generated_questions_string)

    response_text = llm.invoke(prompt).content
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
            response_text = llm.invoke(harder_prompt).content
            print(f"response_text: {response_text}")
    
    return response_text

def ten_questions_generator_tool(db_id: str, question_type: int, difficulty: str, context: str):
    files = ['mcqs', 'oeqs', 'tfqs']
    correct_file = files[question_type - 1]
    generated_questions_list = utils.load_json(db_id, correct_file)

    generated_questions = [question["question"] for question in generated_questions_list]

    # print(f"generated_questions: {generated_questions}")
    
    generated_questions_string = utils.structure_generated_questions_string(generated_questions)
    # print(generated_questions_string)
    
    # llm = AzureChatOpenAI(
    #     deployment_name=os.environ["OPENAI_DEPLOYMENT_NAME"],
    #     temperature=0.8,
    # )
    
    llm = ChatOpenAI(
        model=MODEL_NAME,
        temperature=0.8
    )
    
    types = [TEN_Q_MCQ_PROMPT, TEN_Q_OEQ_PROMPT, TEN_Q_TFQ_PROMPT]
    # types = [QANDA_MCQ_PROMPT, QANDA_OEQ_PROMPT, QANDA_TFQ_PROMPT]
    
    prompt_template = ChatPromptTemplate.from_template(types[question_type - 1])
    prompt = prompt_template.format(context=context, generated_questions=generated_questions_string)

    # response_text = llm.invoke(prompt).content
    # print(f"response_text 1: {response_text}")
    
    structured_llm = llm.with_structured_output(QuestionsOutputList)
    response_text = structured_llm.invoke(prompt)
    # print(f"response_text 2: {response_text}")
    
    return response_text["questions"]

def answer_generator_tool(q_type: int, question: str, difficulty: str, context: str):
    # llm = AzureChatOpenAI(
    #     deployment_name=os.environ["OPENAI_DEPLOYMENT_NAME"],
    #     temperature=0.7
    # )
    
    llm = ChatOpenAI(
        model=MODEL_NAME,
        temperature=0.7
    )
    
    types = [A_MCQ_PROMPT, A_OEQ_PROMPT, A_TFQ_PROMPT]
    
    print(f'PREGUNTA: {question}')
    prompt_template = ChatPromptTemplate.from_template(types[q_type - 1])
    prompt = prompt_template.format(context=context, question=question, difficulty=difficulty)
    structured_llm = llm.with_structured_output(FullQuestionOutput)
    response_text = structured_llm.invoke(prompt)
    
    choices_dict = utils.choices_list_to_dict(response_text["choices"])
    response_text["choices"] = choices_dict       

    return str(response_text)
    
    # for _ in range(10):
    #     try:
    #         response_text = structured_llm.invoke(prompt)
    #         print(response_text)
    #         response_dict = json.loads(response_text)  # intentamos convertir el texto a dict
    #         return response_text
    #     except json.JSONDecodeError:
    #         print("Error al convertir response_text a dict. Regenerando el texto...")
    #         prompt += f"""
    #         ---------------------------------------------------------------------------------
    #         [UPDATE PROMPT] No generaste el formato correcto de respuestas.
    #         Por favor, genera las respuestas en un formato JSON.

    #         Habías generado:

    #         "{response_text}"
    #         """
    #         continue  # vuelve a intentar si hay error
    #     except Exception as e:
    #         print(f"Otro error ocurrió: {e}")
    #         break  # rompe el loop si ocurre un error inesperado no relacionado con JSON

    # return "ERROR"

def conditional_evaluation(db_id: str, generated_question: str, threshold: float):
    context = get_context(db_id)
    print("Got context")
    # llm = AzureChatOpenAI(
    #     deployment_name=os.environ["OPENAI_DEPLOYMENT_NAME"],
    #     temperature=0.2
    # )
    
    llm = ChatOpenAI(
        model=MODEL_NAME,
        temperature=0.2
    )
    
    print(f"Evaluating: {generated_question}")
    prompt_template = ChatPromptTemplate.from_template(Q_EVALUATION_PROMPT)
    prompt = prompt_template.format(generated_question=generated_question, context=context)
    response = llm.invoke(prompt).content
    print(f"LLM response: {response}")
    
    return response

def structure_output_metrics(evaluation: str) -> float:
    # grammaticality_pattern = r"Gramaticalidad:\s*((0|1)(\.\d+)?)"
    # appropiateness_pattern = r"Adecuación:\s*((0|1)(\.\d+)?)"
    # relevance_pattern = r"Relevancia:\s*((0|1)(\.\d+)?)"
    # complexity_pattern = r"Complejidad:\s*((0|1)(\.\d+)?)"
    # novelty_pattern = r"Novedad:\s*((0|1)(\.\d+)?)"
    # conciseness_pattern = r"Concisión:\s*((0|1)(\.\d+)?)"
    # ambiguity_pattern = r"Ambigüedad:\s*((0|1)(\.\d+)?)"

    # grammaticality = re.search(grammaticality_pattern, evaluation)
    # appropiateness = re.search(appropiateness_pattern, evaluation)
    # relevance = re.search(relevance_pattern, evaluation)
    # complexity = re.search(complexity_pattern, evaluation)
    # novelty = re.search(novelty_pattern, evaluation)
    # conciseness = re.search(conciseness_pattern, evaluation)
    # ambiguity = re.search(ambiguity_pattern, evaluation)

    # gramamaticality_score = float(grammaticality.group(1)) if grammaticality else 0
    # appropiateness_score = float(appropiateness.group(1)) if appropiateness else 0
    # relevance_score = float(relevance.group(1)) if relevance else 0
    # complexity_score = float(complexity.group(1)) if complexity else 0
    # novelty_score = float(novelty.group(1)) if novelty else 0
    # conciseness_score = float(conciseness.group(1)) if conciseness else 0
    # ambiguity_score = float(ambiguity.group(1)) if ambiguity else 0
    
    # print(f"Grammaticality: {gramamaticality_score} | Appropiateness: {appropiateness_score} | Relevance: {relevance_score} | Complexity: {complexity_score} | Novelty: {novelty_score} | Conciseness: {conciseness_score} | Ambiguity: {ambiguity_score}")

    # average = round((gramamaticality_score + appropiateness_score + relevance_score + complexity_score + novelty_score + conciseness_score + ambiguity_score) / 7, 3)
    
    # return average
    
    clarity_pattern = r"Claridad:\s*((0|1)(\.\d+)?)"
    relevance_pattern = r"Contextualización:\s*((0|1)(\.\d+)?)"
    complexity_pattern = r"Complejidad:\s*((0|1)(\.\d+)?)"
    originality_pattern = r"Originalidad:\s*((0|1)(\.\d+)?)"

    clarity = re.search(clarity_pattern, evaluation)
    relevance = re.search(relevance_pattern, evaluation)
    complexity = re.search(complexity_pattern, evaluation)
    originality = re.search(originality_pattern, evaluation)

    clarity_score = float(clarity.group(1)) if clarity else 0
    relevance_score = float(relevance.group(1)) if relevance else 0
    complexity_score = float(complexity.group(1)) if complexity else 0
    originality_score = float(originality.group(1)) if originality else 0

    print(f"Claridad: {clarity_score} | Contextualización: {relevance_score} | Complejidad: {complexity_score} | Originalidad: {originality_score}")

    average = round((clarity_score + relevance_score + complexity_score + originality_score) / 4, 2)

    return average

def evaluate_quality_tool(db_id: str, generated_question: str, threshold: float):       
    response = conditional_evaluation(db_id, generated_question, threshold)
    similarity = structure_output_metrics(response)
    
    print(f"[SIMILARITY EVALUATION TOOL] Similarity: {similarity}")
    return similarity, response

def refine_question(db_id: str, generated_question: str, feedback: str, quality: float, question_type: int, threshold: float):
    files = ['mcqs', 'oeqs', 'tfqs']
    correct_file = files[question_type - 1]
    generated_questions_list = utils.load_json(db_id, correct_file)

    generated_questions = [question["question"] for question in generated_questions_list]
    generated_questions_string = utils.structure_generated_questions_string(generated_questions)
    
    question_type_to_string = {
        1: "Opción Múltiple",
        2: "Respuesta Abierta",
        3: "Verdadero o Falso"
    }
    
    # llm = AzureChatOpenAI(
    #     deployment_name=os.environ["OPENAI_DEPLOYMENT_NAME"],
    #     temperature=1
    # )
    
    llm = ChatOpenAI(
        model=MODEL_NAME,
        temperature=1
    )
    
    prompt_template = ChatPromptTemplate.from_template(Q_REFINER_PROMPT)
    prompt = prompt_template.format(
        feedback=feedback,
        generated_question=generated_question,
        quality=quality,
        threshold=threshold,
        generated_questions_string=generated_questions_string,
        question_type=question_type_to_string[question_type]
    )
    response = llm.invoke(prompt).content
    print(f"LLM response: {response}")
    return response

def refine_question_tool(db_id: str, generated_question: str, feedback: str, similarity: float, question_type: int, threshold: float):   
    response = refine_question(db_id, generated_question, feedback, similarity, question_type, threshold)
    
    return response

def question_seen_tool(question: dict, question_type: int):
    files = ['mcqs', 'oeqs', 'tfqs']
    correct_file = files[question_type - 1]
    generated_questions_list = utils.load_json(correct_file)

    generated_questions = [question["question"] for question in generated_questions_list]
    
    generated_questions_string = utils.structure_generated_questions_string(generated_questions)
    
    print(f"Evaluating if {question} was already seen...")
        
    seen = any(value == question["question"] for value in generated_questions)
    
    if seen == False:
        prompt = f"""    
        Debes comparar la pregunta: "{question['question']}"
        
        Con cada una de las siguientes preguntas:
            
        `
        {generated_questions_string}
        `
        
        Y determinar si la pregunta ya ha sido generada anteriormente.
        -----------------------------------------------------------------------------------------------------------------------------
        Debes determinar si la pregunta es parecida a alguna otra de las de la lista lista.
        
        ¿De en una escala de 0 a 1 (1 significa que son iguales y 0 significa que son totalmente distintas), es parecida a alguna?

        No me recomiendes cómo sacar los valores. Necesito que tú determines los valores de parecido
        
        Determina un valor de parecido con cada pregunta de la lista.
        
        Sé muy sincero. Si hay alguna parecida, no tengas miedo de dar un valor alto.
        
        Retorna siempre una valoración para cada pregunta y al final la valoración más alta entre todas.
        """

        # llm = AzureChatOpenAI(
        #     deployment_name=os.environ["OPENAI_DEPLOYMENT_NAME"],
        #     temperature=1
        # )
        
        llm = ChatOpenAI(
            model=MODEL_NAME,
            temperature=1
        )
        
        response = llm.invoke(prompt).content
    else:
        response = "1.0"
        
    # print(f"question_seen_tool: {response}")
    matches = re.findall(r'\b\d+\.\d+|\b[01]\b', response)[-1]
    
    print(f"Valoración: {matches}")
    return float(matches)

def question_seen_embeddings_tool(question: dict, question_type: int, threshold: float, hdf5_file='embeddings.h5'):
    # Obtener el modelo de embedding
    embedding_model = chroma_utils.get_embedding_function()
    question_embedding = embedding_model.embed_query(question["question"])

    # Cargar embeddings almacenados
    stored_embeddings = utils.load_embeddings_hdf5(question_type, hdf5_file)

    if len(stored_embeddings) == 0:
        # Si no hay embeddings, guarda el nuevo embedding y retorna
        utils.save_embedding_hdf5(question_embedding, question_type, hdf5_file)
        return 0  # no hay preguntas previas, así que no hay similitud previa

    # Calcular la similitud coseno
    similarities = cosine_similarity([question_embedding], stored_embeddings)
    max_similarity = max(similarities[0])

    if max_similarity < threshold:
        # Si no es lo suficientemente similar, guarda el nuevo embedding
        utils.save_embedding_hdf5(question_embedding, question_type, hdf5_file)

    return max_similarity

def find_most_different_question(db_id: str, questions: list, question_type: int, threshold: float, hdf5_file='embeddings.h5'):
    # Obtener el modelo de embedding
    embedding_model = chroma_utils.get_embedding_function()

    # Cargar embeddings almacenados
    stored_embeddings = utils.load_embeddings_hdf5(question_type, db_id, hdf5_file)

    # Si no hay embeddings almacenados, guarda el primero y retorna
    if len(stored_embeddings) == 0:
        current_question = utils.add_question_marks(questions[0]["question"])
        first_question_embedding = embedding_model.embed_query(current_question)
        utils.save_embedding_hdf5(first_question_embedding, question_type, db_id, hdf5_file)
        return questions[0], 0  # retorna la primera pregunta y similitud 0

    # Inicializamos variables para almacenar la pregunta con menor similitud
    min_similarity = 2
    most_different_question = None

    # Iterar sobre las preguntas y calcular la similitud coseno de cada una
    for question_dict in questions:
        question_text = question_dict["question"]
        question_text = utils.add_question_marks(question_text)
        question_embedding = embedding_model.embed_query(question_text)

        # Calcular la similitud coseno entre el embedding de la pregunta y los almacenados
        similarities = cosine_similarity([question_embedding], stored_embeddings)
        curr_similarity = min(similarities[0]) # encontrar la menor similitud

        print(f"{curr_similarity}")
        # Verificar si la similitud es menor al umbral y si es la menor encontrada hasta ahora
        if curr_similarity < threshold and curr_similarity < min_similarity:
            min_similarity = curr_similarity
            most_different_question = question_dict

    # Si se encontró una pregunta por debajo del umbral, guardar su embedding
    if most_different_question:
        question_embedding = embedding_model.embed_query(most_different_question["question"])
        utils.save_embedding_hdf5(question_embedding, question_type, db_id, hdf5_file)

    # Retornar la pregunta con la menor similitud y su valor
    return most_different_question, min_similarity

def save_question_tool(db_id: str, question: dict, question_type: str):
    utils.update_json(db_id, question_type, question)
    utils.update_json(db_id, 'qs', question)
