import app.graph.utils as utils
from app.graph.state import State
from app.graph.nodes import single_tools_node, single_tools_tool_node, \
                            chooser_tool_node, evaluation_tool_node,\
                            points_updater_tool_node, human_interaction, \
                            narrator_node, goblin_node, bridge_goblin_node, \
                            goblin_at_home_node, castle_goblin_node, \
                            lives_updater_tool_node

import uuid
from typing import Literal

from langchain_core.messages import HumanMessage
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

single_use_tools = [
    'rag_search',
    'qanda_generation',
    'feedback_provider',
    'points_retrieval',
]

goblin_game_tools = [
    'narrator_tool',
    'bridge_goblin',
    'goblin_at_home',
    'castle_goblin',
]

# routing function
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

def points_or_lives(state) -> Literal["points_updater_tool", "lives_updater_tool"]:
    tool_used = state["from_goblin"] if "from_goblin" in state else False

    if tool_used:
        print("lives_updater_tool")
        return "lives_updater_tool"
    else:
        print("points_updater_tool")
        return "points_updater_tool"

def goblin_or_finish(state) -> Literal["goblin", "__end__"]:
    step = state["step"]
    
    if step != 4:
        return "goblin"
    else:
        return END

def which_goblin(state) -> Literal["bridge_goblin", "goblin_at_home", "castle_goblin"]:
    step = state["step"]  

    if step == 1:
        return "bridge_goblin"
    elif step == 2:
        return "goblin_at_home"
    elif step == 3:
        return "castle_goblin"
    
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
workflow.add_node("simple_interaction", single_tools_node)
workflow.add_node("single_tools", single_tools_tool_node)

workflow.add_node("chooser", chooser_tool_node)
workflow.add_node("human_interaction", human_interaction)
workflow.add_node("evaluation_tool", evaluation_tool_node)
workflow.add_node("points_updater_tool", points_updater_tool_node)

workflow.add_node("narrator", narrator_node)
workflow.add_node("goblin", goblin_node)
workflow.add_node("bridge_goblin", bridge_goblin_node)
workflow.add_node("goblin_at_home", goblin_at_home_node)
workflow.add_node("castle_goblin", castle_goblin_node)

workflow.add_node("lives_updater_tool", lives_updater_tool_node)

# add edges
workflow.set_entry_point("simple_interaction")

workflow.add_conditional_edges(
    "simple_interaction",
    should_use_single_tool
)

workflow.add_conditional_edges(
    "evaluation_tool",
    points_or_lives
)

workflow.add_conditional_edges(
    "narrator",
    goblin_or_finish
)

workflow.add_conditional_edges(
    "goblin",
    which_goblin
)

workflow.add_conditional_edges(
    "lives_updater_tool",
    should_continue_or_another_try
)

workflow.add_edge("single_tools", END)

workflow.add_edge("chooser", "human_interaction")
workflow.add_edge("human_interaction", "evaluation_tool")
workflow.add_edge("points_updater_tool", END)

# workflow.add_edge("narrator", "goblin")
workflow.add_edge("bridge_goblin", "human_interaction")
workflow.add_edge("goblin_at_home", "human_interaction")
workflow.add_edge("castle_goblin", "human_interaction")

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
        }
    }

    questions = [
        'hola!',
        'quiero jugar el juego del goblin!',
        'sigue con el juego!',
        'sigue!',
        'termina!'
        # 'hazme una pregunta!',
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
        graph.update_state(thread, {"thread_id": thread_id})
        # print(f"SNAPSHOT {query}: {snapshot}")
        for event in graph.stream({"messages": [HumanMessage(content=query)]}, thread, stream_mode="values"):
            event['messages'][-1].pretty_print()

        tool_used = graph.get_state(thread).values['messages'][-1].name

        is_not_single_use = False
        if tool_used is not None:
            is_not_single_use = len([tool for tool in single_use_tools if tool in tool_used]) != 1
        
        is_not_goblin_game = False
        if tool_used is not None:
            is_not_goblin_game = tool_used != 'narrator_tool'
        
        print(f"NEXT: {graph.get_state(thread).next}")

        # interrupción para el camino quiz
        if (is_not_single_use and is_not_goblin_game):
            user_answer = input('You: ')
            question = event['messages'][-1].content if event['messages'][-1].content[0] == '¿' else graph.get_state(thread).values['to_evaluate'] # pregunta sencilla o pregunta de juego goblin
            
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
                }
            )
            print(f"AFTER: {graph.get_state(thread).next}")
            
            for event in graph.stream(None, thread, stream_mode="values"):
                event['messages'][-1].pretty_print()
            
            # interrupción para el camino del juego del goblin cuando tiene una respuesta incorrecta
            if list(graph.get_state(thread).metadata['writes'].keys())[0] == 'lives_updater_tool':
                if "incorrecta" in graph.get_state(thread).values["messages"][-2].content:
                    snapshot = graph.get_state(thread).values["messages"][-2].content
                    current_lives_snapshot = 3
                    i = 3
                    while "incorrecta" in snapshot and current_lives_snapshot > 0: # si la respuesta es incorrecta y aún tiene vidas
                        print(f'LIVES UPDATER TOOL -> {snapshot}')
                        user_answer = input('You: ')
                        question = graph.get_state(thread).values['to_evaluate']
                        
                        combined_input = f"{question}|||{user_answer}"
                        print(f"COMBINED: {combined_input}")

                        # actualizar el estado con la pregunta y la respuesta combinada para que el nodo 'evaluation' lo reciba
                        graph.update_state(
                            thread, 
                            {
                                'messages': [
                                    HumanMessage(content=combined_input),
                                ],
                                'from_goblin': True,
                            },
                            as_node="human_interaction" # acá toca usar ese as_node para que se ejecute como si fuera el nodo 'human_interaction', para que pase bien a evaluar y luego a actualizar vidas
                        )
                        
                        for event in graph.stream(None, thread, stream_mode="values"):
                            event['messages'][-1].pretty_print()
                            
                        snapshot = graph.get_state(thread).values["messages"][-2].content
                        print(f"SNAPSHOT: {snapshot}")
                        
                        current_lives_snapshot = int(graph.get_state(thread).values["messages"][-1].content.split('|||')[1])
                        print(f"CURRENT LIVES: {current_lives_snapshot}")

                        print(f"AFTER: {graph.get_state(thread).next}")
                        
                        # i += 1
                    for event in graph.stream(None, thread, stream_mode="values"):
                        event['messages'][-1].pretty_print()
                            

use_graph()

"""
Para el juego de duendes:
- definir cómo se pasa de un duende a otro, es decir, si se pasa el duende del puente,
  qué debe decir el usuario para seguir? o debería ser secuencial:
  narrador -> puente -> H-I-L -> evaluation -> update tries -> casa -> H-I-L -> evaluation -> update tries -> castillo H-I-L -> evaluation -> update tries -> fin
- arísta condicional desde evaluation a points_updater_tool_node. si venía del juego de duendes, debe ir por el lado de un nuevo nodo que
  lleve cuenta de los corazones (sería chévere mostrarlos siempre con emojis -> siempre me refiero luego de cada duende o cuando pierde uno) (no creo que se necesite bd
  porque la idea es que si se inicia el juego, se termine en la misma sesión; ya sea ganando o perdiendo).
  
Para el frontend:
- Opción para que el usuario cargue el o los PDFs con los que quiera trabajar.

"""
