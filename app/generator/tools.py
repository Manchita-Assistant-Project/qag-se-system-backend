import os
import re
import json
import random
import pandas as pd

import app.config as config
import app.generator.utils as utils
import app.database.chroma_utils as chroma_utils

from sklearn.metrics.pairwise import cosine_similarity

from langchain_openai import AzureChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain_community.vectorstores import Chroma

from app.prompts.tools_prompts import Q_MCQ_PROMPT, HARDER_Q_PROMPT, A_MCQ_PROMPT

from dotenv import load_dotenv
os.environ["OPENAI_API_KEY"] = config.OPENAI_API_KEY
os.environ["AZURE_OPENAI_ENDPOINT"] = config.AZURE_OPENAI_ENDPOINT
os.environ["OPENAI_API_TYPE"] = config.OPENAI_API_TYPE
os.environ["OPENAI_API_VERSION"] = config.OPENAI_API_VERSION
os.environ["OPENAI_DEPLOYMENT_NAME"] = config.OPENAI_DEPLOYMENT_NAME
load_dotenv()

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
QANDAS_EVALUATION_DATASET = os.path.join(base_dir, 'generator', 'datasets', 'qandas_dataset.csv')

def load_dataset(path: str) -> pd.DataFrame:
    return pd.read_csv(path, sep=";")

def get_context(query: str="", k: int=90):
    embedding_function = chroma_utils.get_embedding_function()
    db = Chroma(persist_directory=chroma_utils.CHROMA_PATH, embedding_function=embedding_function)
    
    # Search the DB -> top k most relevant chunks to the query.
    results = db.similarity_search_with_score(query, k)

    context_text = "\n\n---\n\n".join([doc.page_content for doc, _score in results])

    return context_text

def get_context_tool(query: str="", k: int=90):
    context = get_context(query, k)
    return context

def question_generator_tool(q_type: int, difficulty: str, context: str):
    generated_questions = utils.load_json("app/generator/q&as/qs.json")
    llm = AzureChatOpenAI(
        deployment_name=os.environ["OPENAI_DEPLOYMENT_NAME"],
        temperature=0.7,
        max_tokens=200
    )
    
    types = [Q_MCQ_PROMPT]
    # types = [QANDA_MCQ_PROMPT, QANDA_OAQ_PROMPT, QANDA_TFQ_PROMPT]
    
    prompt_template = ChatPromptTemplate.from_template(types[q_type - 1])
    prompt = prompt_template.format(context=context, difficulty=difficulty, harder_prompt="", generated_questions=generated_questions)

    response_text = llm.invoke(prompt).content
    print(f"response_text: {response_text}")
    
    if difficulty == 'Difícil':
        rand_int = random.randint(1, 5) # cinco niveles de dificultad
        print(f"rand_int: {rand_int}")
        harder_prompt_template = ChatPromptTemplate.from_template(HARDER_Q_PROMPT)
        for _ in range(rand_int): # iterar para hacer la pregunta para hacerla más difícil
            harder_prompt = harder_prompt_template.format(question=response_text, context=context)
            response_text = llm.invoke(harder_prompt).content
    
    return response_text

def answer_generator_tool(q_type: int, question: str, difficulty: str, context: str):
    llm = AzureChatOpenAI(
        deployment_name=os.environ["OPENAI_DEPLOYMENT_NAME"],
        temperature=0.7,
        max_tokens=200
    )
    
    types = [A_MCQ_PROMPT]
    # types = [QANDA_MCQ_PROMPT, QANDA_OAQ_PROMPT, QANDA_TFQ_PROMPT]
    print(f'PREGUNTA: {question}')
    prompt_template = ChatPromptTemplate.from_template(types[q_type - 1])
    prompt = prompt_template.format(context=context, question=question, difficulty=difficulty)

    while True:
        try:
            response_text = llm.invoke(prompt).content
            response_dict = json.loads(response_text)  # intentamos convertir el texto a dict
            return response_text
        except json.JSONDecodeError:
            print("Error al convertir response_text a dict. Regenerando el texto...")
            continue  # vuelve a intentar si hay error
        except Exception as e:
            print(f"Otro error ocurrió: {e}")
            break  # rompe el loop si ocurre un error inesperado no relacionado con JSON

    return None

