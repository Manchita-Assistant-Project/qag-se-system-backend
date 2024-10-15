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

def load_json(path: str):
    with open(path, 'r', encoding='utf-8') as f:
        content = json.load(f)

    return content['content']

def generate_graph_image(runnable):
    i = runnable.get_graph().draw_mermaid_png()
    with open("app/generator/graph.png", "wb") as png:
        png.write(i)
