import uuid
from typing import Literal

import app.agent.utils as utils
import app.agent.nodes as nodes
from app.agent.state import State
import app.database.chroma_utils as chroma_utils

from langchain_core.messages import HumanMessage
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.runnables import RunnableConfig

single_use_tools = [
    'rag_search',
    'qanda_generation',
    'feedback_provider',
    'points_retrieval',
]

character_game_tools = [
    'narrator_tool',
    "character",
    "character_first_interaction",
    "character_life_lost",
    "character_success_or_failure",
    "character_loop_interaction",
    "lives_retrieval"
]

# routing functions
def should_use_single_tool(state) -> Literal["chooser", "single_tools", "narrator", "__end__"]:
    messages = state["messages"]
    last_message = messages[-1]
    
    if last_message.content == "end":
        return END

    # if the LLM makes a tool call, we route to the single tools node
    print(f"last_message.tool_calls: {last_message.tool_calls}")

    if last_message.tool_calls:
        if last_message.tool_calls[0]['name'] in single_use_tools:
            return "single_tools"
        elif last_message.tool_calls[0]['name'] == "narrator_tool":
            return "narrator"
        elif last_message.tool_calls[0]['name'] == "qanda_chooser":
            return "chooser"
        
    return "__end__"

def response_or_interaction(state) -> Literal["character", "evaluation_tool"]:
    current_story = state.get("current_story", None)
    step_in_step = current_story["step_in_step"] if current_story else None

    if step_in_step is not None and step_in_step == 4:
        return "character"
    
    return "evaluation_tool"

def points_or_lives(state) -> Literal["points_updater_tool", "lives_updater_tool"]:
    tool_used = state["from_story"] if "from_story" in state else False

    if tool_used:
        print("lives_updater_tool")
        return "lives_updater_tool"
    else:
        print("points_updater_tool")
        return "points_updater_tool"

def character_or_finish(state) -> Literal["character", "__end__"]:
    step = state["current_story"]["step"]
    
    if step != 4:
        return "character"
    else:
        return END

def which_from_character(state) -> Literal["character_first_interaction", "character_life_lost", "character_success_or_failure", "character_loop_interaction"]:
    step_in_step = state["current_story"]["step_in_step"]
    print(f"--- {step_in_step} ---")
    possible_steps = ["character_first_interaction", "character_life_lost", "character_success_or_failure", "character_loop_interaction"]
    
    next_step = possible_steps[step_in_step - 1]
    print(f"--- {next_step} ---")
    return next_step
    
def should_continue_or_another_try(state) -> Literal["human_interaction", "__end__"]:
    last_evaluation_message = state["messages"][-2].content
    current_lives = state["messages"][-1].content.split("|||")[1]
    
    if "incorrecta" in last_evaluation_message and int(current_lives) > 0:
        print("Another try")
        return "human_interaction"
    else:
        return END

# building the graph
workflow = StateGraph(State)

# add nodes
workflow.add_node("simple_interaction", nodes.single_tools_node)
workflow.add_node("single_tools", nodes.single_tools_tool_node)

workflow.add_node("chooser", nodes.chooser_tool_node)
workflow.add_node("human_interaction", nodes.human_interaction)
workflow.add_node("response_classifier", nodes.response_classifier_node)
workflow.add_node("evaluation_tool", nodes.evaluation_tool_node)
workflow.add_node("points_updater_tool", nodes.points_updater_tool_node)
workflow.add_node("motivator", nodes.motivator_node)

workflow.add_node("narrator", nodes.narrator_node)
workflow.add_node("character", nodes.character_node)

workflow.add_node("character_first_interaction", nodes.character_first_interaction_node)
workflow.add_node("character_life_lost", nodes.character_life_lost_node)
workflow.add_node("character_success_or_failure", nodes.character_success_or_failure_node)
workflow.add_node("character_loop_interaction", nodes.character_loop_interaction_node)

workflow.add_node("lives_updater_tool", nodes.lives_updater_tool_node)

# add edges
workflow.set_entry_point("simple_interaction")

workflow.add_conditional_edges(
    "simple_interaction",
    should_use_single_tool
)

workflow.add_conditional_edges(
    "response_classifier",
    response_or_interaction
)

workflow.add_conditional_edges(
    "evaluation_tool",
    points_or_lives
)

workflow.add_conditional_edges(
    "narrator",
    character_or_finish
)

workflow.add_conditional_edges(
    "character",
    which_from_character
)

# workflow.add_conditional_edges(
#     "lives_updater_tool",
#     should_continue_or_another_try
# )

workflow.add_edge("single_tools", END)

workflow.add_edge("chooser", "human_interaction")
# workflow.add_edge("human_interaction", "evaluation_tool")
workflow.add_edge("human_interaction", "response_classifier")
workflow.add_edge("points_updater_tool", "motivator")
workflow.add_edge("motivator", END)

# workflow.add_edge("narrator", "character")
# workflow.add_edge("first_character", "human_interaction")
# workflow.add_edge("second_character", "human_interaction")
# workflow.add_edge("third_character", "human_interaction")
workflow.add_edge("lives_updater_tool", "character")
workflow.add_edge("character_first_interaction", "human_interaction")
workflow.add_edge("character_loop_interaction", "human_interaction")
workflow.add_edge("character_life_lost", "human_interaction")
workflow.add_edge("character_success_or_failure", END)


