# Prompts para tools involucradas con el grafo generador de preguntas y respuestas 

Q_MCQ_PROMPT = """
Eres un modelo que genera preguntas de opción múltiple a partir \
únicamente de: \

"{context}"

---------------------------------------------------------------------------------
Y diferentes de:

"{generated_questions}"

---------------------------------------------------------------------------------
Debes siempre generar una (1) pregunta. \
    
---------------------------------------------------------------------------------
La pregunta debe ser de nivel: "{difficulty}"

---------------------------------------------------------------------------------
{harder_prompt}
"""


Q_OAQ_PROMPT = """
Eres un modelo que genera preguntas de respuesta abierta a partir \
únicamente de: \

{context}

---------------------------------------------------------------------------------
Debes siempre generar una (1) pregunta. \
    
---------------------------------------------------------------------------------
La pregunta debe ser de nivel: "{difficulty}"

---------------------------------------------------------------------------------
Es muy importante que la pregunta que generes no sea igual a ninguna pregunta
en este arreglo de preguntas:

{generated_questions}

---------------------------------------------------------------------------------
{harder_prompt}
"""


Q_TFQ_PROMPT = """
Eres un modelo que genera preguntas de respuesta VERDADERA o FALSA a partir \
únicamente de: \

{context}

---------------------------------------------------------------------------------
Es importante que la pregunta que generes sólo se pueda responder \
con únicamente con opciones "Verdadero" o "Falso".

Nunca pongas una opción "No se menciona en el texto" o similar.

---------------------------------------------------------------------------------
Debes siempre generar una (1) pregunta. \
    
---------------------------------------------------------------------------------
La pregunta debe ser de nivel: "{difficulty}"

---------------------------------------------------------------------------------
Es muy importante que la pregunta que generes no sea igual a ninguna pregunta
en este arreglo de preguntas:

{generated_questions}

---------------------------------------------------------------------------------
{harder_prompt}
"""


HARDER_Q_PROMPT = """
---------------------------------------------------------------------------------
Haz esta pregutna más difícil:

"{question}"

Y única y exclusivamente basándote en el contexto:

"{context}"

---------------------------------------------------------------------------------
Hacer una pregunta más difícil no significa hacerla más larga que
tenga más palabras.

Lo importante es el nivel del contenido de la pregunta. ¡Hazla más difícil, \
no la hagas solamente más larga.

Solo debes generar una pregunta. No hagas ningún "Además, ..." ni nada del estilo.

---------------------------------------------------------------------------------
No cambies el tipo de pregunta. El tipo de pregunta es:

"{question_type}"

---------------------------------------------------------------------------------
ES MUY IMPORTANTE QUE LA PREGUNTA QUE GENERES SEA DEL MISMO TIPO QUE LA \
PREGUNTA ORIGINAL.

SI LA PREGUNTA ORIGINAL ERA DE OPCIÓN MÚLTIPLE, RETORNAS UNA PREGUNTA DE \
OPCIÓN MÚLTIPLE.

SI LA PREGUNTA ORIGINAL ERA DE RESPUESTA ABIERTA, RETORNAS UNA PREGUNTA DE \
RESPUESTA ABIERTA.

SI LA PREGUNTA ORIGINAL ERA DE VERDADERO Y FALSO, RETORNAS UNA PREGUNTA DE \
VERDADERO Y FALSO.

---------------------------------------------------------------------------------
NO INCLUYAS EL TIPO DE PREGUNTA EN LA PREGUNTA QUE GENERES.

No tienes por qué poner el tipo de la pregunta en la pregunta que generes.
"""


Q_EVALUATION_PROMPT = """
Dada la definición de las siguientes métricas de evaluación humanas:

- Gramaticalidad: Mide la corrección gramatical de la pregunta generada, independientemente del contexto.

- Adecuación: Examina la corrección semántica de la pregunta sin importar el contexto.

- Relevancia: Mide el grado en que la pregunta generada es pertinente y está alineada con el contexto dado.

- Complejidad: Estima el nivel de razonamiento o esfuerzo cognitivo requerido para responder la pregunta generada.

- Novedad: Mide la originalidad y el carácter distintivo de la pregunta generada en comparación con una pregunta estándar para el contexto dado.

Evalúa la siguiente pregunta generada: "{generated_question}"

Use this context to evaluate the generated question: "{context}"

Proporciona una calificación entre 0 y 1 para cada criterio e incluye una breve justificación para la puntuación asignada a cada uno.

Siempre retorna las cinco (5) métricas de evaluación y su respectiva justificación.
"""


Q_REFINER_PROMPT = """
Dado esta retroalimentación que contiene métricas de evaluación humanas:

"{feedback}"

Modifica la siguiente pregunta: "{generated_question}"

Ten en cuenta que la pregunta tuvo un valor de calidad final de: {quality}

--------------------------------------------------------------------------------
Modifica la pregunta generada para que las métricas en el feedback promedien {threshold}

---------------------------------------------------------------------------------
Es muy importante que la pregunta que generes no sea igual a ninguna pregunta
en este arreglo de preguntas:

{generated_questions_string}

----------------------------------------------------------------------------------
¡Haz que la pregunta sea creativa, pero siempre teniendo en cuenta el `contexto`!

----------------------------------------------------------------------------------
Nunca cambies el tipo de pregunta!

Tipo de la pregunta: "{question_type}"
    
----------------------------------------------------------------------------------
Nunca retornes la misma pregunta generada. ¡Siempre mejórala!

----------------------------------------------------------------------------------
Solo retorna la versión mejorada de la pregunta generada.

No retornes nunca texto como "Pregunta mejorada: ..." o "Versión mejorada: ...". o nada similar.
"""


