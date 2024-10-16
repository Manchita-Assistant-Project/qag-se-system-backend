import app.generator.graph as graph

if __name__ == "__main__":
    for i in range(1, 51):
        question_type = 1
        if (i % 3 == 0):
            question_difficulty_int = 1
        else:
            question_difficulty_int = 2
    
        graph.use_graph(question_type, question_difficulty_int)
        
    for i in range(1, 51):
        question_type = 3
        if (i % 3 == 0):
            question_difficulty_int = 1
        else:
            question_difficulty_int = 2
    
        graph.use_graph(question_type, question_difficulty_int)
