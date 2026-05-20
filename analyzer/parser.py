# analyzer/parser.py
# Extracts plain text from PDF, DOCX, or TXT files

import fitz          # PyMuPDF
import docx
import io


def extract_text(file_storage) -> str:
    """
    Accept a Flask FileStorage object.
    Returns extracted plain text string.
    """
    filename = file_storage.filename.lower()
    file_bytes = file_storage.read()

    if filename.endswith('.pdf'):
        return _extract_pdf(file_bytes)
    elif filename.endswith('.docx'):
        return _extract_docx(file_bytes)
    elif filename.endswith('.txt'):
        return file_bytes.decode('utf-8', errors='ignore')
    else:
        raise ValueError(f"Unsupported file type: {filename}")


def _extract_pdf(file_bytes: bytes) -> str:
    text_parts = []
    with fitz.open(stream=file_bytes, filetype='pdf') as doc:
        for page in doc:
            text_parts.append(page.get_text())
    return '\n'.join(text_parts)


def _extract_docx(file_bytes: bytes) -> str:
    doc = docx.Document(io.BytesIO(file_bytes))
    return '\n'.join(para.text for para in doc.paragraphs if para.text.strip())