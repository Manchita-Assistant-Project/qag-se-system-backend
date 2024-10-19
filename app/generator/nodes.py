import os
import json

import app.generator.tools as tools

def context_generator_node(state):
    print('--- CONTEXT GENERATOR ---')
    question = state["question"]
    
    if question["approved"] == True: # se genera un contexto basado en la pregunta generada
        result = tools.get_context_tool(question["question"], k=5)
    else:
        result = tools.get_context_tool(k=15)
        
    return { "messages": [result] }

def question_generator_node(state):
    print('--- QUESTION GENERATOR ---')
    question = state["question"]
    question_type = question["question_type"] # para este momento ya existe
    question_difficulty = question["question_difficulty"]
    
    context = state["messages"][-1].content if '|||' not in state["messages"][-1].content else state["messages"][-1].content.split('|||')[0]
    result = tools.question_generator_tool(question_type, question_difficulty, context)
    
    question["question"] = result
    print(f"question: {result}")
    return { "messages": [result], "question": question }

def question_seen_node(state):
    print("--- QUESTION SEEN ---")
    question = state["question"]
    question_type = question["question_type"]
    similarity_threshold = state["threshold"]["similarity_threshold"]
    
    generated_question = state["messages"][-1].content
    context = state["messages"][-2].content
    
    seen = tools.question_seen_embeddings_tool(question, question_type, similarity_threshold)    
    
    print(f"Similarity: {seen}")
    
    if seen >= 0.86:
        return { "messages": [f"{context}|||{seen}"] }
    
    question["question"] = generated_question if '|||' not in generated_question else generated_question.split('|||')[0]
    return { "messages": [f"{question['question']}|||{seen}"], "question": question }

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

def question_evaluator_node(state):
    print('--- QUESTION EVALUATOR ---')
    question = state["question"]
    quality_threshold = state["threshold"]["quality_threshold"]
    
    generated_question = state["messages"][-1].content
    quality, feedback = tools.evaluate_quality_tool(generated_question, quality_threshold)
    
    if quality < quality_threshold:
        return { "messages": [f"{feedback}|||{quality}"] }
    
    question["question"] = generated_question if '|||' not in generated_question else generated_question.split('|||')[0]
    question["approved"] = True
    
    return { "messages": [f"{feedback}|||{quality}"], "question": question }

def question_refiner_node(state):
    print('--- QUESTION REFINER ---')
    question = state["question"]
    quality_threshold = state["threshold"]["quality_threshold"]
    
    last_message = state["messages"][-1].content
    feedback, quality = last_message.split("|||")
    
    response = tools.refine_question_tool(question["question"], feedback, float(quality), question["question_type"], quality_threshold)
    
    return { "messages": [response] }

def data_saver_tool(state):
    print('--- DATA SAVER ---')
    question = state["question"]
    question_format = question["question_answers"]
    
    if question_format is None or question_format == "ERROR":
        return
    
    double_quotes_string = question_format.replace("'", '"')
    question_format_dict = json.loads(double_quotes_string)

    type_to_string = {
        1: "MCQ",
        2: "OAQ",
        3: "TFQ"
    }
    question_format_dict["type"] = type_to_string[question["question_type"]]
    question_format_dict["difficulty"] = question["question_difficulty"]

    tools.save_question_tool(question_format_dict, type_to_string[question["question_type"]].lower() + 's')
