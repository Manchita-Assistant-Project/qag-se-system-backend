# Prompts para tools involucradas con el grafo generador de preguntas y respuestas 

Q_MCQ_PROMPT = """
Eres un modelo que genera preguntas de opción múltiple a partir \
únicamente de: \

{context}

---------------------------------------------------------------------------------
Debes siempre generar una (1) pregunta. \
    
---------------------------------------------------------------------------------
La pregunta debe ser de nivel: "{difficulty}"

{harder_prompt}

---------------------------------------------------------------------------------
Es muy importante que la pregunta que generes no sea igual a ninguna pregunta
en este arreglo de preguntas:

"{generated_questions}"
"""


Q_OAQ_PROMPT = """
Eres un modelo que genera preguntas de respuesta abierta a partir \
únicamente de: \

{context}

---------------------------------------------------------------------------------
Debes siempre generar una (1) pregunta. \
    
---------------------------------------------------------------------------------
La pregunta debe ser de nivel: "{difficulty}"

{harder_prompt}

---------------------------------------------------------------------------------
Es muy importante que la pregunta que generes no sea igual a ninguna pregunta
en este arreglo de preguntas:

"{generated_questions}"
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

{harder_prompt}

---------------------------------------------------------------------------------
Es muy importante que la pregunta que generes no sea igual a ninguna pregunta
en este arreglo de preguntas:

"{generated_questions}"
"""


HARDER_Q_PROMPT = """
---------------------------------------------------------------------------------
Genera una pregunta más compleja basada en la pregunta:

"{question}"

Y única y exclusivamente en el contexto:

"{context}"

---------------------------------------------------------------------------------
Hacer una pregunta más compleja significa que la pregunta debe ser más difícil \
de responder, no necesariamente más larga ni más palabras.

Lo importante es el nivel del contenido de la pregunta. ¡Hazla más difícil, \
no la hagas solamente más larga.

Solo debes generar una pregunta. No hagas ningún "Además, ..." ni nada del estilo.

---------------------------------------------------------------------------------
No cambies el tipo de pregunta. El tipo de pregunta es:

"{question_type}"

ES MUY IMPORTANTE QUE LA PREGUNTA QUE GENERES SEA DEL MISMO TIPO QUE LA \
PREGUNTA ORIGINAL.

SI LA PREGUNTA ORIGINAL ERA DE OPCIÓN MÚLTIPLE, RETORNAS UNA PREGUNTA DE \
OPCIÓN MÚLTIPLE.
SI LA PREGUNTA ORIGINAL ERA DE RESPUESTA ABIERTA, RETORNAS UNA PREGUNTA DE \
RESPUESTA ABIERTA.
SI LA PREGUNTA ORIGINAL ERA DE VERDADER Y FALSO, RETORNAS UNA PREGUNTA DE \
VERDADERO Y FALSO.

---------------------------------------------------------------------------------
NO INCLUYAS EL TIPO DE PREGUNTA EN LA PREGUNTA QUE GENERES.

No tienes por qué poner el tipo de la pregunta en la pregunta que generes.
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
Eres un modelo que genera respuestas de opción VERDADERO y FALSO a partir \
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

---------------------------------------------------------------------------------
Haz que las respuestas sean muy variadas entre sí y entre cada pregunta. \
    
---------------------------------------------------------------------------------
Las respuestas debe ser de nivel: "{difficulty}"

---------------------------------------------------------------------------------
Debes retornar la pregunta ("{question}"), una opción incorrecta y respuesta correcta en formato JSON. \
Aquí un ejemplo: \

    "question": "¿Bogotá es la capital del Colombia?", \
    "choices": ( \
        "a": "Verdadero", \
        "b": "Falso", \
    ), \
    "answer": "b" \
        
dentro de un diccionario Python.
"""