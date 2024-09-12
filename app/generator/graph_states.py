from typing import TypedDict, Annotated, List, Union
from langchain_core.agents import AgentAction, AgentFinish
from langchain_core.messages import BaseMessage
import operator

class AgentState(TypedDict):
    input: str # input del usuario
    chat_history: list[BaseMessage] # historial de mensajes
    intermediate_steps: Annotated[list[tuple[AgentAction, str]], operator.add] # pasos intermedios -> (acción, mensaje) -> la idea es ir agregando pasos en lugar de reemplazar