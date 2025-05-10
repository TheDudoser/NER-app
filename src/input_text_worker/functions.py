import json
import hashlib


def get_json_hash(data):
    # Сортируем ключи для детерминированности
    json_str = json.dumps(data, sort_keys=True, ensure_ascii=False)
    return hashlib.md5(json_str.encode('utf-8')).hexdigest()
