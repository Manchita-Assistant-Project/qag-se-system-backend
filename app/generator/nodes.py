import app.generator.tools as tools

def context_generator_node(state):
    question = state.get("question", None)
    
    if question["question"] is not None: # se genera un contexto basado en la pregunta generada
        result = tools.get_context_tool(question["question"], k=5)
    else:
        result = tools.get_context_tool()
        
    return { "messages": [result] }

def question_generator_node(state):
    question = state["question"]
    question_type = question["question_type"] # para este momento existe
    question_difficulty = question["question_difficulty"]
    
    context = state["messages"][-1].content
    result = tools.question_generator_tool(question_type, question_difficulty, context)
    
    question["question"] = result
    print(f"question: {result}")
    return { "messages": [result], "question": question }

def answer_generator_node(state):
    question = state["question"]
    question_type = question["question_type"]
    question_difficulty = question["question_difficulty"]
    
    context = state["messages"][-1].content

    result = tools.answer_generator_tool(question_type, question["question"], question_difficulty, context)
    print(result)
    question["question_answers"] = result

    return { "messages": [result], "question": question }

def question_evaluator_node(state):
    question = state["question"]
    generated_question = state["messages"][-1].content
    similarity, feedback = tools.evaluate_similarity_tool(generated_question)
    
    if similarity < 0.7:
        return { "messages": [f"{feedback}|||{similarity}"] }
    
    question["question"] = generated_question
    return { "messages": [f"{feedback}|||{similarity}"], "question": question }

def question_refiner_node(state):
    question = state["question"]
    last_message = state["messages"][-1].content
    feedback, similarity = last_message.split("|||")
    
    response = tools.refine_question_tool(question["question"], feedback)
    
    return { "messages": [response] }
