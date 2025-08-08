import io

def extract_doc_content(file_bytes: bytes, extension: str) -> str:
    """
    Extracts the content of the provided document and returns it as a string

    Args:
        file_bytes: bytes -> File bytes
        extension: str -> Extension of the file which we are extracting the content
    Returns:
        str -> Extracted content
    """
    content = ""

    if extension == ".txt":
        content = file_bytes.decode("utf-8")

    elif extension == ".pdf":
        from PyPDF2 import PdfReader

        pdf = PdfReader(io.BytesIO(file_bytes))
        content = "\n".join(page.extract_text() for page in pdf.pages if page.extract_text())

    elif extension == ".docx":
        import docx

        doc = docx.Document(io.BytesIO(file_bytes))
        content =  "\n".join([para.text for para in doc.paragraphs])

    elif extension == ".csv":
        import csv

        text_lines = file_bytes.decode("utf-8").splitlines()
        reader = csv.reader(text_lines)
        content = "\n".join([", ".join(row) for row in reader])

    return content