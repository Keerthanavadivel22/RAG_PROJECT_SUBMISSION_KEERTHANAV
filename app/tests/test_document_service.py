
import pytest
import pymupdf
from docx import Document

from services.document_service import extract_document_text


# 1. TXT extraction
def test_extract_txt(tmp_path):

    file_path = tmp_path / "sample.txt"

    file_path.write_text(
        "Python is a programming language.",
        encoding="utf-8"
    )

    result = extract_document_text(str(file_path))

    assert result == "Python is a programming language."


# 2. DOCX extraction
def test_extract_docx(tmp_path):

    file_path = tmp_path / "sample.docx"

    doc = Document()

    doc.add_paragraph("This is a DOCX document.")

    table = doc.add_table(rows=1, cols=2)

    table.rows[0].cells[0].text = "Name"
    table.rows[0].cells[1].text = "Keerthana"

    doc.save(file_path)

    result = extract_document_text(str(file_path))

    assert "This is a DOCX document." in result
    assert "Name | Keerthana" in result


# 3. PDF extraction
def test_extract_pdf(tmp_path):

    file_path = tmp_path / "sample.pdf"

    pdf = pymupdf.open()

    page = pdf.new_page()

    page.insert_text(
        (50, 50),
        "This is a PDF document."
    )

    pdf.save(file_path)
    pdf.close()

    result = extract_document_text(str(file_path))

    assert "This is a PDF document." in result


# 4. Unsupported format
def test_unsupported_file(tmp_path):

    file_path = tmp_path / "sample.xlsx"

    file_path.write_text("Sample content")

    with pytest.raises(ValueError):
        extract_document_text(str(file_path))


# 5. Empty TXT file
def test_empty_txt(tmp_path):

    file_path = tmp_path / "empty.txt"

    file_path.write_text("", encoding="utf-8")

    result = extract_document_text(str(file_path))

    assert result == ""
