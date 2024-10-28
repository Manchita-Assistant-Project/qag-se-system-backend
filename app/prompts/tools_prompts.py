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


EVALUATE_PROMPT = """
Basado única y excluvisamente en esta cadena: \

`{context}`
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

Si la respuesta es incorrecta, responde "La respuesta es incorrecta..." y \
agrega la respuesta correcta: "{right_answer}".
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


RESPONSE_CLASSIFIER_PROMPT = """
Debes determinar si la respuesta: "{response}"
Es una posible respuesta a la pregunta: "{question}"

Una posible respuesta no necesariamente es una correcta,
simplemente es una posible respuesta (correcta o incorrecta).

Por ejemplo, dada la pregunta: "¿Cuál es la capital de Colombia?"

Una posible respuesta sería: "Bogotá".

Otra posible respuesta sería: "Medellín", aún así sea incorrecta.

Una no posible respuesta sería: "Queso".

Una no posible respuesta sería: "Dame una pista".

---------------------------------------------------------------------------------------
Responde "True" si sí es una posible respuesta a la pregunta.
"""
