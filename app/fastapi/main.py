import os
import json
import time
import uuid
import shutil
from typing import List, Optional

from pydantic import BaseModel
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, File, UploadFile, HTTPException

from langchain_core.messages import HumanMessage
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.runnables import RunnableConfig

# from app.agent.state import ChromaDatabase
import app.agent.utils as utils
import app.agent.tools as tools
from app.agent.graph import workflow
import app.generator.loader as loader
import app.generator.generator as generator
import app.generator.utils as generator_utils
import app.database.chroma_utils as chroma_utils
import app.database.sqlite_utils as sqlite_utils
from app.agent.utils import JSON_PATH, load_json

app = FastAPI()

# CORS Configuration

origins = [
    'http://localhost:8080',
    'https://manchita-gamificado.netlify.app',
    'https://urban-space-spoon-7xpxgrq75q93x5x6-8080.app.github.dev'
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.options("/{path:path}")
async def preflight_handler():
    return JSONResponse({"message": "CORS preflight OK"}, headers={
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "OPTIONS, POST",
        "Access-Control-Allow-Headers": "Authorization, Content-Type"
    })
    
@app.get("/")
def home():
    return {"message": "Hello World"}

# ========================= #
# Función de Chat principal #
# ========================= #

story_game_tools = [
    "character",
    "character_first_interaction",
    "character_life_lost",
    "character_success_or_failure",
    "character_loop_interaction",
    "lives_retrieval"
]

user_graphs = {}

def get_or_create_user_graph(thread_id: str, db_id: str, user_name: str):
    global user_graphs
    print(f"THREAD_ID: {thread_id}")
    print(f"DB_ID: {db_id}")
    print(f"USER_NAME: {user_name}")
    
    # Verifica si existe el grafo para el thread_id
    if thread_id not in user_graphs:
        print("CREATING NEW GRAPH")
        checkpointer = MemorySaver()  # Cada usuario tiene su propio MemorySaver
        new_graph = workflow.compile(
            checkpointer=checkpointer,
            interrupt_before=["human_interaction"],  # Especificar nodo de interrupción
        )
        
        utils.generate_graph_image(new_graph)
        
        exists = chroma_utils.knowledge_base_exists(db_id)
        if (exists == False):
            return None
        
        # db = chroma_utils.get_db(db_id)
        # db_obj = ChromaDatabase(
        #     db_id=db_id
        # )
        
        # Establecer el estado inicial del grafo con el thread_id
        initial_state = {
            "thread_id": thread_id,
            "db_chroma": db_id,
            "db_sqlite": db_id,
            "user_name": user_name,
            "from_story": False,
            "messages": []
        }
        
        new_graph.update_state({"configurable": {"thread_id": thread_id}}, initial_state)
        
        user_graphs[thread_id] = new_graph
    else:
        print("USING EXISTING GRAPH")

    print(f"TOTAL GRAPHS: {len(user_graphs)}")
    return user_graphs[thread_id]

class ChatInput(BaseModel):
    query: str
    thread_id: str = None
    db_id: Optional[str] = None
    user_name: Optional[str] = None
    user_answer: Optional[str] = None  # Campo "opcional" para manejar la interrupción

@app.post("/chat")
async def chat(input_data: ChatInput):
    """
    Para manejar el Human-in-the-loop, lo que se hace es
    mandar relativamente a la fuerza en el JSON un indicador
    de que hay una interrupción en el flujo. ¡Con eso, se puede
    manejar luego desde le front los mensajes que se mandan!
    
    Ejemplo de JSON:
    Primera interacción:

    {
        "query": "hazme una pregunta!",
        "thread_id": "a0d043ad-a1f2-41ce-833b-94c37cf232ee"
    }
    
    Acá, el backend manda pone true el campo "is_interrupted".
    
    Interrupción (se agrega el campo de "user_answer"):
    {
        "query": "hazme una pregunta!",
        "thread_id": "a0d043ad-a1f2-41ce-833b-94c37cf232ee",
        "user_answer": "es algo de 2008?"
    }

    """
    
    # Generar o reutilizar el 'thread_id'
    if input_data.thread_id is None or input_data.thread_id == "":
        input_data.thread_id = str(uuid.uuid4())
    
    thread = {
        "configurable": {
            "thread_id": input_data.thread_id,
        }
    }
    
    config = RunnableConfig(
        thread_id=input_data.thread_id,
        recursion_limit=15
    )
    
    print(input_data)
    graph = get_or_create_user_graph(input_data.thread_id, input_data.db_id, input_data.user_name)
    print(f"GRAPH: {input_data.thread_id} - {graph.get_state(thread).next}")
    print(f"INPUT DATA: {input_data}")

    try:
        # Si hay una respuesta del usuario tras la interrupción
        if input_data.user_answer:
            print("USER ANSWER")
            state = graph.get_state(thread)

            to_evaluate = state.values['current_story']["to_evaluate"] if 'current_story' in state.values else ''
            last_question = graph.get_state(thread).values["last_question"] if state.values['messages'][-1].name == "qanda_chooser" else to_evaluate  # pregunta sencilla o pregunta de juego goblin
            combined_input = f"{last_question}|||{input_data.user_answer}"
            
            # Actualizar el estado del grafo con la respuesta
            graph.update_state(
                thread, 
                {
                    'messages': [
                        HumanMessage(content=combined_input),
                    ],
                    'last_question': last_question,
                },
                as_node="human_interaction"
            )
            
            # Continuar el flujo después de la interrupción
            evaluation_response = []
            for event in graph.stream(None, config, stream_mode="values"):
                evaluation_response.append(event['messages'][-1].content)
            
            print(f"EVALUATION RESPONSE: {evaluation_response}")
            print(f"EVALUATION RESPONSE: {graph.get_state(thread).values['from_story']}")
            print(f"EVALUATION RESPONSE: {'incorrecta' in evaluation_response[-3]}")
            
            return {
                "thread_id": input_data.thread_id,
                "response": evaluation_response[-1].split("|||")[0] if '|||' in evaluation_response[-1] else evaluation_response[-1],
                "is_interrupted": graph.get_state(thread).values["from_story"]
            }
        
        # Si es una interacción inicial (sin interrupción todavía)
        else:
            print("SIMPLE INTERACTION")
            
            # Procesar la interacción inicial
            response = []
            for event in graph.stream({"messages": [HumanMessage(content=input_data.query)]}, config, stream_mode="values"):
                response.append(event['messages'][-1].content)

            # Verificar si el flujo fue interrumpido en 'human_interaction'
            state = graph.get_state(thread)
            last_tool_call = state.values['messages'][-1].name if state.values['messages'][-1].name is not None else list(state.metadata['writes'].keys())[0]
            print(f"LAST TOOL CALL: {hasattr(state.values['messages'][-1], 'name')} - {state.values['messages'][-1].name}")
            print(f"LAST TOOL CALL: {last_tool_call}")
            
            is_interrupted = False
            if last_tool_call:
                is_interrupted = last_tool_call == "qanda_chooser" or last_tool_call in story_game_tools
            
            return {
                "thread_id": input_data.thread_id,
                "response": response[-1],
                "is_interrupted": is_interrupted  # Verifica si se requiere input del usuario
            }
    except Exception as e:
        print(f"ERROR: {e}")
        return {
            "thread_id": input_data.thread_id,
            "response": "Lo siento, no pude procesar tu solicitud."
        }

# ========================================== #
# Endpoints para Juego de Construir la Torre #
# ========================================== #

class QuestionEvaluation(BaseModel):
    question: str
    answer: str

@app.get('/questions/{db_id}')
def get_questions(db_id: str):
    # data = load_json(JSON_PATH) # cambiar constante de rutas
    json_path = os.path.join(chroma_utils.DATABASES_PATH, db_id, 'q&as', 'qs.json')
    data = load_json(json_path)
    
    # solo para preguntas de "Verdadero o Falso"
    questions = [item["question"] for item in data if item["type"] == "TFQ"]
    return questions

@app.post('/evaluate/{db_id}')
def evaluate_query(input: QuestionEvaluation, db_id: str):
    evaluation = tools.qanda_evaluation(f"{input.question}|||{input.answer}", "simple_quiz", db_id)
    return {"evaluation": False if "incorrecta" in evaluation else True}

# ======================================= #
# Endpoint para los contadores de puntos #
# ======================================= #

@app.get('/user_points_counter/{user_id}/{db_id}')
def get_user_asked_questions(user_id: str, db_id: str):
    print(f"GETTING POINTS COUNTER FOR USER_ID: {user_id} IN {db_id}")
    return {
        'asked_questions': tools.asked_questions_retrieval(user_id, db_id),
        'current_points': tools.points_only_retrieval(user_id, db_id)
    }
    
# ================================================================= #
# Endpoint para verificar la existencia de una base de conocimiento #
# ================================================================= #

@app.get('/knowledge_base_exists/{bd_id}')  
def knowledge_base_exists(bd_id: str):
    return { 'database_path': chroma_utils.knowledge_base_exists(bd_id) }

# ==================================== #
# Endpoint para hacer la carga de PDFs #
# ==================================== #

@app.post("/upload_file")
async def upload_pdf(files1: List[UploadFile] = File(...), files2: Optional[List[UploadFile]] = File([])):
    db_id = chroma_utils.generate_bd_id()
    print(f"DB_ID: {db_id}")
    
    files_location = os.path.join(chroma_utils.DATABASES_PATH, db_id, 'files')
    chroma_path = os.path.join(chroma_utils.DATABASES_PATH, db_id, 'knowledge')
    
    chroma_utils.verify_directory_exists(chroma_path)
    chroma_utils.verify_directory_exists(files_location)
    chroma_utils.verify_directory_exists(os.path.join(chroma_utils.DATABASES_PATH, db_id, 'q&as'))
    chroma_utils.verify_directory_exists(os.path.join(chroma_utils.DATABASES_PATH, db_id, 'embeddings'))
    
    for file in files1:
        # Validar que cada archivo sea un PDF o un archivo de Word
        if file.content_type not in ["application/pdf", "application/vnd.openxmlformats-officedocument.wordprocessingml.document", "application/msword"]:
            raise HTTPException(status_code=400, detail=f"El archivo '{file.filename}' no es un PDF ni un archivo de Word.")

        # Guardar el archivo temporalmente en el servidor
        file_location = os.path.join(files_location, file.filename)
        
        with open(file_location, "wb") as f:
            shutil.copyfileobj(file.file, f)

        # Carga el archivo a la base de conocimiento
        loader.main_load(chroma_path, file_location)
        
        # Elimina el archivo temporal
        os.remove(file_location)    
        
    if len(files2) == 0:
        # Generar el archivo JSON con las preguntas y respuestas
        quality_threshold = 0.82
        mcq_similarity_threshold = 0.8
        tfq_similarity_threshold = 0.8
        number_of_questions = 20

        start_time = time.time()  # Tiempo de inicio
        
        print('--- GENERATING Q&AS ---')
        generator.generate_qandas(mcq_similarity_threshold, tfq_similarity_threshold, quality_threshold, db_id, number_of_questions)
        
        end_time = time.time()  # Tiempo de finalización
        elapsed_time = end_time - start_time  # Tiempo total en segundos

        print('--- DONE ---')
        print(f"Tiempo total de ejecución: {elapsed_time:.2f} segundos")
    else:
        files_location = os.path.join(chroma_utils.DATABASES_PATH, db_id, 'external')
        chroma_utils.verify_directory_exists(files_location)
        
        for file in files2:
            file_location = os.path.join(files_location, file.filename)
            print(f"FILE LOCATION: {file_location}")
            
            with open(file_location, "wb") as f:
                shutil.copyfileobj(file.file, f)
        
            ext = os.path.splitext(file.filename)[-1].lower()
            print(f"EXTENSION: {ext}")
            if ext != '.json':
                generator.format_qandas_from_external_document(db_id, file.filename)
            else:
                path = os.path.join(files_location, file.filename)
                data = utils.load_json(path)
                for question in data:
                    generator_utils.update_json(db_id, 'qs', question)
                
            os.remove(file_location)
    
    sqlite_utils.create_table(db_id)
    
    qandas_json_path = os.path.join(chroma_utils.DATABASES_PATH, db_id, 'q&as', 'qs.json')
    with open(qandas_json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # data["content"].append({ "code": db_id })
    data["content"].insert(0, { "code": db_id })
    
    print(f"DATA: {data}")
        
    return data
