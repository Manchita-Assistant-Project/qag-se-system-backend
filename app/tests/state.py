from typing import Annotated, Optional
from typing_extensions import TypedDict

from langgraph.graph.message import AnyMessage, add_messages

class State(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]
    last_question: Optional[str]
    thread_id: Optional[str]
    step: Optional[int]
    to_evaluate: Optional[str]
    from_goblin: Optional[bool]
