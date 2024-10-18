import os
import re
import json
import random
import string
import numpy as np
import pandas as pd
from typing import Dict, List, TypedDict

from pydantic import BaseModel, RootModel

import app.config as config
import app.generator.utils as utils
import app.database.chroma_utils as chroma_utils

from sklearn.metrics.pairwise import cosine_similarity

from langchain_openai import AzureChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain_community.vectorstores import Chroma

from app.prompts.qandas_prompts import Q_MCQ_PROMPT, Q_OAQ_PROMPT, Q_TFQ_PROMPT, \
                                       HARDER_Q_PROMPT, \
                                       A_MCQ_PROMPT, A_OAQ_PROMPT, A_TFQ_PROMPT, \
                                       Q_EVALUATION_PROMPT, TEN_Q_MCQ_PROMPT
                                       

from dotenv import load_dotenv
os.environ["OPENAI_API_KEY"] = config.OPENAI_API_KEY
os.environ["AZURE_OPENAI_ENDPOINT"] = config.AZURE_OPENAI_ENDPOINT
os.environ["OPENAI_API_TYPE"] = config.OPENAI_API_TYPE
os.environ["OPENAI_API_VERSION"] = config.OPENAI_API_VERSION
os.environ["OPENAI_DEPLOYMENT_NAME"] = config.OPENAI_DEPLOYMENT_NAME
load_dotenv()

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
QANDAS_EVALUATION_DATASET = os.path.join(base_dir, 'generator', 'datasets', 'qandas_dataset.csv')
QANDAS_JSONS = os.path.join(base_dir, 'generator', 'q&as')

class FullQuestionOutput(BaseModel):
    question: str
    choices: List[str]
    answer: str

class QuestionOutput(BaseModel):
    question: str
    difficulty: str

class QuestionsOutputList(BaseModel):
    questions: List[QuestionOutput]

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
    # print(generated_questions_string)
    
    llm = AzureChatOpenAI(
        deployment_name=os.environ["OPENAI_DEPLOYMENT_NAME"],
        temperature=0.7,
    )
    
    types = [TEN_Q_MCQ_PROMPT, Q_OAQ_PROMPT, Q_TFQ_PROMPT]
    # types = [QANDA_MCQ_PROMPT, QANDA_OAQ_PROMPT, QANDA_TFQ_PROMPT]
    
    prompt_template = ChatPromptTemplate.from_template(types[question_type - 1])
    prompt = prompt_template.format(context=context, generated_questions=generated_questions_string)

    # response_text = llm.invoke(prompt).content
    # print(f"response_text 1: {response_text}")
    
    structured_llm = llm.with_structured_output(QuestionsOutputList)
    response_text = structured_llm.invoke(prompt)
    # print(f"response_text 2: {response_text}")
    
    return response_text["questions"]

def answer_generator_tool(q_type: int, question: str, difficulty: str, context: str):
    llm = AzureChatOpenAI(
        deployment_name=os.environ["OPENAI_DEPLOYMENT_NAME"],
        temperature=0.7
    )
    
    types = [A_MCQ_PROMPT, A_OAQ_PROMPT, A_TFQ_PROMPT]
    
    print(f'PREGUNTA: {question}')
    prompt_template = ChatPromptTemplate.from_template(types[q_type - 1])
    prompt = prompt_template.format(context=context, question=question, difficulty=difficulty)
    structured_llm = llm.with_structured_output(FullQuestionOutput)
    response_text = structured_llm.invoke(prompt)
    
    choices_dict = utils.choices_list_to_dict(response_text["choices"])
    response_text["choices"] = choices_dict
    
    return response_text    
    
    # for _ in range(10):
    #     try:
    #         response_text = llm.invoke(prompt).content
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

def conditional_evaluation(generated_question, threshold=0.6):
    context = get_context()
    print("Got context")
    llm = AzureChatOpenAI(
        deployment_name=os.environ["OPENAI_DEPLOYMENT_NAME"],
        temperature=0.2
    )
    
    prompt_template = ChatPromptTemplate.from_template(Q_EVALUATION_PROMPT)
    prompt = prompt_template.format(generated_question=generated_question, context=context)
    response = llm.invoke(prompt).content
    # print(f"LLM response: {response}")
    
    return response

