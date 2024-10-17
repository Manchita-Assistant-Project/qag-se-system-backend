import os
import re
import json
import string
from typing import Dict, List
from IPython.display import Image

from langgraph.prebuilt import ToolNode
from langchain_core.messages import ToolMessage
from langchain_core.runnables import RunnableLambda
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
JSON_PATH = os.path.join(base_dir, "generator", "q&as")

def load_json(filename: str):
    path = os.path.join(JSON_PATH, filename + '.json')
    with open(path, 'r', encoding='utf-8') as f:
        json_dict = json.load(f)

    if "content" not in json_dict or not isinstance(json_dict["content"], list):
        json_dict["content"] = []

    return json_dict['content']

def update_json(filename: str, data: dict):
    path = os.path.join(JSON_PATH, filename + '.json')
    with open(path, 'r', encoding='utf-8') as f:
        json_dict = json.load(f)

    print(f"DATA: {data}")
    
    if "content" not in json_dict or not isinstance(json_dict["content"], list):
        json_dict["content"] = []

    json_dict["content"].append(data)

    with open(path, 'w', encoding='utf-8') as f:
        json.dump(json_dict, f, ensure_ascii=False, indent=4)

def delete_local_file(file_path):
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            print(f"Archivo eliminado: {file_path}")
        else:
            print(f"El archivo no existe: {file_path}")
    except Exception as e:
        print(f"Error al eliminar el archivo {file_path}: {e}")

def generate_graph_image(runnable):
    i = runnable.get_graph().draw_mermaid_png()
    with open("app/generator/graph.png", "wb") as png:
        png.write(i)

def choices_list_to_dict(choices_list: List[str]) -> Dict[str, str]:
    result = {}
    letters = iter(string.ascii_lowercase)  # iterador de letras 'a', 'b', 'c', etc.
    
    for item in choices_list:
        # usamos una expresión regular para agarrar la letra (a, b, c, etc.) seguida de cualquier combinación de ) o .)
        match = re.match(r'^([a-zA-Z])[\.\)]\s*(.*)', item)
        if match:
            letter = match.group(1)
            text = match.group(2)
            result[letter] = text
        else:
            # si no hay prefijo con letra, usamos la siguiente letra del iterador
            letter = next(letters)
            result[letter] = item
    
    return result
