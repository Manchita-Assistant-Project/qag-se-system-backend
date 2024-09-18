from typing import Annotated
from typing_extensions import TypedDict
import app.generator.config as config
from app.generator.agents_graph import qanda_chooser, qanda_evaluation, rag_search, qanda_generation

from langchain_openai import AzureChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph.message import AnyMessage, add_messages
from langchain_core.runnables import Runnable, RunnableConfig

import os
from dotenv import load_dotenv
os.environ["OPENAI_API_KEY"] = config.OPENAI_API_KEY
os.environ["AZURE_OPENAI_ENDPOINT"] = config.AZURE_OPENAI_ENDPOINT
os.environ["OPENAI_API_TYPE"] = config.OPENAI_API_TYPE
os.environ["OPENAI_API_VERSION"] = config.OPENAI_API_VERSION
os.environ["OPENAI_DEPLOYMENT_NAME"] = config.OPENAI_DEPLOYMENT_NAME
load_dotenv()

class State(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]

class Assistant:
    def __init__(self, runnable: Runnable):
        self.runnable = runnable

    def __call__(self, state: State, config: RunnableConfig):
        while True:
            result = self.runnable.invoke(state)
            # If the LLM happens to return an empty response, we will re-prompt it
            # for an actual response.
            if not result.tool_calls or not result.tool_calls and (
                not result.content
                or isinstance(result.content, list)
                and not result.content[0].get("text")
            ):
                messages = state["messages"] + [("user", "Respond with a real output.")]
                state = {**state, "messages": messages}
                messages = state["messages"] + [("user", "Respond with a real output.")]
                state = {**state, "messages": messages}
            else:
                break
        return {"messages": result}


llm = AzureChatOpenAI(
    deployment_name=os.environ["OPENAI_DEPLOYMENT_NAME"],
    temperature=1
)

assistant_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are a helpful teachers assistant for a university in Cali, Colombia. "
            " Use the provided tools to assist the user with their queries. "
            " When searching, be persistent. Expand your query bounds if the first search returns no results. "
            " If a search comes up empty, expand your search before giving up."
            " It is important that, if you encounter a question as a valid response to the user, "
            " you should not answer it, but ask it to the user instead.",
        ),
        ("placeholder", "{messages}"),
    ]
).partial()

loop_tools = [
    qanda_evaluation,
    qanda_chooser,
]

single_tools = [
    qanda_generation,
    rag_search
]


loop_tool_names = {tool.name for tool in loop_tools}

# Nuestro LLM no sabe qué a qué nodos hacer el route. En su "cabeza", solo invoca funciones
assistant_runnable = assistant_prompt | llm.bind_tools(loop_tools + single_tools)
