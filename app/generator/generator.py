import os
import time
import tempfile
from typing import Dict, List, Literal
from concurrent.futures import ThreadPoolExecutor


from pydantic import BaseModel
from langchain.prompts import ChatPromptTemplate
from langchain_openai import AzureChatOpenAI, ChatOpenAI

import app.config as config
import app.generator.utils as utils
import app.generator.graph as graph

from app.prompts.qandas_prompts import FORMAT_QANDAS_PROMPT

from dotenv import load_dotenv
os.environ["OPENAI_API_KEY"] = config.OPENAI_API_KEY
os.environ["AZURE_OPENAI_ENDPOINT"] = config.AZURE_OPENAI_ENDPOINT
os.environ["OPENAI_API_TYPE"] = config.OPENAI_API_TYPE
os.environ["OPENAI_API_VERSION"] = config.OPENAI_API_VERSION
os.environ["OPENAI_DEPLOYMENT_NAME"] = config.OPENAI_DEPLOYMENT_NAME
MODEL_NAME = config.OPENAI_MODEL_4OMINI
load_dotenv()

class PdfOuput(BaseModel):
    question: str
    choices: dict
    answer: str
    type: Literal["MCQ", "TFQ", "OEQ"]
    difficulty: Literal["Fácil", "Difícil"]	

class PdfOuputList(BaseModel):
    questions: List[PdfOuput]

def format_qandas_from_external_document(db_id: str, filename: str):
    llm = ChatOpenAI(
        model_name=MODEL_NAME,
        temperature=0.2,
    )
    
    path = os.path.join(utils.DATABASES_PATH, db_id, 'external', filename)
    loaded_document = utils.load_documents(path)
    document_string = "\n".join([doc.page_content for doc in loaded_document])
    
    prompt_template = ChatPromptTemplate.from_template(FORMAT_QANDAS_PROMPT)
    prompt = prompt_template.format(document_string=document_string)
    
    structured_llm = llm.with_structured_output(PdfOuputList)
    response_text = structured_llm.invoke(prompt)
    
    for question in response_text["questions"]:
        utils.update_json(db_id, 'qs', question)
    
    return response_text

# def generate_qandas(mcq_similarity_threshold: float, tfq_similarity_threshold: float, quality_threshold: float, db_id: str):
#     # eliminamos el contenido de los archivos de persistencia de embeddings
#     utils.delete_all_content_hdf5(db_id, hdf5_file='embeddings.h5')
    
#     # preguntas "Opción Múltiple"
#     print("Generating MCQs...")
#     for i in range(1, 4): # 21
#         question_type = 1
#         if (i % 3 == 0):
#             question_difficulty_int = 1
#         else:
#             question_difficulty_int = 2
    
#         try:
#             graph.use_graph(
#                 question_type,
#                 question_difficulty_int,
#                 mcq_similarity_threshold,
#                 quality_threshold,
#                 db_id
#             )
#             # time.sleep(120)
#             pass
#         except Exception as e:
#             print(f"Error al cargar la pregunta {i}: {e}")
#             continue
    
#     # preguntas "Verdadero o Falso"
#     print("Generating TFQs...")
#     for i in range(1, 4): # 21
#         question_type = 3
#         if (i % 3 == 0):
#             question_difficulty_int = 1
#         else:
#             question_difficulty_int = 2
     
#         try:
#             graph.use_graph(
#                 question_type,
#                 question_difficulty_int,
#                 tfq_similarity_threshold,
#                 quality_threshold,
#                 db_id
#             )
#             # time.sleep(30)
#         except Exception as e:
#             print(f"Error al cargar la pregunta {i}: {e}")
#             continue
    
#     # preguntas de Respuesta Abierta
#     print("Generating OEQs...")
#     for i in range(1, 4): # 21
#         question_type = 2
#         if (i % 3 == 0):
#             question_difficulty_int = 1
#         else:
#             question_difficulty_int = 2
     
#         try:
#             graph.use_graph(
#                 question_type,
#                 question_difficulty_int,
#                 tfq_similarity_threshold,
#                 quality_threshold,
#                 db_id
#             )
#             # time.sleep(30)
#         except Exception as e:
#             print(f"Error al cargar la pregunta {i}: {e}")
#             continue
    
