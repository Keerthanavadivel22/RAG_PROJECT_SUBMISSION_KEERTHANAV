
import os
import pymupdf

from docx import Document


def extract_document_text(file_path: str):

    extension = os.path.splitext(file_path)[1].lower()

    # PDF extraction

    if extension == ".pdf":

        text_content = []

        with pymupdf.open(file_path) as pdf:

            for page in pdf:

                page_text = page.get_text("text")

                if isinstance(page_text, str):

                    text_content.append(page_text)

        return "\n".join(text_content).strip()

    # Word extraction

    elif extension == ".docx":

        doc = Document(file_path)

        text = "\n".join(
            paragraph.text
            for paragraph in doc.paragraphs
        )

        # Extract table content too

        for table in doc.tables:

            for row in table.rows:

                text += "\n" + " | ".join(
                    cell.text for cell in row.cells
                )

        return text.strip()

    # Text file extraction

    elif extension == ".txt":

        with open(
            file_path,
            "r",
            encoding="utf-8-sig"
        ) as file:

            return file.read().strip()

    else:

        raise ValueError("Unsupported file format")
