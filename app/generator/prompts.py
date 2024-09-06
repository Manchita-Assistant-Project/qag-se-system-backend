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
Basado únicamente en las preguntas, opciones y respuestas de: \

{context}

----------------------------------------------------------------
Responde de forma corta si la respuesta: \

{answer} \

es la respuesta correcta o incorrecta a la pregunta: \

{question}
----------------------------------------------------------------
Responde "¡La respuesta es correcta!" o "La respuesta es incorrecta...".
"""

FEEDBACK_PROMPT = """
Answer the question based only on the following context:

{context}

-----------------------------------------------------------

Answer the question based on the above context: {question}
"""