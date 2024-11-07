import os
import re
import json
import time
import h5py
import string
import numpy as np
from typing import Dict, List

import app.database.chroma_utils as chroma_utils

base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
base_dir_app = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def verify_directory_exists(directory_path):
    if not os.path.exists(directory_path):
        os.makedirs(directory_path)
        print(f"Directory '{directory_path}' created.")
    else:
        print(f"Directory '{directory_path}' already exists.")
        
def verify_file_exists(file_path):
    ext = os.path.splitext(file_path)[-1].lower() # extensión del archivo en minúscula
    if not os.path.exists(file_path):
        with open(file_path, 'w') as file:
            if ext == ".json":
                json.dump({"content": []}, file, indent=4)
            else:
                pass
        print(f"File '{file_path}' created with initial content.")
    else:
        print(f"File '{file_path}' already exists.")

DATABASES_PATH = os.path.join(base_dir, 'databases')
verify_directory_exists(DATABASES_PATH)

JSON_PATH = os.path.join(base_dir_app, "generator", "q&as")
HDF5_PATH = os.path.join(base_dir_app, "generator", "embeddings")

# ==== #
# JSON #
# ==== #

def load_json(db_id: str, filename: str):
    path = os.path.join(DATABASES_PATH, db_id, 'q&as', filename + '.json')
    # time.sleep(5)
    verify_file_exists(path)
    with open(path, 'r', encoding='utf-8') as f:
        json_dict = json.load(f)

    if "content" not in json_dict or not isinstance(json_dict["content"], list):
        json_dict["content"] = []

    return json_dict['content']

def update_json(db_id: str, filename: str, data: dict):
    path = os.path.join(DATABASES_PATH, db_id, 'q&as', filename + '.json')
    verify_file_exists(path)
    
    with open(path, 'r', encoding='utf-8') as f:
        json_dict = json.load(f)
    
    if "content" not in json_dict or not isinstance(json_dict["content"], list):
        json_dict["content"] = []

    json_dict["content"].append(data)

    with open(path, 'w', encoding='utf-8') as f:
        json.dump(json_dict, f, ensure_ascii=False, indent=4)

def update_temp_json(temp_filename: str, data: dict):
    if os.path.exists(temp_filename):
        with open(temp_filename, 'r', encoding='utf-8') as f:
            json_dict = json.load(f)
    else:
        json_dict = {"content": []}

    json_dict["content"].append(data)

    with open(temp_filename, 'w', encoding='utf-8') as f:
        json.dump(json_dict, f, ensure_ascii=False, indent=4)

def merge_temp_files(temp_files, main_json_path):
    main_data = {"content": []}
    for temp_file in temp_files:
        with open(temp_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if "content" in data:
                main_data["content"].extend(data["content"])
    
    with open(main_json_path, 'w', encoding='utf-8') as f:
        json.dump(main_data, f, ensure_ascii=False, indent=4)

def delete_content_json(db_id: str, filename: str):
    path = os.path.join(DATABASES_PATH, db_id, 'q&as', filename + '.json')
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

def create_empty_hdf5_file(path):
    with h5py.File(path, 'w') as f:
        pass
    # print(f"Archivo HDF5 '{path}' creado vacío.")

def load_embeddings_hdf5(question_type: int, db_id: str, hdf5_file='embeddings.h5'):
    types = ['mcqs', 'oeqs', 'tfqs']
    correct_file = types[question_type - 1]

    path = os.path.join(DATABASES_PATH, db_id, 'embeddings', hdf5_file)

    # verificar si el archivo existe antes de abrirlo - crea uno nuevo si no existe
    if not os.path.exists(path):
        create_empty_hdf5_file(path)

    # abrir el archivo HDF5 si existe
    try:
        with h5py.File(path, 'r') as f:
            if correct_file in f and 'content' in f[correct_file]:
                return f[correct_file]["content"][:]
            else:
                return []
    except OSError as e:
        # print(f"Error al abrir el archivo HDF5: {e}")
        return []

def save_embedding_hdf5(embedding, question_type: int, db_id: str, hdf5_file='embeddings.h5'):
    types = ['mcqs', 'oeqs', 'tfqs']
    correct_file = types[question_type - 1]

    path = os.path.join(DATABASES_PATH, db_id, 'embeddings', hdf5_file)
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

def delete_content_hdf5(question_type: int, db_id: str, hdf5_file='embeddings.h5'):
    types = ['mcqs', 'oeqs', 'tfqs']
    correct_file = types[question_type - 1]

    path = os.path.join(DATABASES_PATH, db_id, 'embeddings', hdf5_file)
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

def delete_all_content_hdf5(db_id: str, hdf5_file='embeddings.h5'):
    types = ['mcqs', 'oeqs', 'tfqs']
    
    path = os.path.join(DATABASES_PATH, db_id, 'embeddings', hdf5_file)
    for question_type in range(1, len(types) + 1):
        delete_content_hdf5(question_type, db_id, path)

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

def add_question_marks(text: str) -> str:
    if text[0] not in ['V', '¿']:
        text = '¿' + text[:-1] + '?'
        
    return text

def load_documents(file_location: str):
    loaded_documents = chroma_utils.load_documents(file_location)
    return loaded_documents
