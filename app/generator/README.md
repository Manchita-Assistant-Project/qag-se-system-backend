# Generator Graph

<p align="center">
  <img src="https://github.com/user-attachments/assets/8db8ac34-2b49-4da5-b67c-8eedceb17be9" alt="Generator Graph Architecture" width="400"/>
</p>

Below is a brief overview of each node and conditional edge in the agent graph:

### Nodes

- **`context_generator`**: Retrieves the necessary context for question generation by querying a vector database and retrieving up to *k* relevant results.
- **`question_generator`**: Generates ten questions based on the provided context. The results depend on the desired difficulty level.
- **`question_seen_validator`**: Calculates the cosine similarity between each of the newly generated ten questions and every *already-generated* question from earlier iterations, selecting the question with the lowest similarity value.
- **`question_evaluator`**: Evaluates the validated question using an LLM agent. The quality is assessed based on five aspects: grammaticality, relevance, appropriateness, novelty, and complexity. The LLM returns a score between 0 and 1 for each metric. Then, the average rating is computed to determine the overall quality of the question.
- **`question_refiner`**: Refines the evaluated question using an LLM, aiming to surpass an established threshold. The prompt includes: the obtained metrics, feedback, and instructions to modify the question so that the metrics exceed the threshold.
- **`messages_remover`**: Removes messages from the `messages` list in the global state of the graph.
- **`answer_generator`**: Takes the evaluated and refined question, performs a RAG search using the question as the query, and generates corresponding answers depending on the question type.
- **`qanda_saver`**: Takes a JSON structure containing the question, answer choices, correct answer, question type, and difficulty, and adds it to a JSON file where all questions and their answers are stored.

### Conditional Edges

- **`question_or_answer_path`**: Directs the graph's execution from the `context_generator` node to either the `question_generator` or `answer_generator`, depending on whether there is already an approved question.
- **`question_already_seen`**: Directs the graph's execution from the `question_seen_validator` node to either the `messages_remover` or `question_evaluator` nodes, depending on whether all generated questions surpass the similarity threshold.  
  - If all questions exceed the threshold, a new context is generated to attempt creating different questions.
- **`question_approved`**: Directs the graph's execution from the `question_evaluator` node to either the `question_refiner` or `messages_remover`, depending on whether the question surpasses the quality threshold.
