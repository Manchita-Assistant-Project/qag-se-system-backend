from app.generator import utils
import app.generator.config as config
from app.generator.agents_graph import State, qanda_evaluation

import os
import uuid
import random
from typing import List
from langchain_openai import AzureChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import Runnable, RunnableConfig

from dotenv import load_dotenv
os.environ["OPENAI_API_KEY"] = config.OPENAI_API_KEY
os.environ["AZURE_OPENAI_ENDPOINT"] = config.AZURE_OPENAI_ENDPOINT
os.environ["OPENAI_API_TYPE"] = config.OPENAI_API_TYPE
os.environ["OPENAI_API_VERSION"] = config.OPENAI_API_VERSION
os.environ["OPENAI_DEPLOYMENT_NAME"] = config.OPENAI_DEPLOYMENT_NAME
load_dotenv()

class QandAChooserAgent:
    def __init__(self, runnable: Runnable):
        self.runnable = runnable

    def __call__(self, state: State, config: RunnableConfig):
        # Primero selecciona una pregunta al azar
        random_question = self._choose_question(state)
        state["messages"] += [("user", random_question)]  # Agregar la pregunta generada al estado
        
        # Luego ejecuta el flujo del agente con la pregunta seleccionada
        while True:
            result = self.runnable.invoke(state)
            if not result.tool_calls or not result.content:
                messages = state["messages"] + [("user", "Please provide a valid question.")]
                state = {**state, "messages": messages}
            else:
                break

        # Retorna los mensajes con la pregunta incluida
        return {"messages": result}

    def _choose_question(self, state: State) -> str:
        # Aquí es donde se selecciona una pregunta aleatoria del archivo JSON
        json_path = utils.JSON_PATH
        data = utils.load_json(json_path)
        questions = [each_qandas["question"] for each_qandas in data[0]['questions']]
        random_question = random.choice(questions)

        # Guardar la pregunta seleccionada en el estado
        state["last_question"] = random_question
        print(f"RANDOM QUESTION: {random_question}")
        return random_question

llm = AzureChatOpenAI(
    deployment_name=os.environ["OPENAI_DEPLOYMENT_NAME"],
    temperature=0.1
)

qanda_chooser_prompt = ChatPromptTemplate.from_messages(
    [
        ("system",
         "Your only purpose is to connect the user with the right tool. "
         "Don't generate any text. "
         "You don't do absolutely anything else.",
         ),
        ("placeholder", "{messages}")
    ]
).partial()

# Conectar la herramienta de evaluación de respuestas
qanda_chooser_runnable = qanda_chooser_prompt | llm.bind_tools([qanda_evaluation])
