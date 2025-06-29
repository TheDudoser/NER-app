import re

with open("text_examples/pdd.txt") as f:
    text = f.read()
phrase = "транспортное средство"

# Разбиваем текст на предложения (упрощённо)
sentences = re.split(r'(?<=[.!?])\s+', text)

# Ищем предложения с фразой
matches = [s for s in sentences if re.search(rf'\b{re.escape(phrase)}\b', s, flags=re.IGNORECASE)]

print(len(matches))
