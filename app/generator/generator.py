import app.generator.utils as utils
import app.generator.graph as graph

from langgraph.errors import GraphRecursionError

if __name__ == "__main__":
    counter = 0
    
    # eliminamos el contenido de los archivos de persistencia de embeddings
    utils.delete_all_content_hdf5(hdf5_file='embeddings.h5')
    
    # preguntas "Opción Múltiple"
    similarity_threshold = 0.8
    quality_threshold = 0.75
    # for i in range(1, 26):
    #     question_type = 1
    #     if (i % 3 == 0):
    #         question_difficulty_int = 1
    #     else:
    #         question_difficulty_int = 2
    
    #     try:
    #         graph.use_graph(
    #             question_type,
    #             question_difficulty_int,
    #             similarity_threshold,
    #             quality_threshold
    #         )
    #         # time.sleep(120)
    #         pass
    #     except Exception as e:
    #         print(f"Error al cargar la pregunta {i}: {e}")
    #         counter += 1
    #         continue
    
    # preguntas "Verdadero o Falso"
    similarity_threshold = 0.96
    for i in range(1, 26):
        question_type = 3
        if (i % 3 == 0):
            question_difficulty_int = 1
        else:
            question_difficulty_int = 2
     
        try:
            graph.use_graph(
                question_type,
                question_difficulty_int,
                similarity_threshold,
                quality_threshold
            )
            # time.sleep(30)
        except Exception as e:
            print(f"Error al cargar la pregunta {i}: {e}")
            counter += 1
            continue
    
    print(f"Recursion limit reached {counter} times.")
    
    # eliminamos el contenido de los archivos de persistencia de embeddings
    utils.delete_all_content_hdf5(hdf5_file='embeddings.h5')
