from app import config
from app.graph.utils import create_agent, create_goblin_agent
from app.graph.tools import single_tools, qanda_chooser, bridge_goblin, goblin_at_home, castle_goblin
from app.prompts.agents_prompts import SINGLE_TOOLS_TEMPLATE, LOOP_TOOLS_TEMPLATE, GOBLIN_TOOLS_TEMPLATE

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

If the what the user said is answering a previous question,
you have to call the tool `qanda_evaluation`.

It's important you differentiate between wanting questions
and wanting to play the game.
If the user wants to continue playing the game, you have to call
the tool `narrator_tool`.

It's mportant you acknowledge the user's input:

INPUT MESSAGE: {input_message}
THREAD_ID: {thread_id}
"""

loop_tools_template = """
Your only purpose is to connect the user with the right tool.
Don't generate any text.
You have to call a tool ALWAYS. NO EXCEPTIONS.
Don't answer questions directly.
Always output the exact same as the user input.

If the output is not in the form {{question}}|||{{answer}}, try again.
"""

goblin_tools_template = """
Your only purpose is to connect the user with the right tool.
Don't generate any text.
You have to call a tool ALWAYS. NO EXCEPTIONS.
"""

llm = AzureChatOpenAI(
    deployment_name=os.environ["OPENAI_DEPLOYMENT_NAME"],
    temperature=0
)

single_tools_agent = create_agent(llm, single_tools, SINGLE_TOOLS_TEMPLATE)
qanda_chooser_agent = create_agent(llm, [qanda_chooser], LOOP_TOOLS_TEMPLATE)
goblin_agent = create_goblin_agent(llm, [bridge_goblin, goblin_at_home, castle_goblin], GOBLIN_TOOLS_TEMPLATE, ["bridge_goblin", "goblin_at_home", "castle_goblin"])
