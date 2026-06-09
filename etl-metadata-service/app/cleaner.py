import re


def clean_text(text: str):
    text = text.replace("\x00", " ")

    # eliminar espacios repetidos
    text = re.sub(r"[ \t]+", " ", text)

    # eliminar más de 2 saltos de línea consecutivos
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()