def structure_output_metrics(evaluation: str) -> float:
    clarity_pattern = r"Clarity:\s*((0|1)(\.\d+)?)"
    relevance_pattern = r"Relevance:\s*((0|1)(\.\d+)?)"
    complexity_pattern = r"Complexity:\s*((0|1)(\.\d+)?)"
    originality_pattern = r"Originality:\s*((0|1)(\.\d+)?)"

    clarity = re.search(clarity_pattern, evaluation)
    relevance = re.search(relevance_pattern, evaluation)
    complexity = re.search(complexity_pattern, evaluation)
    originality = re.search(originality_pattern, evaluation)

    clarity_score = float(clarity.group(1)) if clarity else 0
    relevance_score = float(relevance.group(1)) if relevance else 0
    complexity_score = float(complexity.group(1)) if complexity else 0
    originality_score = float(originality.group(1)) if originality else 0

    print(f"Clarity: {clarity_score} | Relevance: {relevance_score} | Complexity: {complexity_score} | Originality: {originality_score}")

    average = round((clarity_score + relevance_score + complexity_score + originality_score) / 4, 2)

    return average

def evaluate_similarity_tool(generated_question: str, threshold: float=0.75):      
    response = conditional_evaluation(generated_question, threshold)
    similarity = structure_output_metrics(response)
    
    print(f"[SIMILARITY EVALUATION TOOL] Similarity: {similarity}")
    return similarity, response

def refine_question(generated_question: str, feedback: str, question_type: int):
    files = ['mcqs', 'oaqs', 'tfqs']
    correct_file = files[question_type - 1]
    generated_questions_list = utils.load_json(correct_file)

    generated_questions = [question["question"] for question in generated_questions_list]
    generated_questions_string = utils.structure_generated_questions_string(generated_questions)
    
    question_type_to_string = {
        1: "Opción Múltiple",
        2: "Respuesta Abierta",
        3: "Verdadero o Falso"
    }
    
    refinement_prompt = f"""
    Modifica la siguiente pregunta generada basándote en el feedback proporcionado.
    
    Pregunta generada: "{generated_question}"
    
    Usa este feedback para mejorar la pregunta generada:
    
    "{feedback}"
        
    Modifica la pregunta generada para que las métricas en el feedback promedien 0.75.
    
    ---------------------------------------------------------------------------------
    Es muy importante que la pregunta que generes no sea igual a ninguna pregunta
    en este arreglo de preguntas:

    {generated_questions_string}
    
    ----------------------------------------------------------------------------------
    ¡Haz que la pregunta sea creativa, pero siempre teniendo en cuenta el `contexto`!
    
    ----------------------------------------------------------------------------------
    Nunca cambies el tipo de pregunta!
    
    Tipo de la pregunta: "{question_type_to_string[question_type]}"
        
    ----------------------------------------------------------------------------------
    Nunca retornes la misma pregunta generada. ¡Siempre mejórala!
    
    ----------------------------------------------------------------------------------
    Solo retorna la versión mejorada de la pregunta generada.
    """
    llm = AzureChatOpenAI(
        deployment_name=os.environ["OPENAI_DEPLOYMENT_NAME"],
        temperature=1
    )
    
    response = llm.invoke(refinement_prompt).content
    print(f"Possible refined question: {response}")
    return response

def are_the_same(a: str, b: str) -> bool: 
    prompt = f"""
    Debes comparar dos preguntas para determinar si son iguales o no.
    
    Pregunta A: "{a}"
    
    Pregunta B: "{b}"
    
    ¿De en una escala de 0 a 1 (1 significa que son iguales y 0 significa que son totalmente distintas), qué tan parecidas son estas dos preguntas?
    
    Sé muy sincero. Si son muy parecidas, no tengas miedo de dar un valor alto.
    
    Retorna únicamente el valor de la escala.
    """
    llm = AzureChatOpenAI(
        deployment_name=os.environ["OPENAI_DEPLOYMENT_NAME"],
        temperature=1
    )
    
    response = llm.invoke(prompt).content # Normaliza la respuesta
    # print(f"Are the same: {response}")
    
    return response  # Asegura que el resultado sea booleano

