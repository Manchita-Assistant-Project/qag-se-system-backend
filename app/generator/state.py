from typing import Annotated, Optional
from typing_extensions import TypedDict

from langgraph.graph.message import AnyMessage, add_messages

class Question(TypedDict):
    question: str
    question_type: int
    question_difficulty: str
    question_answers: str
    approved: bool

class State(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]
    question: Optional[Question]
