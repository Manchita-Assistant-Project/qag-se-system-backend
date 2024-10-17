import app.generator.graph as graph

if __name__ == "__main__":
    
    # preguntas "Opción Múltiple"
    for i in range(1, 51):
        question_type = 1
        if (i % 3 == 0):
            question_difficulty_int = 1
        else:
            question_difficulty_int = 2
    
        try:
            graph.use_graph(question_type, question_difficulty_int)
        except Exception as e:
            print(f"Error al cargar la pregunta {i}: {e}")
            continue
    
    # preguntas "Verdadero o Falso"
    for i in range(1, 51):
        question_type = 3
        if (i % 3 == 0):
            question_difficulty_int = 1
        else:
            question_difficulty_int = 2
    
        try:
            graph.use_graph(question_type, question_difficulty_int)
        except Exception as e:
            print(f"Error al cargar la pregunta {i}: {e}")
            continue
