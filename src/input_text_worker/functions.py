from pathlib import Path


def read_file(file_name: str) -> str:
    base_path = Path(__file__).absolute().parent.parent.parent / 'text_examples'
    with open(str(base_path / file_name), "r", encoding="utf-8") as file:
        return file.read()