def question_seen_tool(question: str, question_type: int):
    files = ['mcqs', 'oaqs', 'tfqs']
    correct_file = files[question_type - 1]
    generated_questions_list = utils.load_json(correct_file)

    generated_questions = [question["question"] for question in generated_questions_list]
    
    generated_questions_string = utils.structure_generated_questions_string(generated_questions)
    
    prompt = f"""    
    Debes comparar la pregunta: "{question}"
    
    Con cada una de las siguientes preguntas:
        
    `
    {generated_questions_string}
    `
    
    Y determinar si la pregunta ya ha sido generada anteriormente.
    -----------------------------------------------------------------------------------------------------------------------------
    Debes determinar si la pregunta es parecida a alguna otra de las de la lista lista.
    
    ¿De en una escala de 0 a 1 (1 significa que son iguales y 0 significa que son totalmente distintas), es parecida a alguna?
    
    Determina un valor de parecido con cada pregunta de la lista.
    
    Sé muy sincero. Si hay alguna parecida, no tengas miedo de dar un valor alto.
    
    Retorna siempre una valoración para cada pregunta y al final la valoración más alta entre todas.
    """

    llm = AzureChatOpenAI(
        deployment_name=os.environ["OPENAI_DEPLOYMENT_NAME"],
        temperature=1
    )
    
    response = llm.invoke(prompt).content
    print(f"question_seen_tool: {response}")
    matches = re.findall(r'\b\d+\.\d+|\b[01]\b', response)[-1]
    
    return float(matches)
    
def create_new_question_tool(question: str, question_type: int, difficulty: str, context: str):
    files = ['mcqs', 'oaqs', 'tfqs']
    correct_file = files[question_type - 1]
    generated_questions_list = utils.load_json(correct_file)

    generated_questions = [question["question"] for question in generated_questions_list]
    
    generated_questions_string = utils.structure_generated_questions_string(generated_questions)
    
    prompt = f"""    
    Dada la pregunta: "{question}"
    
    Y basándote única y exclusivamente en el contexto:
    
    `
    {context}
    `
    
    Genera una nueva pregunta de opción múltiple de nivel de dificultad {difficulty} basada en la pregunta dada.
    
    Debe ser diferente a las siguientes preguntas:
    
    {generated_questions_string}
    -----------------------------------------------------------------------------------------------------------------------------
    Es importante que, en una escala de 0 a 1, el parecido sea menor que 0.5.
    
    Retorna solo la pregunta.
    """
    
    llm = AzureChatOpenAI(
        deployment_name=os.environ["OPENAI_DEPLOYMENT_NAME"],
        temperature=1
    )
    
    response = llm.invoke(prompt).content
    
    return response

def question_seen_embeddings_tool(a: str, b: str):
    embedding_model = chroma_utils.get_embedding_function()
    a_embedding = embedding_model.embed_query(a)
    b_embedding = embedding_model.embed_query(b)
    
    a_embedding = np.array(a_embedding).reshape(1, -1)
    b_embedding = np.array(b_embedding).reshape(1, -1)
    
    # Calcular la similitud coseno
    similarities = cosine_similarity(a_embedding, b_embedding)
    max_similarity = similarities[0][0]
    
    print(f"Similarity: {max_similarity}")

def save_question_tool(question: dict, question_type: str):
    utils.update_json(question_type, question)
    utils.update_json('qs', question)

