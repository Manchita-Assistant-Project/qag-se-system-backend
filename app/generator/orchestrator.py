import app.generator.utils as utils
import app.generator.config as config
from app.generator.prompts import FIXED_AGENTS_PROMPT
from app.generator.agents import QandAGenerationAgent, QandAChooserTool, QandAEvaluationAgent, InteractionAgent

import os
import json
from langchain_openai import AzureChatOpenAI
from langchain.chains import ConversationChain
from langchain.agents import Tool, initialize_agent
from langchain.memory import ConversationBufferMemory
from langchain.prompts.chat import SystemMessagePromptTemplate
from langchain.chains.conversation.memory import ConversationBufferWindowMemory

from dotenv import load_dotenv
os.environ["OPENAI_API_KEY"] = config.OPENAI_API_KEY
os.environ["AZURE_OPENAI_ENDPOINT"] = config.AZURE_OPENAI_ENDPOINT
os.environ["OPENAI_API_TYPE"] = config.OPENAI_API_TYPE
os.environ["OPENAI_API_VERSION"] = config.OPENAI_API_VERSION
os.environ["OPENAI_DEPLOYMENT_NAME"] = config.OPENAI_DEPLOYMENT_NAME
load_dotenv()

llm = AzureChatOpenAI(
    deployment_name=os.environ["OPENAI_DEPLOYMENT_NAME"],
    temperature=0.2
)

memory = ConversationBufferWindowMemory(
    memory_key='chat_history',
    k=3,
    return_messages=True
)

tools = [
    QandAGenerationAgent(),
    QandAChooserTool(),
    QandAEvaluationAgent(),
    InteractionAgent(),
]

conversational_agent = initialize_agent(
    agent='chat-conversational-react-description', 
    tools=tools, 
    llm=llm,
    verbose=True,
    max_iterations=3,
    memory=memory
)

conversational_agent.agent.llm_chain.prompt.messages[0].prompt.template = FIXED_AGENTS_PROMPT

states = {
    'initial',
    'question_asked',
    'question_answered',
}

def main():
    print("Bot: ¿Cómo quieres aprender hoy? Puedo evaluar conocimiento haciéndote preguntas o podemos tener una conversación educativa.")
    current_state = 'initial'
    question = None
    while True:
        user_input = input("You: ")
        response = None
        
        if current_state == 'initial':
            if 'pregunta' in user_input.lower(): # DEMO - por supuesto que esta evaluación hay que cambiarla!!
                print('Bot: ¡Genial! Vamos a evaluar tus conocimientos.')

                chooser_tool = QandAChooserTool()
                question = chooser_tool._run('')
                print(f"     {question}")
                current_state = 'question_asked'
                continue
            elif 'sí' in user_input.lower():
                interaction_tool = InteractionAgent()
                print(question)
                response = interaction_tool._run(f"{question}|||{user_input}")
                current_state = 'initial'
            else:
                response = conversational_agent.run(f"{question}|||{user_input}")
                cle
        elif current_state == 'question_asked':
            evaluation_tool = QandAEvaluationAgent()
            response = evaluation_tool._run(f"{question}|||{user_input}")
            current_state = 'initial'
                        

        # manejo de estados... sí o sí
        print(f"Bot: {response}")

if __name__ == "__main__":
    main()