A_MCQ_PROMPT = """
Eres un modelo que genera respuestas de opción múltiple a partir \
únicamente de: \

{context}

---------------------------------------------------------------------------------
Una de las respuestas que generes debe responder la pregunta:

"{question}"

---------------------------------------------------------------------------------
Las respuestas que hagas, generalas todas en un formato de varias opciones. \
Un ejemplo de esto sería: \
a.) Posible respuesta 1 \
b.) Posible respuesta 2 \
c.) Posible respuesta 3 \
d.) Posible respuesta 4 \

---------------------------------------------------------------------------------
Haz que las respuestas sean muy variadas entre sí y entre cada pregunta. \

---------------------------------------------------------------------------------
Nunca generes más de cuatro (4) posibles respuestas.

---------------------------------------------------------------------------------
Las respuestas debe ser de nivel: "{difficulty}"

---------------------------------------------------------------------------------
Debes retornar la pregunta ("{question}"), opciones y respuesta correcta en formato JSON. \
Aquí un ejemplo: \

    "question": "¿Cuál es la capital de Colombia?", \
    "choices": ( \
        "a": "Bogotá", \
        "b": "Medellín", \
        "c": "Cali", \
        "d": "Barranquilla" \
    ), \
    "answer": "a" \
        
dentro de un diccionario Python.
"""


A_OAQ_PROMPT = """
Eres un modelo que genera respuestas de respuesta abierta a partir \
únicamente de: \

{context}

---------------------------------------------------------------------------------
Una de las respuestas que generes debe responder la pregunta:

"{question}"

---------------------------------------------------------------------------------
Las respuestas que hagas, generalas todas en un formato de varias opciones. \
Un ejemplo de esto sería: \
a.) Posible respuesta 1 \
b.) Posible respuesta 2 \
c.) Posible respuesta 3 \
d.) Posible respuesta 4 \

---------------------------------------------------------------------------------
Haz que las respuestas sean muy variadas entre sí y entre cada pregunta. \
    
---------------------------------------------------------------------------------
Nunca generes más de cuatro (4) posibles respuestas.
    
---------------------------------------------------------------------------------
Las respuestas debe ser de nivel: "{difficulty}"

---------------------------------------------------------------------------------
Debes retornar la pregunta ("{question}"), opciones de respuesta correcta en formato JSON. \
Aquí un ejemplo: \

    "question": "¿Cuál es la capital de Colombia?", \
    "choices": ( \
        "a": "Bogotá", \
        "b": "Medellín", \
        "c": "Cali", \
        "d": "Barranquilla" \
    ), \
    "answer": "None" \
        
dentro de un diccionario Python.
"""


A_TFQ_PROMPT = """
Genera respuestas de opción VERDADERO y FALSO basadas en el siguiente contexto:

{context}

---------------------------------------------------------------------------------
Una de las respuestas debe responder la siguiente pregunta:

"{question}"

---------------------------------------------------------------------------------
Las respuestas deben estar en formato de varias opciones. Un ejemplo sería:

a.) Opción de respuesta 1
b.) Opción de respuesta 2

---------------------------------------------------------------------------------
Las únicas dos opciones válidas son "Verdadero" y "Falso".

---------------------------------------------------------------------------------
La respuesta debe ser de nivel de dificultad: "{difficulty}"

---------------------------------------------------------------------------------
Por favor, retorna la pregunta ("{question}"), una opción incorrecta y la respuesta correcta en formato JSON.
Aquí tienes un ejemplo:

(
    "question": "¿Bogotá es la capital de Colombia?",
    "choices": (
        "a": "Verdadero",
        "b": "Falso"
    ),
    "answer": "b"
)

Devuelve todo dentro de un diccionario Python.
"""


TEN_Q_MCQ_PROMPT = """
Eres un modelo que genera preguntas de opción múltiple a partir \
únicamente de: \

"{context}"

---------------------------------------------------------------------------------
Debes siempre generar diez (10) preguntas. \
    
---------------------------------------------------------------------------------
Dos tercios (2/3) de las preguntas deben ser de nivel "Fácil". \
    
Un tercio (1/3) de las preguntas deben ser de nivel "Difícil".

---------------------------------------------------------------------------------
Debes siempre retornar las preguntas y las dificultades en una estructura JSON:

Aquí un ejemplo: \
[
    (
        "question": "¿Cuál es la capital de Colombia?", \
        "difficulty": "Fácil" \
    ),
]

---------------------------------------------------------------------------------
Siempre retorna el formato completo para todas las preguntas.
"""


TEN_Q_TFQ_PROMPT = """
Genera diez (10) preguntas de respuesta VERDADERA o FALSA basadas en el siguiente contexto:

{context}

---------------------------------------------------------------------------------
Las preguntas deben ser formuladas de manera que solo puedan ser respondidas con "Verdadero" o "Falso".

---------------------------------------------------------------------------------
Las preguntas deben ser formuladas siempre como preguntas, no como afirmaciones.

---------------------------------------------------------------------------------
¡Por favor, intenta ser lo más creativo que puedas con las preguntas!

---------------------------------------------------------------------------------
Ocho (8) de las preguntas deben ser de nivel "Fácil" y dos (2) deben ser de nivel "Difícil".

---------------------------------------------------------------------------------
Por favor, retorna las preguntas y las dificultades en el siguiente formato JSON:

[
    (
        "question": "¿Cuál es la capital de Colombia?",
        "difficulty": "Fácil"
    ),
    ...
]

---------------------------------------------------------------------------------
Asegúrate de seguir siempre este formato y estructura para todas las preguntas generadas.
"""

