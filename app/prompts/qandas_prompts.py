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


Q_OEQ_PROMPT = """
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

- Claridad: ¿Es fácil de entender la pregunta y menciona claramente los conceptos clave que se están preguntando? La pregunta debe incluir explícitamente los elementos importantes en lugar de dejarlos implícitos. Por ejemplo, si se refiere a una asignatura, la pregunta no debería ser vaga como "¿Cuál es el objetivo de esta asignatura?", sino que debería especificar claramente a qué se refiere. Si aparece un concepto específico del contexto, es importante que esté claro qué significa dentro de la pregunta. Una puntuación de 1 indica que la pregunta es clara y no tiene ambigüedades, mientras que una puntuación más baja sugiere vaguedad o posible confusión.

- Contextualización: ¿Aprovecha la pregunta los elementos específicos del contexto, mostrando una comprensión detallada de la información dada? Esto implica que la pregunta no solo es relevante, sino que integra términos, detalles o conceptos únicos presentes en el contexto proporcionado. Una puntuación de 1 indica que la pregunta está claramente contextualizada y refleja los detalles únicos del tema, mientras que una puntuación más baja sugiere que la pregunta podría ser genérica o no aprovechar la especificidad del contexto.

- Complejidad: ¿La pregunta demuestra un nivel de pensamiento más profundo, o es demasiado simple? Este criterio observa cuánta reflexión requiere la pregunta para responder y si desafía al lector a reflexionar o analizar. Una puntuación de 1 indica que la pregunta es apropiadamente desafiante para el contexto, mientras que una puntuación más baja sugiere que es demasiado básica o demasiado avanzada para la situación.

- Originalidad: ¿La pregunta es única o parece una pregunta estándar que podría hacerse en cualquier situación similar? Si la pregunta generada se siente genérica o sobreutilizada, penaliza la originalidad. Una puntuación de 1 indica que la pregunta es altamente original y creativa, mientras que una puntuación más baja se debe otorgar a preguntas que parecen comunes.

Evalúa la siguiente pregunta generada: "{generated_question}"

Usa este contexto para evaluar la pregunta generada: "{context}"

Proporciona una calificación entre 0 y 1 para cada criterio e incluye una breve justificación para la puntuación asignada a cada uno.

Siempre retorna las cuatro (4) métricas de evaluación y su respectiva justificación.

Por favor, nunca agregues símbolos como "*" a tu respuesta.
"""


Q_REFINER_PROMPT = """
Dado esta retroalimentación que contiene métricas de evaluación humanas:

"{feedback}"

Modifica la siguiente pregunta: "{generated_question}"

Ten en cuenta que la pregunta tuvo un valor de calidad final de: {quality}

--------------------------------------------------------------------------------
Modifica la pregunta generada para que las métricas en el feedback promedien {threshold}

Analiza la retroalimentación y realiza los cambios necesarios para mejorar la calidad de la pregunta.

Revisa las métricas de evaluación que tienen valores bajos y realiza los cambios necesarios para mejorarlas.

Es importante que tengas en cuenta que "mejorar la pregunta" no siempre es hacerla más larga o agregarle preguntas.
Ten en cuenta las métricas de evaluación y el feedback para MODIFICAR la pregunta.

----------------------------------------------------------------------------------
Nunca cambies el tipo de pregunta!

Tipo de la pregunta: "{question_type}"
    
----------------------------------------------------------------------------------
Nunca retornes la misma pregunta generada. ¡Siempre mejórala!

¡Hazle cambios significativos!

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
Las respuestas deben generarse en un formato de opciones múltiples. \
Un ejemplo de esto sería: \
a.) Posible respuesta 1 \
b.) Posible respuesta 2 \
c.) Posible respuesta 3 \
d.) Posible respuesta 4 \

---------------------------------------------------------------------------------
Asegúrate de que las respuestas sean muy variadas entre sí y entre cada pregunta. \

Nunca generes más de cuatro (4) opciones posibles. \

---------------------------------------------------------------------------------
Las respuestas deben ser de nivel: "{difficulty}"

---------------------------------------------------------------------------------
**ETAPA DE GENERACIÓN**: Genera una pregunta en el siguiente formato, incluyendo opciones \
y la respuesta correcta, en un diccionario Python:
(
    "question": "{question}",
    "choices": (
        "a": "Respuesta 1",
        "b": "Respuesta 2",
        "c": "Respuesta 3",
        "d": "Respuesta 4"
    ),
    "answer": "c"  # Esta es la opción correcta
)

No todas las respuestas correctas deben ser la opción "c"; \
varíalas aleatoriamente entre las cuatro (4) opciones (recuerda que las opciones son "a", "b", "c", "d"). \

---------------------------------------------------------------------------------
**ETAPA DE VERIFICACIÓN DE RESPUESTA CORRECTA**: Revisa si la respuesta marcada \
en "answer" es realmente la más adecuada y precisa según el contexto proporcionado. \
Si encuentras algún problema, ajusta las opciones para asegurar que la respuesta \
correcta esté bien identificada.

---------------------------------------------------------------------------------
**ETAPA DE VERIFICACIÓN DE RESPUESTAS INCORRECTAS**: Ahora verifica cada opción \
incorrecta para asegurarte de que sean respuestas plausibles pero incorrectas. \
Las respuestas incorrectas deben estar relacionadas con el contexto pero ser claramente \
falsas o menos adecuadas que la respuesta correcta, sin ser demasiado evidentes. \
Asegúrate de que ninguna de las respuestas incorrectas pueda confundirse fácilmente \
con la respuesta correcta.

---------------------------------------------------------------------------------
Retorna el diccionario final en el siguiente formato: 

(
    "question": "{question}",
    "choices": (
        "a": "Respuesta 1",
        "b": "Respuesta 2",
        "c": "Respuesta 3",
        "d": "Respuesta 4"
    ),
    "answer": "c"  # Esta es la opción correcta después de verificación
)
"""


