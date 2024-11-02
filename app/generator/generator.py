import os
from typing import Dict, List, Literal

from pydantic import BaseModel
from langchain.prompts import ChatPromptTemplate
from langchain_openai import AzureChatOpenAI, ChatOpenAI
from langchain_community.document_loaders.pdf import PyPDFDirectoryLoader
from langchain_community.document_loaders import UnstructuredWordDocumentLoader

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
    # print(f"📄 Document loaded: {document_string}")
    
    prompt_template = ChatPromptTemplate.from_template(FORMAT_QANDAS_PROMPT)
    prompt = prompt_template.format(document_string=document_string)
    
    structured_llm = llm.with_structured_output(PdfOuputList)
    response_text = structured_llm.invoke(prompt)
    
    # print(f"📄 Response: {response_text} - {type(response_text)}")
    
    for question in response_text["questions"]:
        utils.update_json(db_id, 'qs', question)
    
    return response_text

def generate_qandas(mcq_similarity_threshold: float, tfq_similarity_threshold: float, quality_threshold: float, db_id: str):
    # eliminamos el contenido de los archivos de persistencia de embeddings
    utils.delete_all_content_hdf5(db_id, hdf5_file='embeddings.h5')
    
    # preguntas "Opción Múltiple"
    print("Generating MCQs...")
    for i in range(1, 21): # 21
        question_type = 1
        if (i % 3 == 0):
            question_difficulty_int = 1
        else:
            question_difficulty_int = 2
    
        try:
            graph.use_graph(
                question_type,
                question_difficulty_int,
                mcq_similarity_threshold,
                quality_threshold,
                db_id
            )
            # time.sleep(120)
            pass
        except Exception as e:
            print(f"Error al cargar la pregunta {i}: {e}")
            continue
    
    # preguntas "Verdadero o Falso"
    print("Generating TFQs...")
    for i in range(1, 11): # 11
        question_type = 3
        if (i % 3 == 0):
            question_difficulty_int = 1
        else:
            question_difficulty_int = 2
     
        try:
            graph.use_graph(
                question_type,
                question_difficulty_int,
                tfq_similarity_threshold,
                quality_threshold,
                db_id
            )
            # time.sleep(30)
        except Exception as e:
            print(f"Error al cargar la pregunta {i}: {e}")
            continue
    
    # preguntas de Respuesta Abierta
    print("Generating OEQs...")
    for i in range(1, 11): # 11
        question_type = 2
        if (i % 3 == 0):
            question_difficulty_int = 1
        else:
            question_difficulty_int = 2
     
        try:
            graph.use_graph(
                question_type,
                question_difficulty_int,
                tfq_similarity_threshold,
                quality_threshold,
                db_id
            )
            # time.sleep(30)
        except Exception as e:
            print(f"Error al cargar la pregunta {i}: {e}")
            continue
    
    # eliminamos el contenido de los archivos de persistencia de embeddings
    utils.delete_all_content_hdf5(db_id, hdf5_file='embeddings.h5')

# if __name__ == "__main__":
#     quality_threshold = 0.82
#     mcq_similarity_threshold = 0.8
#     tfq_similarity_threshold = 0.8
#     print('--- GENERATING FOR FIRST DATABASE ---')
#     generate_qandas(mcq_similarity_threshold, tfq_similarity_threshold, quality_threshold, db_id='TXVHBV')
#     print('--- GENERATING FOR SECOND DATABASE ---')
#     generate_qandas(mcq_similarity_threshold, tfq_similarity_threshold, quality_threshold, db_id='XLAVUD')
#     print('--- GENERATING FOR THIRD DATABASE ---')
#     generate_qandas(mcq_similarity_threshold, tfq_similarity_threshold, quality_threshold, db_id='YNHXDE')
#     print('--- DONE ---')