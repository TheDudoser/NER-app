import os
import torch
from transformers import AutoModelForTokenClassification, AutoTokenizer, pipeline


class NERModel:
    def __init__(self, model_name="Davlan/bert-base-multilingual-cased-ner-hrl", cache_dir=".cache/ner_model"):
        self.model_name = model_name
        self.cache_dir = cache_dir
        self.pipeline = None

    def load(self):
        """Загрузка модели с кэшированием на диск"""
        try:
            os.makedirs(self.cache_dir, exist_ok=True)

            if self.is_model_cached():
                model, tokenizer = self._load_cached_model()
            else:
                model, tokenizer = self._download_and_cache_model()

            self.pipeline = pipeline(
                "ner",
                model=model,
                aggregation_strategy="simple",
                tokenizer=tokenizer,
                device=0 if torch.cuda.is_available() else -1
            )
            return True
        except Exception as e:
            print(f"Ошибка загрузки модели: {e}")
            return False

    def is_model_cached(self):
        return os.path.exists(os.path.join(self.cache_dir, "config.json"))

    def _load_cached_model(self):
        print("🔄 Загрузка модели из локального кэша...")
        return (
            AutoModelForTokenClassification.from_pretrained(self.cache_dir),
            AutoTokenizer.from_pretrained(self.cache_dir)
        )

    def _download_and_cache_model(self):
        print("🌐 Скачивание модели из интернета...")
        model = AutoModelForTokenClassification.from_pretrained(self.model_name)
        tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        model.save_pretrained(self.cache_dir)
        tokenizer.save_pretrained(self.cache_dir)
        return model, tokenizer

    def is_predict(self):
        return self.pipeline

    def predict(self, text):
        """Возвращает предсказанные сущности для текста"""
        return self.pipeline(text) if self.pipeline else []
