import json
import hashlib
import os


class TextService:
    @staticmethod
    def get_json_hash(data):
        # Сортируем ключи для детерминированности
        json_str = json.dumps(data, sort_keys=True, ensure_ascii=False)
        return hashlib.md5(json_str.encode('utf-8')).hexdigest()

    @staticmethod
    def get_text_content_hash(data):
        return hashlib.md5(data.encode('utf-8')).hexdigest()

    @staticmethod
    async def save_json_file_by_request(request, file_path):
        data = await request.json()

        if not os.path.exists(file_path):
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

    @staticmethod
    def get_content_file(file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