def pipeline(question_type: int):
    # primero, genera todas las preguntas en un arreglo
    
    context = get_context()
    questions_list = question_generator_tool(question_type, "Fácil", context)
    for each_question in questions_list:
        print(F"Evaluating question: {each_question['question']}")
        seen = question_seen_tool(each_question["question"], question_type)
        print(f"Valoración de parecido: {seen}")
        new_question = each_question["question"]
        while seen > 0.5:
            new_question = create_new_question_tool(questions_list[0]["question"], question_type, each_question["difficulty"], context)
            print(f"New question: {new_question}")
            seen = question_seen_tool(new_question, question_type)
            print(f"Nueva valoración de parecido: {seen}")
            
        each_question["question"] = new_question
    
    # en un for loop, evaluar cada una y sacar las métricas.
    # las preguntas que no pasen el threshold, refinarlas.
    
    refined_questions = []
    for each_question in questions_list:
        question = each_question["question"]
        print(f"Evaluating question: {question}")
        similarity, response = evaluate_similarity_tool(question)
        
        # si la pregunta no pasa el threshold, refinarla
        refined_question = question
        while similarity < 0.75:
            feedback = response
            refined_question = refine_question(question, feedback, question_type)
            similarity, response = evaluate_similarity_tool(refined_question)
        else:
            refined_questions.append({ "question": refined_question, "difficulty": each_question["difficulty"] })
    
    # print(f"refined_questions: {refined_questions}")
    
    # cuando todas las preguntas pasen el threshold, se generan las respuestas.
    
    questions_final = []
    for each_question in refined_questions:
        question = each_question["question"]
        difficulty = each_question["difficulty"]
        
        context = get_context(question, k=5)
        question_format = str(answer_generator_tool(question_type, question, difficulty, context))
        print(f"question_format: {question_format}")
        double_quotes_string = question_format.replace("'", '"')
        question_format_dict = json.loads(double_quotes_string)

        type_to_string = {
            1: "MCQ",
            2: "OAQ",
            3: "TFQ"
        }
        
        question_format_dict["type"] = type_to_string[question_type]
        question_format_dict["difficulty"] = difficulty
        
        questions_final.append(question_format_dict)
           
    # se guardan las preguntas y las respuestas en archivos JSON.
    for each in questions_final:
        save_question_tool(each, type_to_string[question_type].lower() + 's')
    
if __name__ == "__main__":
    # for _ in range(10):
    #     try:
    #         pipeline(1)  # Opción Múltiple
    #     except Exception as e:
    #         print(f"Error en el pipeline: {e}")
    #         continue
    
    question_seen_embeddings_tool(
        "¿Cuál es el objetivo del programa de Diseño Gráfico en relación a la investigación?",
        # "¿Cuál es la cantidad de créditos académicos requeridos en el programa de Diseño Gráfico?"
        "¿Cuál es el objetivo del programa de Diseño Gráfico en relación a la investigación?"
    )
    
    # with open('app/generator/q&as/qs.json', 'r', encoding='utf-8') as f:
    #     data = json.load(f)["content"]
        
    # # Crear un diccionario para contar cuántas veces aparece cada pregunta
    # question_counts = {}

    # # Recorrer el JSON para contar las preguntas
    # for item in data:
    #     question = item["question"]
    #     if question in question_counts:
    #         question_counts[question] += 1
    #     else:
    #         question_counts[question] = 1

    # # Filtrar el diccionario para quedarte solo con las preguntas que se repiten
    # repeated_questions = {q: count for q, count in question_counts.items() if count > 1}

    # # # Mostrar el diccionario completo de todas las preguntas
    # # print("Todas las preguntas y su cantidad:")
    # # print(question_counts)

    # # # Mostrar solo las preguntas que se repiten
    # # print("\nPreguntas que se repiten:")
    # # print(repeated_questions)
    
    # # print("\nTotal de preguntas en el JSON")
    # # print(len(data))
    
    # repeated_more_than_two = {q: count for q, count in question_counts.items() if count > 1}

    # # Métrica final
    # total_questions = len(data)
    # repeated_more_than_two_count = len(repeated_more_than_two)
    
    # print(f"De {total_questions} preguntas, {repeated_more_than_two_count} se repiten más de dos veces.")
    
    # total_clones = sum(count - 1 for count in repeated_questions.values())
    # print(f"Eso significa que {total_clones} son repetidas")

    # questions = [item['question'] for item in data]

    # # Contador de clones
    # clone_count = 0
    # evaluated_pairs = set()  # Para evitar contar pares repetidos

    # are_equal = are_the_same("¿Cuál es uno de los proyectos de investigación en el área de diseño gráfico y diseño gráfico editorial digital realizados por el programa de Diseño Gráfico?", "¿Cuál es la ciudad en la que se encuentra el Instituto Departamental de Bellas Artes?")
    # print(f"¿Son iguales? {are_equal}")
    
    # seen_float = question_seen_tool("¿Cuál es uno de los proyectos de investigación en el área de diseño gráfico y diseño gráfico editorial digital realizados por el programa de Diseño Gráfico?", 1)
    
    # print(f"¿Vista? (float) {seen_float}")
    # seen = True if float(seen_float) > 0.4 else False
    
    # print(f"¿Vista? {seen}")
        