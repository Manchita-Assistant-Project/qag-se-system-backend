from typing import Annotated, Optional
from typing_extensions import TypedDict

from langchain_community.vectorstores import Chroma
from langgraph.graph.message import AnyMessage, add_messages

class Story(TypedDict):
    name: Optional[str]
    step: Optional[int]
    step_in_step: Optional[int] # 1 -> first interaction | 2 -> life lost | 3 -> success or failure
    prompt_type: Optional[str]
    to_evaluate: Optional[str]
    character_personality: Optional[str]

class State(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]
    last_question: Optional[str]
    thread_id: Optional[str]
    was_tool_call: Optional[bool]
    current_story: Optional[Story]
    from_story: Optional[bool]
    db_chroma: Optional[str]
    db_sqlite: Optional[str]
