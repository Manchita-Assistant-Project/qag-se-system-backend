import json

JSON_PATH = "app/generator/q&as/qs.json"

def load_json(path: str):
    with open(path, 'r') as f:
        content = json.load(f)

    return content['content']

def update_json(path: str, data: list):
    with open(path, 'r') as f:
        json_dict = json.load(f)

    parsed_data = [json.loads(item) for item in data]

    json_dict.update({"content": parsed_data})

    with open(path, 'w') as f:
        json.dump(json_dict, f, ensure_ascii=False, indent=4)
