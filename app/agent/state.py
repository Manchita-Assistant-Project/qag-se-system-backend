from typing import Annotated, Optional
from typing_extensions import TypedDict

from langchain_community.vectorstores import Chroma
from langgraph.graph.message import AnyMessage, add_messages

class Story(TypedDict):
    name: Optional[str]
    step: Optional[int]
    to_evaluate: Optional[str]
    character_personality: Optional[str]
    
class ChromaDatabase(TypedDict):
    db_id: Optional[str]
    db: Optional[Chroma]

class State(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]
    last_question: Optional[str]
    thread_id: Optional[str]
    was_tool_call: Optional[bool]
    # step: Optional[int]
    # to_evaluate: Optional[str]
    current_story: Optional[Story]
    from_story: Optional[bool]
    db_chroma: Optional[ChromaDatabase]
    db_sqlite: Optional[str]
