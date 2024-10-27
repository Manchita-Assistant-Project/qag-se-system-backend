import csv
import json

# Ruta del archivo JSON
json_file = "databases\YNHXDE\q&as\qs.json"

# Leer el archivo JSON
with open(json_file, 'r', encoding='utf-8') as f:
    data = json.load(f)

csv_file = "databases\YNHXDE\q&as\qs_3.csv"
with open(csv_file, mode='w', newline='', encoding='utf-8-sig') as file:
    writer = csv.writer(file, delimiter=';')
    # Write the header
    writer.writerow(["Pregunta", "A", "B", "C", "D", "Respuesta", "Tipo", "Dificultad"])
    
    # Write the content
    for item in data["content"]:
        # Variables para asegurar que las opciones C y D solo se incluyan si están presentes
        choice_c = item["choices"].get("c", "")  # Si no hay opción C, poner un valor vacío
        choice_d = item["choices"].get("d", "")  # Si no hay opción D, poner un valor vacío
        
        writer.writerow([
            item["question"],
            item["choices"]["a"],
            item["choices"]["b"],
            choice_c,  # Se incluye C solo si está presente
            choice_d,  # Se incluye D solo si está presente
            item["answer"],
            item["type"],
            item["difficulty"]
        ])