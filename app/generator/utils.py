import os
import re
import json
import random
import importlib
from IPython.display import Image

from langgraph.prebuilt import ToolNode
from langchain_core.messages import ToolMessage
from langchain_core.runnables import RunnableLambda
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
JSONS_PATH = os.path.join(base_dir, "generator", "q&as")

def load_json(filename: str):
    path = os.path.join(JSONS_PATH, filename + '.json')
    with open(path, 'r', encoding='utf-8') as f:
        json_dict = json.load(f)

    if "content" not in json_dict or not isinstance(json_dict["content"], list):
        json_dict["content"] = []

    return json_dict['content']

def update_json(filename: str, data: dict):
    path = os.path.join(JSONS_PATH, filename + '.json')
    with open(path, 'r') as f:
        json_dict = json.load(f)

    print(f"DATA: {data}")
    
    if "content" not in json_dict or not isinstance(json_dict["content"], list):
        json_dict["content"] = []

    json_dict["content"].append(data)

    with open(path, 'w', encoding='utf-8') as f:
        json.dump(json_dict, f, ensure_ascii=False, indent=4)

def generate_graph_image(runnable):
    i = runnable.get_graph().draw_mermaid_png()
    with open("app/generator/graph.png", "wb") as png:
        png.write(i)
