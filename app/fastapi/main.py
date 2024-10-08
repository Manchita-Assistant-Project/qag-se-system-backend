import json
import uuid
from typing import Optional

from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from langchain_core.messages import HumanMessage
from langgraph.checkpoint.memory import MemorySaver

from app.graph.utils import JSON_PATH
from app.graph.graph import workflow
from app.graph.tools import qanda_evaluation

app = FastAPI()

# CORS Configuration

origins = [
    'http://localhost:8080',
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

class ChatInput(BaseModel):
    query: str
    thread_id: str = None
    user_answer: Optional[str] = None  # Campo "opcional" para manejar la interrupción

story_game_tools = [
    "first_character",
    "second_character",
    "third_character",
    "lifes_retrieval",
]
user_graphs = {}

def get_or_create_user_graph(thread_id):
    global user_graphs
    print(f"THREAD_ID: {thread_id}")
    
    # Verifica si existe el grafo para el thread_id
    if thread_id not in user_graphs:
        print("CREATING NEW GRAPH")
        checkpointer = MemorySaver()  # Cada usuario tiene su propio MemorySaver
        new_graph = workflow.compile(
            checkpointer=checkpointer,
            interrupt_before=["human_interaction"],  # Especificar nodo de interrupción
        )
        
        # Establecer el estado inicial del grafo con el thread_id
        initial_state = {"thread_id": thread_id, "messages": [], "step": 0}
        new_graph.update_state({"configurable": {"thread_id": thread_id}}, initial_state)
        
        user_graphs[thread_id] = new_graph
    else:
        print("USING EXISTING GRAPH")

    print(f"TOTAL GRAPHS: {len(user_graphs)}")
    return user_graphs[thread_id]

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
    
    graph = get_or_create_user_graph(input_data.thread_id)

    print(f"INPUT DATA: {input_data}")

    # try:
    # Si hay una respuesta del usuario tras la interrupción
    if input_data.user_answer:
        print("USER ANSWER")
        state = graph.get_state(thread)

        to_evaluate = state.values['current_story']["to_evaluate"] if 'current_story' in state.values else ''
        last_question = state.values['messages'][-1].content if state.values['messages'][-1].content.startswith('¿') else to_evaluate  # pregunta sencilla o pregunta de juego goblin
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
        for event in graph.stream(None, thread, stream_mode="values"):
            evaluation_response.append(event['messages'][-1].content)
        
        print(f"EVALUATION RESPONSE: {evaluation_response}")
        
        return {
            "thread_id": input_data.thread_id,
            "response": evaluation_response[-1].split("|||")[0] if '|||' in evaluation_response[-1] else evaluation_response[-1],
            "is_interrupted": graph.get_state(thread).values["from_story"] and "incorrecta" in evaluation_response[-2]
        }
    
    # Si es una interacción inicial (sin interrupción todavía)
    else:
        print("SIMPLE INTERACTION")
        # graph.update_state(thread, {"thread_id": input_data.thread_id})
        
        # Procesar la interacción inicial
        response = []
        for event in graph.stream({"messages": [HumanMessage(content=input_data.query)]}, thread, stream_mode="values"):
            response.append(event['messages'][-1].content)

        # Verificar si el flujo fue interrumpido en 'human_interaction'
        last_tool_call = graph.get_state(thread).values['messages'][-1].name
        print(f"LAST TOOL CALL: {last_tool_call}")
        is_interrupted = False
        if last_tool_call:
            is_interrupted = last_tool_call == "qanda_chooser" or last_tool_call in story_game_tools
        
        return {
            "thread_id": input_data.thread_id,
            "response": response[-1],
            "is_interrupted": is_interrupted  # Verifica si se requiere input del usuario
        }
    # except Exception as e:
    #     print(f"ERROR: {e}")
    #     return {
    #         "thread_id": input_data.thread_id,
    #         "response": "Lo siento, no pude procesar tu solicitud."
    #     }

# IMPORTANTE CAMBIAR EL CÓDIGO A CREAR UN GRAFO POR ENTRADA/LLAMADA AL SERVIDOR!!
# HAY QUE PENSAR SI QUEREMOS QUE PERSISTAN... CON IP O ASÍ JEJE...
# EL TEMA ES QUE SE PUEDEN DEMORAR MIENTRAS COMPILAN... PERO NAH, NO ES NUESTRA PREOCUPACIÓN.

class QuestionEvaluation(BaseModel):
    question: str
    answer: str

@app.get('/questions')
def get_questions():    
    with open(JSON_PATH, encoding='utf-8') as f:
        data = json.load(f)
    
    questions = {question["question"] for question in data["content"][0]["questions"]}
    return questions

@app.post('/evaluate')
def evaluate_query(input: QuestionEvaluation):
    evaluation = qanda_evaluation(f"{input.question}|||{input.answer}")
    return {"evaluation": False if "incorrecta" in evaluation else True}
    