def use_graph():
    # compile the graph
    checkpointer = MemorySaver()
    graph = workflow.compile(
        checkpointer=checkpointer,
        interrupt_before=["human_interaction"],
    )

    # generate a graph image
    utils.generate_graph_image(graph)

    thread_id = str(uuid.uuid4())
    thread = {
        "configurable": {
            "thread_id": thread_id,
            "recursion_limit": 50
        }
    }

    config = RunnableConfig(
        thread_id=thread_id,
        recursion_limit=50
    )

    db_id = 'NKNKNK'
    # db = chroma_utils.get_db(db_id)
    
    # db_obj = ChromaDatabase(
    #     db_id=db_id,
    #     db=db
    # )

    questions = [
        'hola!',
        'hazme una pregunta!',
        'quiero jugar las historias!',
        # 'cuántos puntos tengo?',
        'sigue con el juego!',
        # 'sigue!',
        # 'termina!',
        # 'hazme otra!',
        # 'háblame un poco más sobre eso, por favor.',
        # 'cuántos puntos tengo?',
        # # 'dime la correcta!',
        # 'ahora háblame un poco sobre la Resolución No. 051 de junio 24 de 2008',
        # 'ahora, hazme otra pregunta!',
        # 'cuántos puntos tengo?',
    ]

    # while True:
    for query in questions:
        # query = input("You: ")
        graph.update_state(thread, {"thread_id": thread_id, "db_chroma": db_id})
        # print(f"SNAPSHOT {query}: {snapshot}")
        for event in graph.stream({"messages": [HumanMessage(content=query)]}, config, stream_mode="values"):
            print(f"TOOL USED {graph.get_state(thread).values['messages'][-1].name}")
            event['messages'][-1].pretty_print()

        tool_used = graph.get_state(thread).values['messages'][-1].name

        is_not_single_use = False
        if tool_used is not None:
            is_not_single_use = len([tool for tool in single_use_tools if tool in tool_used]) != 1
        
        is_not_character_game = False
        if tool_used is not None:
            is_not_character_game = tool_used != 'narrator_tool'
        
        print(f"NEXT: {graph.get_state(thread).next}")

        # interrupción para el camino quiz
        if (is_not_single_use and is_not_character_game):
            user_answer = input('You: ')
            question = graph.get_state(thread).values["last_question"] if (event["messages"][-1].name == "qanda_chooser") else graph.get_state(thread).values["current_story"]["to_evaluate"] # pregunta sencilla o pregunta de juego character
            
            combined_input = f"{question}|||{user_answer}"
            print(combined_input)

            # actualizar el estado con la pregunta y la respuesta combinada para que el nodo 'evaluation' lo reciba
            graph.update_state(
                thread, 
                {
                    'messages': [
                        HumanMessage(content=combined_input),
                    ],
                    'last_question': question,
                },
                as_node="human_interaction"
            )
            print(f"AFTER: {graph.get_state(thread).next}")
            
            for event in graph.stream(None, config, stream_mode="values"):
                event['messages'][-1].pretty_print()
            
            # interrupción para el camino del juego del character cuando tiene una respuesta incorrecta
            if list(graph.get_state(thread).metadata['writes'].keys())[0] == 'lives_updater_tool':
                if "incorrecta" in graph.get_state(thread).values["messages"][-2].content:
                    snapshot = graph.get_state(thread).values["messages"][-2].content
                    current_lives_snapshot = 3
                    i = 3
                    while "incorrecta" in snapshot and current_lives_snapshot > 0: # si la respuesta es incorrecta y aún tiene vidas
                        print(f'LIVES UPDATER TOOL -> {snapshot}')
                        user_answer = input('You: ')
                        question = graph.get_state(thread).values['current_story']["to_evaluate"]
                        
                        combined_input = f"{question}|||{user_answer}"
                        print(f"COMBINED: {combined_input}")

                        # actualizar el estado con la pregunta y la respuesta combinada para que el nodo 'evaluation' lo reciba
                        graph.update_state(
                            thread, 
                            {
                                'messages': [
                                    HumanMessage(content=combined_input),
                                ]
                            },
                            as_node="human_interaction" # acá toca usar ese as_node para que se ejecute como si fuera el nodo 'human_interaction', para que pase bien a evaluar y luego a actualizar vidas
                        )
                        
                        for event in graph.stream(None, config, stream_mode="values"):
                            event['messages'][-1].pretty_print()
                            
                        snapshot = graph.get_state(thread).values["messages"][-2].content
                        print(f"SNAPSHOT: {snapshot}")
                        
                        current_lives_snapshot = int(graph.get_state(thread).values["messages"][-1].content.split('|||')[1])
                        print(f"CURRENT LIVES: {current_lives_snapshot}")

                        print(f"AFTER: {graph.get_state(thread).next}")
                        
                        # i += 1
                    for event in graph.stream(None, config, stream_mode="values"):
                        event['messages'][-1].pretty_print()
                            
# use_graph()
