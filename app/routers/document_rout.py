from fastapi import APIRouter, HTTPException
from schemas.models import document_schema
from database.db import get_connection
from fastapi import Depends
from utils.auth import  get_current_user
from logging_config import logger

router = APIRouter(
    prefix = "/documents",
    tags= ["Documents available"]
)

#Documents = []


@router.get("/")
def get_documents(current_user= Depends(get_current_user)):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
        
            # Insert a document chunk
    sql = """
            select * from documents where uploaded_by = %s
            """
        
    
        
    cursor.execute(sql,(current_user["user_id"],))
    documents = cursor.fetchall()
    cursor.close()
    conn.commit()
    if not documents :
        logger.warning(
                            "Document not found for user id : %s ",current_user["user_id"])

    return documents

@router.delete("/{document_id}")
def delete_document(
    document_id: int,
    current_user=Depends(get_current_user)
):
    conn = get_connection()
    cursor = conn.cursor()

    # Check if document exists and belongs to current user
    check_sql = """
        SELECT id
        FROM documents
        WHERE id = %s AND uploaded_by = %s
    """

    cursor.execute(
        check_sql,
        (document_id, current_user["user_id"])
    )

    document = cursor.fetchone()

    if not document:
        cursor.close()
        conn.close()
        logger.warning(
            "Document not found. Document ID: %s, User ID: %s",
            document_id,
            current_user["user_id"]
        )
        raise HTTPException(
            status_code=404,
            detail="Document not found"
        )

    # Delete document
    delete_sql = """
        DELETE FROM documents
        WHERE id = %s AND uploaded_by = %s
    """

    cursor.execute(
        delete_sql,
        (document_id, current_user["user_id"])
    )

    conn.commit()

    cursor.close()
    conn.close()

    logger.info(
        "Document deleted successfully. Document ID: %s, User ID: %s",
        document_id,
        current_user["user_id"]
    )

    return {
        "message": "Document deleted successfully",
        "document_id": document_id
    }