A_OEQ_PROMPT = """
Eres un modelo que genera respuestas a partir \
únicamente de: \

{context}

---------------------------------------------------------------------------------
Debes generar cinco (5) respuestas correctas que respondan la pregunta:

"{question}"

---------------------------------------------------------------------------------
Las respuestas que hagas, generalas todas en un formato de varias opciones. \
Un ejemplo de esto sería: \
a.) Respuesta correcta 1 \
b.) Respuesta correcta 2 \
c.) Respuesta correcta 3 \
d.) Respuesta correcta 4 \
e.) Respuesta correcta 5 \

---------------------------------------------------------------------------------
Haz que las respuestas sean muy variadas entre sí. \
    
---------------------------------------------------------------------------------
Las respuestas debe ser de nivel: "{difficulty}"

---------------------------------------------------------------------------------
Debes retornar la pregunta ("{question}"), opciones de respuesta correcta en formato JSON. \
Aquí un ejemplo: \

    "question": "¿Cómo ha influido la serie Friends en la cultura popular?", \
    "choices": ( \
        "a": "Friends popularizó frases icónicas como "We were on a break!" y estilos de vida, convirtiéndose en un fenómeno de referencia en la cultura pop.", \
        "b": "La serie redefinió las comedias de situación al centrarse en un grupo de amigos, inspirando a numerosas comedias con formatos similares.", \
        "c": "Friends estableció un estándar de estilo en moda y cortes de cabello, como el peinado "Rachel", que marcó tendencia en los años 90.", \
        "d": "Su enfoque en temas universales, como el amor y la amistad, la convirtió en una serie que trasciende generaciones y sigue siendo popular hoy en día.", \
        "e": "La dinámica y química entre los personajes mostró la importancia del elenco en el éxito de una serie, influenciando futuras producciones de comedia." \
    ), \
    "answer": "None" \
        
dentro de un diccionario Python.

Nunca olvides ninguno de los tres (3) elementos: "question", "choices" y "answer".
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


TEN_Q_OEQ_PROMPT = """
Genera diez (10) preguntas de respuesta abierta que permitan respuestas detalladas
y con múltiples enfoques, basadas en el siguiente contexto:

{context}

---------------------------------------------------------------------------------
Las preguntas deben ser formuladas siempre como preguntas, no como afirmaciones.

---------------------------------------------------------------------------------
Intenta que las preguntas sean amplias y favorezcan respuestas largas, diversas y
con interpretaciones variadas, permitiendo que el respondiente aporte ideas
propias o analice el contexto en profundidad.

---------------------------------------------------------------------------------
Ocho (8) de las preguntas deben ser de nivel "Fácil" y dos (2) deben ser de nivel
"Difícil". Asegúrate de que las preguntas de nivel "Difícil" requieran un análisis
más profundo del contexto o permitan múltiples perspectivas complejas.

---------------------------------------------------------------------------------
Por favor, retorna las preguntas y las dificultades en el siguiente formato JSON:

[
    (
        "question": "¿De qué manera ha influido la serie Friends en la cultura \
                     popular y en las relaciones entre amigos en la vida real?",
        "difficulty": "Fácil"
    ),
    ...
]

---------------------------------------------------------------------------------
Asegúrate de seguir siempre este formato y estructura para todas las preguntas generadas.
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


FORMAT_QANDAS_PROMPT = """
Dado el siguiente texto que contiene preguntas y respuestas:

"{document_string}"

Quiero que formatees las preguntas y respuestas en el siguiente formato JSON:
[
    (
        "question": "¿Cuál es la capital de Colombia?",
        "choices": (
            "a": "Bogotá",
            "b": "Medellín",
            "c": "Cali",
            "d": "Barranquilla"
        ),
        "answer": "a",
        "type": "MCQ",
        "difficulty": "Fácil"
    ),
]

Es importante que diferencies entre las preguntas de opción múltiple (MCQ), de respuesta abierta (OEQ) y de verdadero o falso (TFQ).

Ejemplo de una pregunta de OPCIÓN MÚLTIPLE (MCQ):
(
    "question": "¿Cuál es la capital de Colombia?",
    "choices": (
        "a": "Bogotá",
        "b": "Medellín",
        "c": "Cali",
        "d": "Barranquilla"
    ),
    "answer": "a",
    "type": "MCQ",
    "difficulty": "Fácil"
)

Ejemplo de una pregunta de RESPUESTA ABIERTA (OEQ):
(
    "question": "¿Cómo evoluciona la relación entre Ross y Rachel en Friends?",
    "choices": (
        "a": "Comienzan su relación en la temporada 2 después de un primer beso en Central Perk.",
        "b": "Terminan en la temporada 3 tras el "break" y la infidelidad de Ross.",
        "c": "Se casan accidentalmente en Las Vegas y luego anulan el matrimonio.",
        "d": "Rachel queda embarazada y crían a su hija Emma juntos.",
        "e": "En el final, Ross confiesa su amor y Rachel decide quedarse en Nueva York."
    ),
    "answer": "None",
    "type": "OEQ",
    "difficulty": "Difícil"
)

Ejemplo de una pregunta VERDADERO O FALSO (TFQ):
(
    "question": "¿Es el río Nilo el río más largo del mundo?",
    "choices": (
        "a": "Verdadero",
        "b": "Falso"
    ),
    "answer": "b",
    "type": "TFQ",
    "difficulty": "Fácil"
)
--------------------------------------------------------------------------

Por favor, NUNCA olvides el diccionario "choices".
¡Es muy importante!
"""
