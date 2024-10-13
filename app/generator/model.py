import os
import json
from typing import Callable

import app.config as config
import app.database.chroma_utils as chroma_utils

from langchain_openai import AzureChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain_community.vectorstores import Chroma

from dotenv import load_dotenv
os.environ["OPENAI_API_KEY"] = config.OPENAI_API_KEY
os.environ["AZURE_OPENAI_ENDPOINT"] = config.AZURE_OPENAI_ENDPOINT
os.environ["OPENAI_API_TYPE"] = config.OPENAI_API_TYPE
os.environ["OPENAI_API_VERSION"] = config.OPENAI_API_VERSION
os.environ["OPENAI_DEPLOYMENT_NAME"] = config.OPENAI_DEPLOYMENT_NAME
load_dotenv()

from app.prompts.tools_prompts import QANDA_PROMPT, EVALUATE_PROMPT, FEEDBACK_PROMPT

def main_load():
    # Create (or update) the data store.
    documents = chroma_utils.load_documents()
    print(f"📚 Loaded {len(documents)} pages")
    chunks = chroma_utils.split_documents(documents)
    print(f"🔪 Split into {len(chunks)} chunks")
    chroma_utils.add_to_chroma(chunks)
    print("🚀 Data loaded successfully!")

def load_json(path: str):
    with open(path, 'r') as f:
        content = json.load(f)

    return content['content']

def update_json(path: str, data: list):
    with open(path, 'r') as f:
        json_dict = json.load(f)

    parsed_data = [json.loads(item) for item in data]

    json_dict.update({"content": parsed_data})

    with open(path, 'w') as f:
        json.dump(json_dict, f, ensure_ascii=False, indent=4)

def QAndAGeneration(json_path: str):
    # Prepare the DB.
    embedding_function = chroma_utils.get_embedding_function()
    db = Chroma(persist_directory=chroma_utils.CHROMA_PATH, embedding_function=embedding_function)

    query_text = ""

    model = AzureChatOpenAI(
        deployment_name=os.environ["OPENAI_DEPLOYMENT_NAME"],
        temperature=0.2
    )
    
    # Search the DB -> top k most relevant chunks to the query.
    results = db.similarity_search_with_score(query_text, k=5)

    context_text = "\n\n---\n\n".join([doc.page_content for doc, _score in results])
    # print(context_text)
    prompt_template = ChatPromptTemplate.from_template(QANDA_PROMPT)
    prompt = prompt_template.format(context=context_text)

    # response_text = conversation.predict(input=prompt)
    response_text = model.invoke(prompt).content

    # r = change_a_to_q(response_text, query_text)
    # print(change_a_to_q(response_text, query_text), '\n\n')

    # sources = [doc.metadata.get("id", None) for doc, _score in results]
    # formatted_response = f"\nResponse: {response_text}\nSources: {sources}\n"
    # memory.chat_memory.add_ai_message(response_text)
    # memory.chat_memory.add_user_message(query_text)

    update_json(json_path, response_text.split('\n\n'))
    return response_text

def EvaluateAs(json_path: str, question: str, answer: str, feedback: Callable = None):
    questions = load_json(json_path)

    model = AzureChatOpenAI(
        deployment_name=os.environ["OPENAI_DEPLOYMENT_NAME"],
        temperature=0.2
    )
    
    prompt_template = ChatPromptTemplate.from_template(EVALUATE_PROMPT)
    prompt = prompt_template.format(context=questions, answer=answer, question=question)
    response_text = model.invoke(prompt).content

    if 'incorrecto' in response_text.lower() or \
       'incorrecta' in response_text.lower():
        if feedback:
            print('La respuesta es incorrecta...\n')
            return feedback(question)

    return response_text

def ProvideFeedback(question: str):
    embedding_function = chroma_utils.get_embedding_function()
    db = Chroma(persist_directory=chroma_utils.CHROMA_PATH, embedding_function=embedding_function)

    model = AzureChatOpenAI(
        deployment_name=os.environ["OPENAI_DEPLOYMENT_NAME"],
        temperature=0.2
    )

    # Search the DB -> top k most relevant chunks to the query.
    results = db.similarity_search_with_score(question, k=5)

    context_text = "\n\n---\n\n".join([doc.page_content for doc, _score in results])

    prompt_template = ChatPromptTemplate.from_template(FEEDBACK_PROMPT)
    prompt = prompt_template.format(context=context_text, question=question)

    response_text = model.invoke(prompt).content

    return response_text

def main():
    # ================= #
    # 0. Load the data  #
    # ================= #
    
    main_load()
    
    """
    generar preguntas múltiples.
    evaluarlas -> ver una respuesta y decir y si está bien o mal
               -> explique la respuesta -> feedback
    """

    # ========================== #
    # 1. Generate some questions #
    # ========================== #

    # rag_response = QAndAGeneration('app/generator/q&as/qs.json')
    # print(rag_response)

    # ========================== #
    # 2. Evaluate the questions  #
    # ========================== #

    # 2.1. Load JSON.
    # Pass it as context to the model.
    # Ask one of the questions in the JSON.
    # Evaluate the answer based on the JSON.

    # question = '¿Qué se valora y fomenta en el programa de diseño gráfico?'
    # answer = 'La facultad de matematicas de la Universidad de Antioquia'
    # answer = 'La iniciativa individual de los estudiantes'
    # response = EvaluateAs('questions/qs2.json', question, answer)
    # print(response)
     
    # ====================#
    # 3. Provide feedback #
    # ====================#

    # If asked, call this function to provide feedback.
    # response = EvaluateAs('app/generator/q&as/qs.json', question, answer, ProvideFeedback)
    # print(response)

    # ========================================== #
    # 4. Continue with supplementary interaction #
    # ========================================== #

    ...

if __name__ == "__main__":
    main()
