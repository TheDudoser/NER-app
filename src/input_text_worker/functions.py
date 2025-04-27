import json
from pathlib import Path
import hashlib


def read_file_text_examples(file_name: str) -> str:
    base_path = Path(__file__).absolute().parent.parent.parent / 'text_examples'
    with open(str(base_path / file_name), "r", encoding="utf-8") as file:
        return file.read()


def get_json_hash(data):
    # Сортируем ключи для детерминированности
    json_str = json.dumps(data, sort_keys=True, ensure_ascii=False)
    return hashlib.md5(json_str.encode('utf-8')).hexdigest()
