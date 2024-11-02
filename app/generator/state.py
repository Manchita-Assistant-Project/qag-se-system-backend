from typing import Annotated, Dict, List, Optional
from typing_extensions import TypedDict

from langgraph.graph.message import AnyMessage, add_messages

class Question(TypedDict):
    question: str
    question_type: int
    question_difficulty: str
    question_answers: str
    approved: bool
    
class Threshold(TypedDict):
    similarity_threshold: float
    quality_threshold: float

class State(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]
    messages_to_remove: Optional[list[int]] # para poder luego eliminar los contextos de los mensajes del grafo
    question: Optional[Question]
    threshold: Optional[Threshold]
    questions: Optional[List[Dict[str, str]]]
    db_id: Optional[str]
