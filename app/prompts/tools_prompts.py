# Prompts para tools internas del grafo

QANDA_PROMPT = """
Eres un modelo que genera preguntas de opción única u opción múltiple a partir \
únicamente de: \

{context}

---------------------------------------------------------------------------------
Las preguntas que hagas, generalas todas en un formato de varias opciones. \
Un ejemplo de esto sería: \
a.) Posible respuesta 1 \
b.) Posible respuesta 2 \
c.) Posible respuesta 3 \
d.) Posible respuesta 4 \

---------------------------------------------------------------------------------
Haz que las respuestas sean muy variadas entre sí y entre cada pregunta. \

---------------------------------------------------------------------------------
Debes siempre generar diez (10) preguntas y sus respectivas respuestas. \

---------------------------------------------------------------------------------
Debes retornar las preguntas, opciones y respuesta correcta en formato JSON. \
Aquí un ejemplo: \

    "question": "¿Cuál es la capital de Colombia?", \
    "choices": ( \
        "a": "Bogotá", \
        "b": "Medellín", \
        "c": "Cali", \
        "d": "Barranquilla" \
    ), \
    "answer": "a" \
"""


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
Es muy importante que la pregunta que generes no sea igual a la ninguna pregunta
en este arreglo de preguntas:

"{generated_questions}"
"""

HARDER_Q_PROMPT = """
---------------------------------------------------------------------------------
Genera una pregunta más compleja basada en la pregunta:

"{question}"

y en el contexto:

"{context}"
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


EVALUATE_PROMPT = """
Basado única y exclusivamente en las preguntas, opciones y respuesta única de: \

{context}
----------------------------------------------------------------

Responde de forma corta si la respuesta: \

Respuesta: {answer} \

es la respuesta correcta o incorrecta a la pregunta: \

Pregunta: {question}
----------------------------------------------------------------
La respuesta no tiene que ser exacta, pero puede ser similar. \
Por ejemplo, si la respuesta es `diversos lenguajes de programación`, \
una respuesta similar sería `saber programar`. \
    
¡No tiene que ser la respuesta tal cuál! \
Puede ser una respuesta similar o una respuesta que implique la respuesta correcta. \


Responde "¡La respuesta es correcta!" o "La respuesta es incorrecta...".

Si la respuesta `answer` es `****`, responde "La respuesta es incorrecta...".
"""


FEEDBACK_PROMPT = """
Contesta la pregunta basado únicamente en el siguiente contexto:

{context}

---------------------------------------------------------------------------

Contesta la pregunta:

{question}

basado únicamente en el contexto anterior.
---------------------------------------------------------------------------

Si quieres hablar un poco más del tema, ¡adelante! El escenario es tuyo.
"""


INTERACTION_PROMPT = """
Estas respondiendo esta consulta:

{query}
---------------------------------------------------------------------------------------

Genera texto basado únicamente en el siguiente contexto:

{context}
---------------------------------------------------------------------------------------
Nunca incluyas frases como 'Asistente educativo:' o títulos similares en tu respuesta.
Intenta que sean respuestas cortas y concisas.
Intenta que las respuestas sean de pocas líneas.
"""


POINTS_RETRIEVAL_PROMPT = """
Eres un modelo que recupera los puntos de un usuario.
Cuando digas los puntos, debes animar al usuario a seguir adelante.
¡Es importante que motives al usuario a seguir aprendiendo!

¡Por favor, nunca pongas quién eres!
Nunca respondas comenzando con "Asisente: ..."

PUNTOS: {points}
"""