def evaluate_with_embeddings(human_questions, generated_question):
    embeddings = chroma_utils.get_embedding_function()

    # embedding de la pregunta generada
    embedding_generated = embeddings.embed_query(generated_question)

    similarities = []
    for human_question in human_questions:
        # embedding de la pregunta humana
        embedding_human = embeddings.embed_query(human_question)

        similarity = cosine_similarity([embedding_human], [embedding_generated])[0][0]
        similarities.append(similarity)
        print(f"Similarity with '{human_question}': {similarity}")
    
    avg_similarity = sum(similarities) / len(similarities)

    return avg_similarity

# Usar LLM solo si la similitud cae por debajo de un umbral
def conditional_evaluation(human_questions, generated_question, threshold=0.6):
    context = get_context()
    print("Got context")
    # similarity = evaluate_with_embeddings(human_questions, generated_question)
    similarity = 0.5
    # print(f"[C. E. Function] Similarity: {similarity}")
    if similarity < threshold:  # Si la similitud es baja, pedirle al LLM una evaluación más profunda
        evaluation_prompt = f"""
        Evaluate the following generated question.
        
        Generated question: "{generated_question}"

        Use this context to evaluate the generated question:
        
        "{context}"

        Evaluate the generated question based on:
        - Clarity
        - Relevance
        - Complexity
        - Originality
        
        If the generated question is a common question that could be asked about any program, penalize originality.

        Provide a score from 0 to 1 for each criterion and a brief explanation for your scoring.
        """
        llm = AzureChatOpenAI(
            deployment_name=os.environ["OPENAI_DEPLOYMENT_NAME"],
            temperature=0.2,
            max_tokens=200
        )
        
        response = llm.invoke(evaluation_prompt).content
        # print(f"LLM response: {response}")
        return response
    else:
        return f"High similarity detected ({similarity}), skipping LLM evaluation."

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

def evaluate_similarity_tool(generated_question: str, dataset_path: str=QANDAS_EVALUATION_DATASET, threshold: float=0.8):
    dataset = load_dataset(dataset_path)
    human_questions = dataset["Pregunta"].to_list()
       
    response = conditional_evaluation(human_questions, generated_question, threshold)
    similarity = structure_output_metrics(response)
    
    print(f"[SIMILARITY EVALUATION TOOL] Similarity: {similarity}")
    return similarity, response

def refine_question(human_questions: str, generated_question: str, feedback: str):
    refinement_prompt = f"""
    Modify the following generated question based on the feedback provided.
    
    Generated question: "{generated_question}"
    
    Use this feedback to improve the generated question:
    
    "{feedback}"
        
    Modify the generated question, so that the metrics in the feedback average 0.75.
    
    ¡Never translate the improved question! ¡Always return it in spanish!
    
    ¡Never return the exact same generated question! ¡Always improve it!
    
    Return only the improved version of the generated question.
    """
    llm = AzureChatOpenAI(
        deployment_name=os.environ["OPENAI_DEPLOYMENT_NAME"],
        temperature=1
    )
    
    response = llm.invoke(refinement_prompt).content
    print(f"LLM response: {response}")
    return response

def refine_question_tool(generated_question: str, feedback: str, dataset_path: str=QANDAS_EVALUATION_DATASET):
    dataset = load_dataset(dataset_path)
    human_questions = dataset["Pregunta"].to_list()
    
    response = refine_question(human_questions, generated_question, feedback)
    
    return response

def classify_question(generated_question: str, context: str):
    refinement_prompt = f"""
    Classify the following generated question based on the context provided.
    
    The three classes are:
    - Easy
    - Medium
    - Hard 
        
    Generated question: "{generated_question}"

    Use this contexto to classify the generated question:
    
    "{context}"
    
    Return only the class of the generated question.    
    """
    llm = AzureChatOpenAI(
        deployment_name=os.environ["OPENAI_DEPLOYMENT_NAME"],
        temperature=0.8,
        max_tokens=200
    )
    
    response = llm.invoke(refinement_prompt).content
    print(f"LLM response: {response}")
    return response

def classify_question_tool(generated_question: str, context: str):
    response = classify_question(generated_question, context)
    
    return response
