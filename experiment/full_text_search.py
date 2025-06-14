import re
import time

with open("text_examples/redhead.txt") as f:
    text = f.read()
phrases = ["красный шапочка", "красная шапочка", "бабушка"]

# Запускаем поиск и измеряем время
start = time.time()
true_phrases = [phrase for phrase in phrases if re.search(re.escape(phrase), text, re.IGNORECASE)]
end = time.time()
search_time = end - start

TP = len(true_phrases)  # Например, 2
FP = 0  # Ищем только из списка, FP = 0
FN = len(phrases) - TP  # Например, 3 - 2 = 1

precision = TP / (TP + FP) if (TP + FP) > 0 else 0
recall = TP / (TP + FN) if (TP + FN) > 0 else 0
f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0

print(f"Time: {search_time}")
print(f"Precision: {precision}")
print(f"Recall: {recall}")
print(f"F1: {f1}")
