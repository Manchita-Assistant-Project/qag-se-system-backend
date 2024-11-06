import csv
import json
import random

# Ruta del archivo JSON
json_file = "databases/UDXQOG/q&as/qs.json"
csv_file = "databases/UDXQOG/q&as/qs_2.csv"


def json_to_csv(json_file, csv_file):
    # Leer el archivo JSON
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    with open(csv_file, mode='w', newline='', encoding='utf-8-sig') as file:
        writer = csv.writer(file, delimiter=';')
        # Write the header
        writer.writerow(["Pregunta", "A", "B", "C", "D", "E", "Respuesta", "Tipo", "Dificultad"])
        
        # Write the content
        for item in data["content"]:
            # Variables para asegurar que las opciones C y D solo se incluyan si están presentes
            choice_c = item["choices"].get("c", "")  # Si no hay opción C, poner un valor vacío
            choice_d = item["choices"].get("d", "")  # Si no hay opción D, poner un valor vacío
            choice_e = item["choices"].get("e", "")  # Si no hay opción E, poner un valor vacío
            
            writer.writerow([
                item["question"],
                item["choices"]["a"],
                item["choices"]["b"],
                choice_c,  # Se incluye C solo si está presente
                choice_d,  # Se incluye D solo si está presente
                choice_e,  # Se incluye E solo si está presente
                item["answer"],
                item["type"],
                item["difficulty"]
            ])

# para sacar preguntas random de los jsons de preguntas
def get_random_questions(json_file, n, qtype):
    with open(json_file, 'r', encoding='utf-8-sig') as f:
        data = json.load(f)
    
    if qtype:
        population = [item for item in data["content"] if item["type"] == qtype]
        print(f"Population: {len(population)}")
        if len(population) < n:
            return None
        return random.sample(population, n)
    else:
        return random.sample(data["content"], n)

if __name__ == "__main__":
    json_files = ["databases/NKTQNH/q&as/qs.json", 
                  "databases/UDXQOG/q&as/qs.json", 
                  "databases/TXVHBV/q&as/qs.json"]
    filter_types = ["MCQ", "TFQ", "OEQ"]
    n = 3

    with open("qsandas_to_evaluate.csv", "w", newline='', encoding='utf-8-sig') as csvfile:
        writer = csv.writer(csvfile, delimiter=';')
        writer.writerow(["question", "A", "B", "C", "D", "E", "answer", "type", "difficulty", "ID", "batch"])

        i = 1
        for json_file in json_files:
            print(f"Processing {json_file}")
            for filter_type in filter_types:
                print(f"Filtering by {filter_type}")
                questions = get_random_questions(json_file, n, filter_type)
                if questions:
                    for item in questions:
                        # Usa .get() para cada clave opcional
                        writer.writerow([
                            item["question"],                 # Columna "question"
                            item["choices"].get("a", ""),     # Columna "A"
                            item["choices"].get("b", ""),     # Columna "B"
                            item["choices"].get("c", ""),     # Columna "C", vacía si no existe
                            item["choices"].get("d", ""),     # Columna "D", vacía si no existe
                            item["choices"].get("e", ""),     # Columna "E", vacía si no existe
                            item.get("answer", ""),           # Columna "answer"
                            item.get("type", ""),             # Columna "type"
                            item.get("difficulty", "") ,      # Columna "difficulty"
                            i,
                            json_file
                        ])
                        
                        i += 1
    
    
    
    
