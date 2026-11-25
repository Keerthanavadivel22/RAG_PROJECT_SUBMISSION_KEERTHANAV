import os
import uuid
import logging

from fastapi import (
    APIRouter,
    UploadFile,
    File,
    Depends,
    HTTPException
)

from database.db import get_connection
from utils.auth import get_current_user

from services.document_service import extract_document_text
from services.chunk_service import create_chunks

from services.pinecone_service import (
    store_chunks,
    delete_document_vectors
)


# --------------------------------------------------
# LOGGING
# --------------------------------------------------

from logging_config import logger

# --------------------------------------------------
# ROUTER CONFIGURATION
# --------------------------------------------------

router = APIRouter(
    prefix="/upload",
    tags=["Document Uploading"]
)


UPLOAD_DIR = "uploads"

MAX_FILE_SIZE = 20 * 1024 * 1024

ALLOWED_EXTENSIONS = {
    ".pdf",
    ".docx",
    ".txt"
}


# --------------------------------------------------
# DOCUMENT UPLOAD ENDPOINT
# --------------------------------------------------

@router.post("/document")
def upload_document(

    file: UploadFile = File(...),

    current_user=Depends(get_current_user)

):

    conn = None
    file_path = None
    document_id = None

    vectors_attempted = False
    success = False

    user_id = current_user["user_id"]

    try:

        # ------------------------------------------
        # 1. VALIDATE FILE NAME AND EXTENSION
        # ------------------------------------------

        if not file.filename:

            raise HTTPException(
                status_code=400,
                detail="File name is required"
            )

        original_name = os.path.basename(file.filename)

        extension = os.path.splitext(original_name)[1].lower()

        if extension not in ALLOWED_EXTENSIONS:

            raise HTTPException(
                status_code=400,
                detail="Only PDF, DOCX and TXT files are allowed"
            )

        logger.info(
            "File validation started. User ID: %s, File: %s",
            user_id,
            original_name
        )

        # ------------------------------------------
        # 2. VALIDATE FILE SIZE
        # ------------------------------------------

        file_content = file.file.read(MAX_FILE_SIZE + 1)

        if len(file_content) > MAX_FILE_SIZE:

            raise HTTPException(
                status_code=413,
                detail="File size must not exceed 20 MB"
            )

        if not file_content:

            raise HTTPException(
                status_code=400,
                detail="Uploaded file is empty"
            )

        # ------------------------------------------
        # 3. VALIDATE FILE CONTENT
        # ------------------------------------------

        if extension == ".pdf":

            if not file_content.startswith(b"%PDF"):

                raise HTTPException(
                    status_code=400,
                    detail="Invalid PDF file"
                )

        elif extension == ".docx":

            if not file_content.startswith(b"PK"):

                raise HTTPException(
                    status_code=400,
                    detail="Invalid DOCX file"
                )

        elif extension == ".txt":

            if b"\x00" in file_content:

                raise HTTPException(
                    status_code=400,
                    detail="Invalid text file"
                )

            try:

                file_content.decode("utf-8-sig")

            except UnicodeDecodeError:

                raise HTTPException(
                    status_code=400,
                    detail="Text file must use UTF-8 encoding"
                )

        logger.info(
            "File validation successful. File: %s",
            original_name
        )

        # ------------------------------------------
        # 4. SAVE DOCUMENT
        # ------------------------------------------

        os.makedirs(
            UPLOAD_DIR,
            exist_ok=True
        )

        unique_name = f"{uuid.uuid4()}{extension}"

        file_path = os.path.join(
            UPLOAD_DIR,
            unique_name
        )

        with open(file_path, "wb") as f:

            f.write(file_content)

        logger.info(
            "File saved successfully. Path: %s",
            file_path
        )

        # ------------------------------------------
        # 5. EXTRACT DOCUMENT TEXT
        # ------------------------------------------

        try:

            text = extract_document_text(file_path)

            if not isinstance(text, str):
                raise ValueError("Extractor did not return text")

        except Exception:

            logger.exception(
                "Document extraction failed. File: %s",
                original_name
            )

            raise HTTPException(
                status_code=400,
                detail="Unable to extract text from document"
            )

        if not text.strip():

            raise HTTPException(
                status_code=400,
                detail="No readable text found"
            )

        logger.info(
            "Text extracted successfully. Characters: %s",
            len(text)
        )

        # ------------------------------------------
        # 6. CREATE CHUNKS
        # ------------------------------------------

        chunks = create_chunks(text)

        if not chunks:

            raise HTTPException(
                status_code=400,
                detail="No chunks generated"
            )

        logger.info(
            "Chunking completed. Total chunks: %s",
            len(chunks)
        )

        # ------------------------------------------
        # 7. CONNECT MYSQL
        # ------------------------------------------

        try:

            conn = get_connection()

            if conn is None:
                raise RuntimeError("Database connection returned None")

            logger.info(
                "MySQL connected successfully. User ID: %s",
                user_id
            )

        except Exception:

            logger.exception(
                "MySQL connection failed. User ID: %s",
                user_id
            )

            raise HTTPException(
                status_code=503,
                detail="Database service is unavailable"
            )

        # ------------------------------------------
        # 8. INSERT DOCUMENT AND CHUNKS INTO MYSQL
        # ------------------------------------------

        with conn.cursor() as cursor:

            cursor.execute(

                """
                INSERT INTO documents
                (file_name, file_path, uploaded_by)
                VALUES (%s, %s, %s)
                """,

                (
                    original_name,
                    file_path,
                    user_id
                )

            )

            document_id = cursor.lastrowid

            chunk_ids = []

            for idx, chunk in enumerate(chunks):

                cursor.execute(

                    """
                    INSERT INTO chunks
                    (document_id, chunk_text, chunk_index)
                    VALUES (%s, %s, %s)
                    """,

                    (
                        document_id,
                        chunk,
                        idx
                    )

                )

                chunk_ids.append(cursor.lastrowid)

        logger.info(
            "Document and chunks inserted into MySQL. "
            "Document ID: %s",
            document_id
        )

        # ------------------------------------------
        # 9. STORE VECTORS IN PINECONE
        # ------------------------------------------

        vectors_attempted = True

        total_vectors = store_chunks(

            user_id=user_id,

            document_id=document_id,

            file_name=original_name,

            chunks=chunks,

            chunk_ids=chunk_ids

        )

        if total_vectors != len(chunks):

            raise RuntimeError(
                "Pinecone vector count does not match chunk count"
            )

        logger.info(
            "Pinecone storage completed. "
            "Document ID: %s, Vectors: %s",
            document_id,
            total_vectors
        )

        # ------------------------------------------
        # 10. COMMIT MYSQL TRANSACTION
        # ------------------------------------------

        conn.commit()

        success = True

        logger.info(
            "Document upload completed successfully. "
            "User ID: %s, Document ID: %s",
            user_id,
            document_id
        )

        # ------------------------------------------
        # 11. RETURN RESPONSE
        # ------------------------------------------

        return {

            "message": "Document uploaded successfully",

            "document_id": document_id,

            "file_name": original_name,

            "file_type": extension,

            "total_chunks": len(chunks),

            "vectors_stored": total_vectors,

            "namespace": f"user_{user_id}"

        }

    # ----------------------------------------------
    # 12. HTTP EXCEPTION HANDLING
    # ----------------------------------------------

    except HTTPException:

        if conn:

            try:
                conn.rollback()

            except Exception:
                logger.exception("MySQL rollback failed")

        raise

    # ----------------------------------------------
    # 13. UNEXPECTED ERROR HANDLING
    # ----------------------------------------------

    except Exception:

        if conn:

            try:
                conn.rollback()

            except Exception:
                logger.exception("MySQL rollback failed")

        logger.exception(
            "Document upload failed. User ID: %s",
            user_id
        )

        raise HTTPException(
            status_code=500,
            detail="Document upload failed"
        )

    # ----------------------------------------------
    # 14. CLEANUP
    # ----------------------------------------------

    finally:

        # Cleanup Pinecone vectors after failure

        if not success and document_id and vectors_attempted:

            try:

                delete_document_vectors(
                    user_id,
                    document_id
                )

                logger.info(
                    "Pinecone vectors deleted. Document ID: %s",
                    document_id
                )

            except Exception:

                logger.exception(
                    "Pinecone cleanup failed. Document ID: %s",
                    document_id
                )

        # Remove local file after failure

        if not success and file_path and os.path.exists(file_path):

            try:

                os.remove(file_path)

                logger.info(
                    "Temporary uploaded file removed: %s",
                    file_path
                )

            except OSError:

                logger.exception(
                    "File cleanup failed: %s",
                    file_path
                )

        # Close MySQL connection

        if conn:

            try:

                conn.close()

            except Exception:

                logger.exception(
                    "MySQL connection closing failed"
                )

        # Close uploaded file

        try:

            file.file.close()

        except Exception:

            logger.exception(
                "Uploaded file closing failed"
            )
