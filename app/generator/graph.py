import uuid
from typing import Literal

import app.generator.utils as utils
import app.generator.nodes as nodes
from app.generator.state import State, Question

from langchain_core.messages import HumanMessage
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

# routing functions
def question_or_answer_path(state) -> Literal["question_generator", "answer_generator"]:
    question = state["question"]
    
    if question["question"] is None: 
        return "question_generator"
    else:
        print('POR ACÁ')
        return "answer_generator"
    
def refine_or_classify_path(state) -> Literal["question_refiner", "context_generator"]:
    similarity = state["messages"][-1].content.split("|||")[1]

    if float(similarity) < 0.75: # ajustar threshold
        return "question_refiner"
    else:
        return "context_generator"

# building the graph
workflow = StateGraph(State)

# add nodes
workflow.add_node("context_generator", nodes.context_generator_node)
workflow.add_node("question_generator", nodes.question_generator_node)
workflow.add_node("answer_generator", nodes.answer_generator_node)
workflow.add_node("question_evaluator", nodes.question_evaluator_node)
workflow.add_node("question_refiner", nodes.question_refiner_node)
# workflow.add_node("question_classifier", nodes.question_classifier_node)
workflow.add_node("qanda_saver", nodes.data_saver_tool)

# add edges
workflow.set_entry_point("context_generator")

workflow.add_conditional_edges(
    "context_generator",
    question_or_answer_path
)

workflow.add_conditional_edges(
    "question_evaluator",
    refine_or_classify_path
)

workflow.add_edge("question_generator", "question_evaluator")
workflow.add_edge("question_refiner", "question_evaluator")
# workflow.add_edge("question_classifier", "context_generator")
workflow.add_edge("answer_generator", "qanda_saver")
workflow.add_edge("qanda_saver", END)

def use_graph(question_type: int, question_difficulty_int: int):
    # compile the graph
    checkpointer = MemorySaver()
    graph = workflow.compile(
        checkpointer=checkpointer
    )

    # generate a graph image
    utils.generate_graph_image(graph)

    thread_id = str(uuid.uuid4())
    thread = {
        "configurable": {
            "thread_id": thread_id,
        }
    }
    
    # question_type = int(input("Enter question type: "))
    # question_difficulty_int = int(input("Enter question difficulty: "))
    
    # 1 -> Opción Múltiple
    # 2 -> Respuesta Abierta
    # 3 -> Verdadero o Falso
    # 4 -> Completar Espacios (idea)
    
    # question_type = 1
    
    # 1 -> Fácil
    # 2 -> Difícil
    
    # question_difficulty_int = 2
    question_difficulty = ""
    
    if question_difficulty_int == 1:
        question_difficulty = "Fácil"
    elif question_difficulty_int == 2:
        question_difficulty = "Difícil"

    question = Question(
        question=None,
        question_type=question_type,
        question_difficulty=question_difficulty
    )
    graph.update_state(thread, { "question": question })
    
    for event in graph.stream({"messages": [HumanMessage(content=question_type)]}, thread, stream_mode="values"):
        print(f"NEXT: {graph.get_state(thread).next}")
        if graph.get_state(thread).next != "context_generator" and len(event['messages'][-1].content) <= 50:
            event['messages'][-1].pretty_print()

# use_graph()
