import app.generator.config as config
from app.generator.prompts import ORACLE_PROMPT
from app.generator.agents import QandAGenerationAgent, QandAEvaluationAgent, InteractionAgent, qanda_chooser, final_answer

import os
from langchain_openai import AzureChatOpenAI
from langchain_core.messages import ToolCall, ToolMessage
from langchain_core.agents import AgentAction, AgentFinish
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from dotenv import load_dotenv
os.environ["OPENAI_API_KEY"] = config.OPENAI_API_KEY
os.environ["AZURE_OPENAI_ENDPOINT"] = config.AZURE_OPENAI_ENDPOINT
os.environ["OPENAI_API_TYPE"] = config.OPENAI_API_TYPE
os.environ["OPENAI_API_VERSION"] = config.OPENAI_API_VERSION
os.environ["OPENAI_DEPLOYMENT_NAME"] = config.OPENAI_DEPLOYMENT_NAME
load_dotenv()

prompt = ChatPromptTemplate.from_messages([
    ("system", ORACLE_PROMPT),
    MessagesPlaceholder(variable_name="chat_history"),
    ("user", "{input}"),
    ("assistant", "scratchpad: {scratchpad}"), # acá va quedando el proceso de uso de herramientas
])

llm = AzureChatOpenAI(
    deployment_name=os.environ["OPENAI_DEPLOYMENT_NAME"],
    temperature=0
)

tools = [
    # QandAGenerationAgent,
    QandAEvaluationAgent,
    InteractionAgent,
    qanda_chooser,
    final_answer
]

def create_scratchpad(intermediate_steps: list[AgentAction]):
    """
    Transforms intermediate_steps from list of AgentAction to
    scratchpad string (just to visualize it better).
    """
    research_steps = []
    for i, action in enumerate(intermediate_steps):
        if action.log != "TBD":
            # this was the ToolExecution
            research_steps.append(
                f"Tool: {action.tool}, input: {action.tool_input}\n"
                f"Output: {action.log}"
            )
    return "\n---\n".join(research_steps)

oracle = (
    {   # parámetros de entrada
        "input": lambda x: x["input"],
        "chat_history": lambda x: x["chat_history"],
        "scratchpad": lambda x: create_scratchpad(
            intermediate_steps=x["intermediate_steps"]
        ),
    }
    | prompt
    | llm.bind_tools(tools, tool_choice="auto") 
    # parece que Azure OpenAI no soporta el uso de "any" herramientas
    # | llm.bind_tools(tools, tool_choice="any") # obliga al LLM a usar una herramienta siempre
)

def run_oracle(state: list):
    print("run_oracle")
    print(f"intermediate_steps: {state['intermediate_steps']}")
    out = oracle.invoke(state)
    tool_name = out.tool_calls[0]["name"]
    tool_args = out.tool_calls[0]["args"]
    action_out = AgentAction(
        tool=tool_name,
        tool_input=tool_args,
        log="TBD"
    )
    
    return { "intermediate_steps": [action_out] }

def router(state: list):
    """
    Returns the tool name to use
    """
    if isinstance(state["intermediate_steps"], list):
        return state["intermediate_steps"][-1].tool # el paso intermedio más reciente
    else:
        print("Router invalid format")
        return "final_answer"

tool_str_to_func = {
    # "QandAGenerationAgent": QandAGenerationAgent,
    "InteractionAgent": InteractionAgent,
    "QandAEvaluationAgent": QandAEvaluationAgent,
    "qanda_chooser": qanda_chooser,
    "final_answer": final_answer
}

def run_tool(state: list):
    # use this as helper function so we repeat less code
    tool_name = state["intermediate_steps"][-1].tool
    tool_args = state["intermediate_steps"][-1].tool_input
    print(f"{tool_name}.invoke(input={tool_args})")
    # run tool
    out = tool_str_to_func[tool_name].invoke(input=tool_args)
    action_out = AgentAction(
        tool=tool_name,
        tool_input=tool_args,
        log=str(out)
    )
    return {"intermediate_steps": [action_out]}
