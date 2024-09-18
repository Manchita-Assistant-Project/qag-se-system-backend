from app.generator import config
from app.tests.utils import create_agent
from app.tests.tools import single_tools, qanda_chooser, qanda_evaluation

from langchain_openai import AzureChatOpenAI

import os
from dotenv import load_dotenv
os.environ["OPENAI_API_KEY"] = config.OPENAI_API_KEY
os.environ["AZURE_OPENAI_ENDPOINT"] = config.AZURE_OPENAI_ENDPOINT
os.environ["OPENAI_API_TYPE"] = config.OPENAI_API_TYPE
os.environ["OPENAI_API_VERSION"] = config.OPENAI_API_VERSION
os.environ["OPENAI_DEPLOYMENT_NAME"] = config.OPENAI_DEPLOYMENT_NAME
load_dotenv()

single_tools_template = """
Your only purpose is to connect the user with the right tool.
Don't generate any text.
You have to call a tool ALWAYS. NO EXCEPTIONS.
Don't answer questions directly.
Always output the exact same as the user input.
"""

loop_tools_template = """
Your only purpose is to connect the user with the right tool.
Don't generate any text.
You have to call a tool ALWAYS. NO EXCEPTIONS.
Don't answer questions directly.
Always output the exact same as the user input.
"""

llm = AzureChatOpenAI(
    deployment_name=os.environ["OPENAI_DEPLOYMENT_NAME"],
    temperature=0
)

single_tools_agent = create_agent(llm, single_tools, single_tools_template)
qanda_chooser_agent = create_agent(llm, [qanda_chooser], loop_tools_template)
qanda_evaluation_agent = create_agent(llm, [qanda_evaluation], loop_tools_template)
