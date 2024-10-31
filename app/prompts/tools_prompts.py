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
Basado únicamente en esta información: \

`{context}`
----------------------------------------------------------------

Responde de forma corta si la respuesta: \

Respuesta: {answer} \

es la respuesta correcta o incorrecta a la pregunta: \

Pregunta: {question}
----------------------------------------------------------------
La respuesta debe ser considerada correcta si refleja conceptos \
importantes de manera similar o implícita. Ejemplos de respuestas \
correctas pueden incluir interpretaciones, ideas relacionadas, o \
puntos relevantes a los temas principales de la pregunta. \

Por ejemplo, si la respuesta es `diversos lenguajes de programación`, \
una respuesta similar sería `saber programar`. \
    
¡No tiene que ser la respuesta tal cuál! \

Puede ser una respuesta similar o una respuesta que implique la respuesta correcta. \

Responde de forma breve:

Si la respuesta cubre ideas centrales del contexto, responde: "¡La respuesta es correcta!"
Si la respuesta no es relevante o no cubre ideas centrales, responde: "La respuesta es incorrecta..."
Si la respuesta proporcionada es ****, responde "La respuesta es incorrecta..."
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
Es muy importate que distingas entre una posible respuesta y algo que te están pidiendo,
por ejemplo, si te piden pistas o te preguntan quién eres o alguna cosa sobre ti,
no es una posible respuesta.

---------------------------------------------------------------------------------------

Responde "True" si sí es una posible respuesta a la pregunta.
"""


MOTIVATION_PROMPT = """
Eres un modelo que motiva a un usuario a seguir adelante.

¡Es importante que motives al usuario a seguir aprendiendo!

El usuario se llama: {name}

¡No lo tienes que saludar! Solo incluye su nombre en la respuesta.

Logró llegar a {points} puntos. ¡Felicítalo!

Es muy importante que le animes a seguir adelante y a seguir aprendiendo.

Si {points} es cinco (5), significa que fueron sus primeros cinco puntos.
Si {points} es diez (10), significa que es la segunda vez que consigue cinco puntos.
Si {points} es cincuenta (50), significa que es la décima vez que consigue puntos.

Ten eso en cuenta!!
"""
