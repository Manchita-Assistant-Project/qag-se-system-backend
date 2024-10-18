import os
import re
import json
import h5py
import string
import numpy as np
from typing import Dict, List

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
JSON_PATH = os.path.join(base_dir, "generator", "q&as")
HDF5_PATH = os.path.join(base_dir, "generator", "embeddings")

# ==== #
# JSON #
# ==== #

def load_json(filename: str):
    path = os.path.join(JSON_PATH, filename + '.json')
    with open(path, 'r', encoding='utf-8') as f:
        json_dict = json.load(f)

    if "content" not in json_dict or not isinstance(json_dict["content"], list):
        json_dict["content"] = []

    return json_dict['content']

def update_json(filename: str, data: dict):
    path = os.path.join(JSON_PATH, filename + '.json')
    with open(path, 'r', encoding='utf-8') as f:
        json_dict = json.load(f)
    
    if "content" not in json_dict or not isinstance(json_dict["content"], list):
        json_dict["content"] = []

    json_dict["content"].append(data)

    with open(path, 'w', encoding='utf-8') as f:
        json.dump(json_dict, f, ensure_ascii=False, indent=4)

def delete_content_json(filename: str):
    path = os.path.join(JSON_PATH, filename + '.json')
    with open(path, 'r', encoding='utf-8') as f:
        json_dict = json.load(f)
        
    json_dict["content"] = []
    
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(json_dict, f, ensure_ascii=False, indent=4)

def delete_local_file(file_path):
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            print(f"Archivo eliminado: {file_path}")
        else:
            print(f"El archivo no existe: {file_path}")
    except Exception as e:
        print(f"Error al eliminar el archivo {file_path}: {e}")

# ==== #
# HDF5 #
# ==== #

def load_embeddings_hdf5(question_type, hdf5_file='embeddings.h5'):
    types = ['mcqs', 'oaqs', 'tfqs']
    correct_file = types[question_type - 1]

    path = os.path.join(HDF5_PATH, hdf5_file)
    with h5py.File(path, 'r') as f:
        if correct_file in f and 'content' in f[correct_file]:
            return f[correct_file]["content"][:]
        else:
            return []

def save_embedding_hdf5(embedding, question_type, hdf5_file='embeddings.h5'):
    types = ['mcqs', 'oaqs', 'tfqs']
    correct_file = types[question_type - 1]

    path = os.path.join(HDF5_PATH, hdf5_file)
    with h5py.File(path, 'a') as f:
        # si el grupo no existe para este tipo de pregunta, lo creamos
        if correct_file not in f:
            f.create_group(correct_file)
        
        dataset = f[correct_file]

        if 'content' not in dataset:
            # si no existe el dataset "content", lo creamos con el primer embedding
            dataset.create_dataset("content", data=np.array([embedding]), maxshape=(None, len(embedding)))
        else:
            # añadir el nuevo embedding al dataset existente
            data = dataset["content"]
            data.resize((data.shape[0] + 1, data.shape[1]))
            data[-1] = embedding

def delete_content_hdf5(question_type, hdf5_file='embeddings.h5'):
    types = ['mcqs', 'oaqs', 'tfqs']
    correct_file = types[question_type - 1]

    path = os.path.join(HDF5_PATH, hdf5_file)
    if os.path.exists(path):
        with h5py.File(path, 'a') as f:
            # eliminar el dataset "content" si existe
            if correct_file in f and 'content' in f[correct_file]:
                del f[correct_file]['content']  # elimina el dataset de embeddings
                print(f"Contenido de '{correct_file}' eliminado.")
            else:
                print(f"No se encontró el contenido en '{correct_file}'.")
    else:
        print(f"El archivo {hdf5_file} no existe.")

def delete_all_content_hdf5(hdf5_file='embeddings.h5'):
    types = ['mcqs', 'oaqs', 'tfqs']
    
    path = os.path.join(HDF5_PATH, hdf5_file)
    for question_type in range(1, len(types) + 1):
        delete_content_hdf5(question_type, path)

# ========== #
# MORE UTILS # 
# ========== #

def generate_graph_image(runnable):
    i = runnable.get_graph().draw_mermaid_png()
    with open("app/generator/graph.png", "wb") as png:
        png.write(i)

def choices_list_to_dict(choices_list: List[str]) -> Dict[str, str]:
    result = {}
    letters = iter(string.ascii_lowercase)  # iterador de letras 'a', 'b', 'c', etc.
    
    for item in choices_list:
        # usamos una expresión regular para agarrar la letra (a, b, c, etc.) seguida de cualquier combinación de ) o .)
        match = re.match(r'^([a-zA-Z])[\.\)]\s*(.*)', item)
        if match:
            letter = match.group(1)
            text = match.group(2)
            result[letter] = text
        else:
            # si no hay prefijo con letra, usamos la siguiente letra del iterador
            letter = next(letters)
            result[letter] = item
    
    return result

def structure_generated_questions_string(generated_questions: list):
    result = ""
    for item in generated_questions:
        result += f"- {item}\n"
        result += "\n"
    return result
