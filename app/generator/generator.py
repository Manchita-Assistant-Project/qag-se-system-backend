import app.generator.utils as utils
import app.generator.graph as graph

from langgraph.errors import GraphRecursionError

def generate_qandas(mcq_similarity_threshold: float, tfq_similarity_threshold: float, quality_threshold: float, db_id: str):
    # eliminamos el contenido de los archivos de persistencia de embeddings
    utils.delete_all_content_hdf5(db_id, hdf5_file='embeddings.h5')
    
    # preguntas "Opción Múltiple"
    print("Generating MCQs...")
    for i in range(1, 21): # 21
        question_type = 1
        if (i % 3 == 0):
            question_difficulty_int = 1
        else:
            question_difficulty_int = 2
    
        try:
            graph.use_graph(
                question_type,
                question_difficulty_int,
                mcq_similarity_threshold,
                quality_threshold,
                db_id
            )
            # time.sleep(120)
            pass
        except Exception as e:
            print(f"Error al cargar la pregunta {i}: {e}")
            continue
    
    # preguntas "Verdadero o Falso"
    print("Generating TFQs...")
    for i in range(1, 11): # 11
        question_type = 3
        if (i % 3 == 0):
            question_difficulty_int = 1
        else:
            question_difficulty_int = 2
     
        try:
            graph.use_graph(
                question_type,
                question_difficulty_int,
                tfq_similarity_threshold,
                quality_threshold,
                db_id
            )
            # time.sleep(30)
        except Exception as e:
            print(f"Error al cargar la pregunta {i}: {e}")
            continue
    
    # preguntas de Respuesta Abierta
    print("Generating OEQs...")
    for i in range(1, 11): # 11
        question_type = 2
        if (i % 3 == 0):
            question_difficulty_int = 1
        else:
            question_difficulty_int = 2
     
        try:
            graph.use_graph(
                question_type,
                question_difficulty_int,
                tfq_similarity_threshold,
                quality_threshold,
                db_id
            )
            # time.sleep(30)
        except Exception as e:
            print(f"Error al cargar la pregunta {i}: {e}")
            continue
    
    # eliminamos el contenido de los archivos de persistencia de embeddings
    utils.delete_all_content_hdf5(db_id, hdf5_file='embeddings.h5')

# if __name__ == "__main__":
#     quality_threshold = 0.82
#     mcq_similarity_threshold = 0.8
#     tfq_similarity_threshold = 0.8
#     print('--- GENERATING FOR FIRST DATABASE ---')
#     generate_qandas(mcq_similarity_threshold, tfq_similarity_threshold, quality_threshold, db_id='TXVHBV')
#     print('--- GENERATING FOR SECOND DATABASE ---')
#     generate_qandas(mcq_similarity_threshold, tfq_similarity_threshold, quality_threshold, db_id='XLAVUD')
#     print('--- GENERATING FOR THIRD DATABASE ---')
#     generate_qandas(mcq_similarity_threshold, tfq_similarity_threshold, quality_threshold, db_id='YNHXDE')
#     print('--- DONE ---')