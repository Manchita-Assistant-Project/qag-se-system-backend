import time
import json

import app.generator.utils as utils
import app.generator.graph as graph

if __name__ == "__main__":
    counter = 0
    
    # eliminamos el contenido de los archivos de persistencia de embeddings
    utils.delete_all_content_hdf5(hdf5_file='embeddings.h5')
    
    # preguntas "Opción Múltiple"
    # for i in range(1, 31):
    #     question_type = 1
    #     if (i % 3 == 0):
    #         question_difficulty_int = 1
    #     else:
    #         question_difficulty_int = 2
    
    #     try:
    #         graph.use_graph(question_type, question_difficulty_int)
    #         # time.sleep(120)
    #         pass
    #     except Exception as e:
    #         print(f"Error al cargar la pregunta {i}: {e}")
    #         if "Recursion limit reached" in str(e):
    #             counter += 1
    #             print("Recursion limit reached")
    #         continue
    
    # preguntas "Verdadero o Falso"
    for i in range(1, 61):
        question_type = 3
        if (i % 3 == 0):
            question_difficulty_int = 1
        else:
            question_difficulty_int = 2
     
        try:
            graph.use_graph(question_type, question_difficulty_int)
            # time.sleep(30)
        except Exception as e:
            print(f"Error al cargar la pregunta {i}: {e}")
            if "Recursion limit reached" in str(e):
                counter += 1
                print(f"Recursion limit reached counter: {counter}")
                print("Recursion limit reached")
            continue
        
    print(f"Recursion limit reached {counter} times.")
    
    # eliminamos el contenido de los archivos de persistencia de embeddings
    utils.delete_all_content_hdf5(hdf5_file='embeddings.h5')