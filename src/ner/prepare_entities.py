import io
import sys

from ipymarkup import show_span_ascii_markup


def prepare_entities(entities, text):
    # Вывод сущностей в консоль (для отладки)
    for entity in entities:
        print(
            f"Сущность: {entity['word']:20} → Тип: {entity['entity_group']:15} (Точность: {entity['score']:.4f})")

    # Подготовка spans для ipymarkup
    spans = [(ent['start'], ent['end'], ent['entity_group']) for ent in entities]

    # Перехватываем вывод show_span_ascii_markup
    output = io.StringIO()
    old_stdout = sys.stdout
    sys.stdout = output  # Перенаправляем stdout

    # Генерируем ASCII-разметку
    show_span_ascii_markup(text, spans)

    sys.stdout = old_stdout  # Возвращаем stdout
    marked_text = output.getvalue()

    # Проверяем, что marked_text не пустой
    print()
    print("DEBUG - Marked Text:", repr(marked_text))  # Для отладки

    return marked_text
