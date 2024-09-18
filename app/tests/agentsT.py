import operator
import functools
import random

import app.generator.utils as utils
import app.generator.config as config
from app.tests.tools import qanda_evaluation, qanda_generation, rag_search

from typing_extensions import TypedDict
from typing import Annotated, Callable, Optional, List

from langgraph.prebuilt import create_react_agent
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai.chat_models import AzureChatOpenAI
from langchain_core.runnables import Runnable, RunnableConfig
from langgraph.graph.message import AnyMessage, add_messages

import os
from dotenv import load_dotenv
os.environ["OPENAI_API_KEY"] = config.OPENAI_API_KEY
os.environ["AZURE_OPENAI_ENDPOINT"] = config.AZURE_OPENAI_ENDPOINT
os.environ["OPENAI_API_TYPE"] = config.OPENAI_API_TYPE
os.environ["OPENAI_API_VERSION"] = config.OPENAI_API_VERSION
os.environ["OPENAI_DEPLOYMENT_NAME"] = config.OPENAI_DEPLOYMENT_NAME
load_dotenv()

class QandAChooserState(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]
    question: str
    
class QandAChooserAgent:
    def __init__(self, runnable: Runnable):
        self.runnable = runnable
        
    def __call__(self, state: QandAChooserState, config: RunnableConfig):
        random_question = self._choose_question()
        state["messages"] += [("user", random_question)]
        
        while True:
            result = self.runnable.invoke(state)
            # If the LLM happens to return an empty response, we will re-prompt it
            # for an actual response.
            if not result.tool_calls and (
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
        return {"messages": result, "question": random_question}
    
    def _choose_question(self) -> str:
        json_path = utils.JSON_PATH
        data = utils.load_json(json_path)
        questions = [each_qandas["question"] for each_qandas in data[0]['questions']]
        random_question = random.choice(questions)

        print(f"RANDOM QUESTION: {random_question}")
        
        return random_question

llm = AzureChatOpenAI(
    deployment_name=os.environ["OPENAI_DEPLOYMENT_NAME"],
    temperature=0
)

qanda_chooser_prompt = ChatPromptTemplate.from_messages(
    [
        ("system",
         "Your only purpose is to connect the user with the right tool. "
         "Don't generate any text. "
         "Never talk to the user. "
         "Always respond exactly the same words as the user says. "
         "You don't do absolutely anything else.",
         ),
        ("placeholder", "{messages}")
    ]
).partial()

loop_tools = [qanda_evaluation]

single_tools = [
    qanda_generation,
    rag_search
]

loop_tools_names = {tool.name for tool in loop_tools}

qanda_assistant_runnable = qanda_chooser_prompt | llm.bind_tools(
    loop_tools + single_tools
)
