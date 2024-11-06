import os
import json

import app.generator.tools as tools

from langchain_core.messages import RemoveMessage

def context_generator_node(state):
    print('--- CONTEXT GENERATOR ---')
    db_id = state["db_id"]
    question = state["question"]
    messages_to_remove = state["messages_to_remove"]
    
    print(f"MESSAGES: {state['messages']}")
    
    if question["approved"] == True: # se genera un contexto basado en la pregunta generada
        result = tools.get_context_tool(db_id, question["question"], k=5)
    else:
        result = tools.get_context_tool(db_id)
    
    messages_to_remove.append(len(state["messages"])) # se guarda cada índice donde hubo un contexto |
                                                      # se guarda el actual porque para esta línea no
                                                      # se ha agregado el contexto, entonces el índice
                                                      # será el siguiente
                                                   
    print(f"CONTEXT INDEXES: {messages_to_remove}")
                                           
    return { "messages": [result], "messages_to_remove": messages_to_remove }

def question_generator_node(state):
    print('--- QUESTION GENERATOR ---')
    print(f"ESTADO: {state.keys()}")
    db_id = state["db_id"]
    question = state["question"]
    question_type = question["question_type"] # para este momento ya existe
    question_difficulty = question["question_difficulty"]
    
    context = state["messages"][-1].content if '|||' not in state["messages"][-1].content else state["messages"][-1].content.split('|||')[0]
    # result = tools.question_generator_tool(question_type, question_difficulty, context)
    result = tools.ten_questions_generator_tool(db_id, question_type, question_difficulty, context)
    
    # question["question"] = result
    # print(f"question: {result}")
    return { "messages": [result[0]["question"]], "question": question, "questions": result }

def question_seen_node(state):
    print("--- QUESTION SEEN ---")
    db_id = state["db_id"]
    question = state["question"]
    question_type = question["question_type"]
    similarity_threshold = state["threshold"]["similarity_threshold"]
    
    questions = state["questions"]
    
    generated_question = state["messages"][-1].content

    # seen = tools.question_seen_embeddings_tool(question, question_type, similarity_threshold)
    question_n, seen = tools.find_most_different_question(db_id, questions, question_type, similarity_threshold)
    
    print(f"Similarity: {seen}")
    
    if seen >= similarity_threshold:
        return { "messages": [f"{seen}|||{seen}"] }
    
    question["question"] = question_n["question"]
    
    return { "messages": [f"{question['question']}|||{seen}"], "question": question }

def messages_remover_node(state):
    print('--- MESSAGES REMOVER ---')
    messages = state["messages"]
    messages_to_remove = state["messages_to_remove"]
    print(f"CONTEXT INDEXES: {messages_to_remove}")    
    
    print("Removed contexts")
    return { "messages": [RemoveMessage(id=messages[each_index].id) for each_index in messages_to_remove], "messages_to_remove": [] }

def question_evaluator_node(state):
    print('--- QUESTION EVALUATOR ---')
    db_id = state["db_id"]
    question = state["question"]
    messages_to_remove = state["messages_to_remove"]
    quality_threshold = state["threshold"]["quality_threshold"]
    
    generated_question = state["messages"][-1].content.replace("'", '"').split('|||')[0]
    print(f"PREGUNTA A EVALUAR: {generated_question}")
    # generated_question_dict = json.loads(generated_question_dict_str) if generated_question_dict_str[0] == '{' else generated_question_dict_str
    # generated_question = generated_question_dict["question"]
    quality, feedback = tools.evaluate_quality_tool(db_id, generated_question, quality_threshold)
    
    messages_to_remove.append(len(state["messages"])) 
    
    if quality < quality_threshold:
        return { "messages": [f"{feedback}|||{quality}"], "messages_to_remove": messages_to_remove }
    
    question["question"] = generated_question if '|||' not in generated_question else generated_question.split('|||')[0]
    question["approved"] = True
    
    return { "messages": [f"{feedback}|||{quality}"], "question": question, "messages_to_remove": messages_to_remove }

def question_refiner_node(state):
    print('--- QUESTION REFINER ---')
    db_id = state["db_id"]
    question = state["question"]
    quality_threshold = state["threshold"]["quality_threshold"]
    
    last_message = state["messages"][-1].content
    feedback, quality = last_message.split("|||")
    
    response = tools.refine_question_tool(db_id, question["question"], feedback, float(quality), question["question_type"], quality_threshold)
    
    return { "messages": [response] }

def answer_generator_node(state):
    print('--- ANSWER GENERATOR ---')
    question = state["question"]
    question_type = question["question_type"]
    question_difficulty = question["question_difficulty"]
    
    context = state["messages"][-1].content

    result = tools.answer_generator_tool(question_type, question["question"], question_difficulty, context)
    print(result)
    question["question_answers"] = result

    return { "messages": [result], "question": question }

def data_saver_tool(state):
    print('--- DATA SAVER ---')
    db_id = state["db_id"]
    question = state["question"]
    question_format = question["question_answers"]
    
    if question_format is None or question_format == "ERROR":
        return
    
    double_quotes_string = question_format.replace('"', '/')
    double_quotes_string = double_quotes_string.replace("'", '"')
    double_quotes_string = double_quotes_string.replace("/", "'")
    # print(double_quotes_string)
    question_format_dict = json.loads(double_quotes_string)
    # print(question_format_dict)

    type_to_string = {
        1: "MCQ",
        2: "OEQ",
        3: "TFQ"
    }
    question_format_dict["type"] = type_to_string[question["question_type"]]
    question_format_dict["difficulty"] = question["question_difficulty"]

    if "answer" not in question_format_dict:
        question_format_dict["answer"] = "None"

    temp_filename = tools.save_question_tool(db_id, question_format_dict, type_to_string[question["question_type"]].lower() + 's')
    
    return { "messages": [temp_filename] }
