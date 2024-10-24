from app import config
from app.agent.utils import create_agent, create_character_agent
from app.agent.tools import single_tools, qanda_chooser, first_character, second_character, third_character
from app.prompts.agents_prompts import SINGLE_TOOLS_TEMPLATE, LOOP_TOOLS_TEMPLATE, CHARACTER_TOOLS_TEMPLATE

from langchain_openai import AzureChatOpenAI

import os
from dotenv import load_dotenv
os.environ["OPENAI_API_KEY"] = config.OPENAI_API_KEY
os.environ["AZURE_OPENAI_ENDPOINT"] = config.AZURE_OPENAI_ENDPOINT
os.environ["OPENAI_API_TYPE"] = config.OPENAI_API_TYPE
os.environ["OPENAI_API_VERSION"] = config.OPENAI_API_VERSION_2
os.environ["OPENAI_DEPLOYMENT_NAME"] = config.OPENAI_DEPLOYMENT_NAME_2
load_dotenv()

single_tools_template = """
If the user wants to continue playing the story game, you have to call
the tool `narrator_tool`.
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
# goblin_agent = create_goblin_agent(llm, [bridge_goblin, goblin_at_home, castle_goblin], GOBLIN_TOOLS_TEMPLATE, ["bridge_goblin", "goblin_at_home", "castle_goblin"])
character_agent = create_character_agent(llm, [first_character, second_character, third_character], CHARACTER_TOOLS_TEMPLATE, ["first_character", "second_character", "third_character"])
# character_agent = create_character_agent(llm, [], CHARACTER_TOOLS_TEMPLATE, ["BABABOOII", "second_character", "third_character"]) # first_character
