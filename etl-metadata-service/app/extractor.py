import fitz


def extract_text_from_pdf(file_path: str):
    text = ""

    with fitz.open(file_path) as document:
        total_pages = document.page_count

        for page in document:
            text += page.get_text("text") + "\n"

    return text, total_pages