#     # eliminamos el contenido de los archivos de persistencia de embeddings
#     utils.delete_all_content_hdf5(db_id, hdf5_file='embeddings.h5')

def generate_mcqs(mcq_similarity_threshold, quality_threshold, db_id, number_of_questions):
    print("Generating MCQs...")
    temp_files = []
    
    for i in range(1, number_of_questions + 1):  # Cambia a 21 en producción
        question_type = 1
        question_difficulty_int = 1 if i % 3 == 0 else 2
        try:
            temp_filename = graph.use_graph(
                question_type,
                question_difficulty_int,
                mcq_similarity_threshold,
                quality_threshold,
                db_id
            )
            print(f"Temp filename: {temp_filename}")
            temp_files.append(temp_filename)  # Guarda el archivo temporal para fusionarlo luego
        except Exception as e:
            print(f"Error al cargar la pregunta {i}: {e}")
    
    return temp_files

def generate_tfqs(tfq_similarity_threshold, quality_threshold, db_id, number_of_questions):
    print("Generating TFQs...")
    temp_files = []
    
    for i in range(1, number_of_questions + 1):  # Cambia a 21 en producción
        question_type = 3
        question_difficulty_int = 1 if i % 3 == 0 else 2
        try:
            temp_filename = graph.use_graph(
                question_type,
                question_difficulty_int,
                tfq_similarity_threshold,
                quality_threshold,
                db_id
            )
            temp_files.append(temp_filename)
        except Exception as e:
            print(f"Error al cargar la pregunta {i}: {e}")
    
    return temp_files

def generate_oeqs(tfq_similarity_threshold, quality_threshold, db_id, number_of_questions):
    print("Generating OEQs...")
    temp_files = []
    
    for i in range(1, number_of_questions + 1):  # Cambia a 21 en producción
        question_type = 2
        question_difficulty_int = 1 if i % 3 == 0 else 2
        try:
            temp_filename = graph.use_graph(
                question_type,
                question_difficulty_int,
                tfq_similarity_threshold,
                quality_threshold,
                db_id
            )
            temp_files.append(temp_filename)
        except Exception as e:
            print(f"Error al cargar la pregunta {i}: {e}")
    
    return temp_files

def generate_qandas(mcq_similarity_threshold, tfq_similarity_threshold, quality_threshold, db_id, number_of_questions):
    utils.delete_all_content_hdf5(db_id, hdf5_file='embeddings.h5')
    
    # Ejecuta las funciones de generación en paralelo
    temp_files = []
    with ThreadPoolExecutor() as executor:
        futures = [
            executor.submit(generate_mcqs, mcq_similarity_threshold, quality_threshold, db_id, number_of_questions),
            executor.submit(generate_tfqs, tfq_similarity_threshold, quality_threshold, db_id, number_of_questions),
            executor.submit(generate_oeqs, tfq_similarity_threshold, quality_threshold, db_id, number_of_questions)
        ]
        
        # Recoge todos los archivos temporales generados por cada función
        for future in futures:
            temp_files.extend(future.result())
    
    # Fusiona los archivos temporales en el JSON principal
    main_json_path = os.path.join(utils.DATABASES_PATH, db_id, 'q&as', 'qs.json')
    utils.merge_temp_files(temp_files, main_json_path)
    
    utils.delete_all_content_hdf5(db_id, hdf5_file='embeddings.h5')

# if __name__ == "__main__":
#     db_id = 'UDXQOG'
#     quality_threshold = 0.82
#     mcq_similarity_threshold = 0.8
#     tfq_similarity_threshold = 0.8
#     number_of_questions = 1
    
#     start_time = time.time()  # Tiempo de inicio
    
#     print('--- GENERATING Q&AS ---')
#     generate_qandas(mcq_similarity_threshold, tfq_similarity_threshold, quality_threshold, db_id, number_of_questions)
    
#     end_time = time.time()  # Tiempo de finalización
#     elapsed_time = end_time - start_time  # Tiempo total en segundos

#     print('--- DONE ---')
#     print(f"Tiempo total de ejecución: {elapsed_time:.2f} segundos")