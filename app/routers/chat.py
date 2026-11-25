
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, field_validator
from typing import Optional

# --------------------------------------------------
# IMPORTS
# Adjust these import paths if your project
# stores these functions in different modules.
# --------------------------------------------------

from database.db import get_connection
from utils.auth import get_current_user

from services.pinecone_service import search_chunks
from services.llm_service import generate_answer
from logging_config import logger


router = APIRouter(
    prefix="/chat",
    tags=["Chat"]
)


# --------------------------------------------------
# REQUEST MODEL
# --------------------------------------------------

class ChatRequest(BaseModel):

    question: str = Field(
        min_length=1,
        max_length=4000
    )

    chat_id: Optional[int] = None

    @field_validator("question")
    @classmethod
    def validate_question(cls, value):

        value = value.strip()

        if not value:
            raise ValueError("Question cannot be empty")

        return value


# --------------------------------------------------
# HELPER: GET USER ID
# --------------------------------------------------

def get_user_id(current_user):

    if isinstance(current_user, dict):
        user_id = current_user.get("user_id", current_user.get("id"))
    else:
        user_id = getattr(
            current_user,
            "user_id",
            getattr(current_user, "id", None)
        )

    if user_id is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid user information"
        )

    return user_id


# --------------------------------------------------
# HELPER: CHECK DOCUMENT OWNERSHIP
# --------------------------------------------------

def check_document_access(cursor, document_id, user_id):

    cursor.execute(
        """
        SELECT document_id, file_name
        FROM documents
        WHERE document_id = %s
        AND uploaded_by = %s
        """,
        (document_id, user_id)
    )

    document = cursor.fetchone()

    if not document:
        raise HTTPException(
            status_code=404,
            detail="Document not found or access denied"
        )

    return document


# --------------------------------------------------
# 1. CREATE NEW CHAT SESSION
# POST /chat/{document_id}/sessions
# --------------------------------------------------

@router.post("/{document_id}/sessions")
def create_chat_session(
    document_id: int,
    current_user=Depends(get_current_user)
):

    user_id = get_user_id(current_user)
    logger.info("Chat API request started | user_id=%s", user_id)

    connection = get_connection()

    if connection is None:
        logger.error("Database connection failed in chat API | user_id=%s", user_id)
        raise HTTPException(
            status_code=500,
            detail="Database connection failed"
        )

    cursor = None

    try:

        cursor = connection.cursor(dictionary=True)

        logger.info("Creating chat session | user_id=%s | document_id=%s", user_id, document_id)

        # Verify document ownership
        document = check_document_access(
            cursor,
            document_id,
            user_id
        )

        # Create chat session
        cursor.execute(
            """
            INSERT INTO chat_sessions
            (user_id, document_id, title)
            VALUES (%s, %s, %s)
            """,
            (user_id, document_id, "New Chat")
        )

        chat_id = cursor.lastrowid

        connection.commit()
        logger.info("Chat session created | chat_id=%s | user_id=%s | document_id=%s", chat_id, user_id, document_id)

        return {
            "message": "Chat session created successfully",
            "chat_id": chat_id,
            "document_id": document_id,
            "document_name": document["file_name"], # type: ignore
            "title": "New Chat"
        }

    except HTTPException as e:
        connection.rollback()
        logger.warning("Chat API rejected request | user_id=%s | status_code=%s | detail=%s", user_id, e.status_code, e.detail)
        raise

    except Exception as e:
        connection.rollback()
        logger.exception("Unexpected error in chat API | user_id=%s", user_id)

        raise HTTPException(
            status_code=500,
            detail=f"Failed to create chat session: {str(e)}"
        )

    finally:

        if cursor:
            cursor.close()

        connection.close()


# --------------------------------------------------
# 2. GET ALL CHAT SESSIONS
# GET /chat/sessions
# --------------------------------------------------

@router.get("/sessions")
def get_all_chat_sessions(
    current_user=Depends(get_current_user)
):

    user_id = get_user_id(current_user)
    logger.info("Chat API request started | user_id=%s", user_id)

    connection = get_connection()

    if connection is None:
        logger.error("Database connection failed in chat API | user_id=%s", user_id)
        raise HTTPException(
            status_code=500,
            detail="Database connection failed"
        )

    cursor = None

    try:

        cursor = connection.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT
                cs.chat_id,
                cs.document_id,
                cs.title,
                cs.created_at,
                cs.updated_at,
                d.file_name
            FROM chat_sessions cs

            INNER JOIN documents d
                ON cs.document_id = d.document_id

            INNER JOIN chat_messages cm
                ON cs.chat_id = cm.chat_id

            WHERE cs.user_id = %s

            GROUP BY
                cs.chat_id,
                cs.document_id,
                cs.title,
                cs.created_at,
                cs.updated_at,
                d.file_name

            ORDER BY
                cs.updated_at DESC,
                cs.chat_id DESC
            """,
            (user_id,)
        )

        sessions = cursor.fetchall()
        logger.info("Chat sessions fetched | user_id=%s | count=%s", user_id, len(sessions))

        return {
            "sessions": sessions
        }

    except Exception as e:
        logger.exception("Unexpected error in chat API | user_id=%s", user_id)

        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch chat sessions: {str(e)}"
        )

    finally:

        if cursor:
            cursor.close()

        connection.close()


# --------------------------------------------------
# 3. GET MESSAGES FROM A CHAT SESSION
# GET /chat/sessions/{chat_id}/messages
# --------------------------------------------------

@router.get("/sessions/{chat_id}/messages")
def get_chat_messages(
    chat_id: int,
    current_user=Depends(get_current_user)
):

    user_id = get_user_id(current_user)
    logger.info("Chat API request started | user_id=%s", user_id)

    connection = get_connection()

    if connection is None:
        logger.error("Database connection failed in chat API | user_id=%s", user_id)
        raise HTTPException(
            status_code=500,
            detail="Database connection failed"
        )

    cursor = None

    try:

        cursor = connection.cursor(dictionary=True)

        # Verify session ownership
        cursor.execute(
            """
            SELECT chat_id
            FROM chat_sessions
            WHERE chat_id = %s
            AND user_id = %s
            """,
            (chat_id, user_id)
        )

        session = cursor.fetchone()

        if not session:
            raise HTTPException(
                status_code=404,
                detail="Chat session not found"
            )

        # Fetch messages
        cursor.execute(
            """
            SELECT
                message_id,
                chat_id,
                role,
                content,
                created_at
            FROM chat_messages
            WHERE chat_id = %s
            AND user_id = %s
            ORDER BY created_at ASC, message_id ASC
            """,
            (chat_id, user_id)
        )

        messages = cursor.fetchall()
        logger.info("Chat messages fetched | user_id=%s | chat_id=%s | count=%s", user_id, chat_id, len(messages))

        return {
            "chat_id": chat_id,
            "messages": messages
        }

    except HTTPException as e:
        logger.warning("Chat API rejected request | user_id=%s | chat_id=%s | status_code=%s | detail=%s", user_id, chat_id, e.status_code, e.detail)
        raise

    except Exception as e:
        logger.exception("Unexpected error in chat API | user_id=%s", user_id)

        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch messages: {str(e)}"
        )

    finally:

        if cursor:
            cursor.close()

        connection.close()


# --------------------------------------------------
# 4. ASK QUESTION USING RAG
# POST /chat/{document_id}
# --------------------------------------------------

@router.post("/{document_id}")
def chat_with_document(
    document_id: int,
    request: ChatRequest,
    current_user=Depends(get_current_user)
):

    user_id = get_user_id(current_user)
    logger.info("Chat API request started | user_id=%s", user_id)

    connection = get_connection()

    if connection is None:
        logger.error("Database connection failed in chat API | user_id=%s", user_id)
        raise HTTPException(
            status_code=500,
            detail="Database connection failed"
        )

    cursor = None

    try:

        cursor = connection.cursor(dictionary=True)

        # ------------------------------------------
        # STEP 1: VERIFY DOCUMENT
        # ------------------------------------------

        document = check_document_access(
            cursor,
            document_id,
            user_id
        )

        # ------------------------------------------
        # STEP 2: CREATE OR VERIFY CHAT SESSION
        # ------------------------------------------

        if request.chat_id is None:

            cursor.execute(
                """
                INSERT INTO chat_sessions
                (user_id, document_id, title)
                VALUES (%s, %s, %s)
                """,
                (user_id, document_id, "New Chat")
            )

            chat_id = cursor.lastrowid

            connection.commit()

        else:

            cursor.execute(
                """
                SELECT chat_id
                FROM chat_sessions
                WHERE chat_id = %s
                AND user_id = %s
                AND document_id = %s
                """,
                (
                    request.chat_id,
                    user_id,
                    document_id
                )
            )

            session = cursor.fetchone()

            if not session:
                raise HTTPException(
                    status_code=404,
                    detail="Chat session not found"
                )

            chat_id = request.chat_id

        # ------------------------------------------
        # STEP 3: GET PREVIOUS CONVERSATION HISTORY
        # ------------------------------------------

        cursor.execute(
            """
            SELECT role, content
            FROM chat_messages
            WHERE chat_id = %s
            AND user_id = %s
            ORDER BY created_at DESC, message_id DESC
            LIMIT 8
            """,
            (chat_id, user_id)
        )

        history = cursor.fetchall()

        # Reverse to get chronological order
        history.reverse()

        # ------------------------------------------
        # STEP 4: SAVE USER QUESTION
        # ------------------------------------------

        cursor.execute(
            """
            INSERT INTO chat_messages
            (chat_id, user_id, document_id, role, content)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (
                chat_id,
                user_id,
                document_id,
                "user",
                request.question
            )
        )

        # ------------------------------------------
        # STEP 5: RETRIEVE RELEVANT PDF CHUNKS
        # ------------------------------------------

        logger.info("Retrieving document chunks | user_id=%s | document_id=%s | chat_id=%s", user_id, document_id, chat_id)
        retrieved_chunks = search_chunks(
            user_id,
            document_id,
            request.question,
            top_k=5
        )

        if not retrieved_chunks:
            context = "No relevant information was found in the uploaded document."
        else:
            context = "\n\n".join(
                chunk["text"]
                for chunk in retrieved_chunks
                if chunk.get("text")
            )

        # ------------------------------------------
        # STEP 6: GENERATE ANSWER USING OLLAMA
        # ------------------------------------------

        logger.info("Generating answer | user_id=%s | document_id=%s | chat_id=%s | retrieved_chunks=%s", user_id, document_id, chat_id, len(retrieved_chunks))
        answer = generate_answer(
            request.question,
            context,
            history=history[-4:]
        )

        if not answer:
            answer = "Sorry, I could not generate an answer."

        # ------------------------------------------
        # STEP 7: SAVE ASSISTANT ANSWER
        # ------------------------------------------

        cursor.execute(
            """
            INSERT INTO chat_messages
            (chat_id, user_id, document_id, role, content)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (
                chat_id,
                user_id,
                document_id,
                "assistant",
                answer
            )
        )

        # ------------------------------------------
        # STEP 8: UPDATE CHAT TITLE
        # ------------------------------------------

        cursor.execute(
            """
            UPDATE chat_sessions
            SET
                title = CASE
                    WHEN title = 'New Chat'
                    THEN %s
                    ELSE title
                END,
                updated_at = CURRENT_TIMESTAMP
            WHERE chat_id = %s
            AND user_id = %s
            """,
            (
                request.question[:60],
                chat_id,
                user_id
            )
        )

        connection.commit()
        logger.info("Chat response saved | user_id=%s | document_id=%s | chat_id=%s", user_id, document_id, chat_id)

        # ------------------------------------------
        # STEP 9: RETURN RESPONSE
        # ------------------------------------------

        return {
            "message": "Answer generated successfully",
            "chat_id": chat_id,
            "document_id": document_id,
            "document_name": document["file_name"], # type: ignore
            "question": request.question,
            "answer": answer
        }

    except HTTPException as e:
        connection.rollback()
        logger.warning("Chat API rejected request | user_id=%s | status_code=%s | detail=%s", user_id, e.status_code, e.detail)
        raise

    except Exception as e:

        connection.rollback()

        raise HTTPException(
            status_code=500,
            detail=f"Chat failed: {str(e)}"
        )

    finally:

        if cursor:
            cursor.close()

        connection.close()


# --------------------------------------------------
# 5. DELETE CHAT SESSION
# DELETE /chat/sessions/{chat_id}
# --------------------------------------------------

@router.delete("/sessions/{chat_id}")
def delete_chat_session(
    chat_id: int,
    current_user=Depends(get_current_user)
):

    user_id = get_user_id(current_user)
    logger.info("Chat API request started | user_id=%s", user_id)

    connection = get_connection()

    if connection is None:
        logger.error("Database connection failed in chat API | user_id=%s", user_id)
        raise HTTPException(
            status_code=500,
            detail="Database connection failed"
        )

    cursor = None

    try:

        cursor = connection.cursor(dictionary=True)

        # Verify ownership
        cursor.execute(
            """
            SELECT chat_id
            FROM chat_sessions
            WHERE chat_id = %s
            AND user_id = %s
            """,
            (chat_id, user_id)
        )

        session = cursor.fetchone()

        if not session:
            raise HTTPException(
                status_code=404,
                detail="Chat session not found"
            )

        # Delete session
        cursor.execute(
            """
            DELETE FROM chat_sessions
            WHERE chat_id = %s
            AND user_id = %s
            """,
            (chat_id, user_id)
        )

        connection.commit()
        logger.info("Chat session deleted | user_id=%s | chat_id=%s", user_id, chat_id)

        return {
            "message": "Chat session deleted successfully",
            "chat_id": chat_id
        }

    except HTTPException as e:
        connection.rollback()
        logger.warning("Chat API rejected request | user_id=%s | status_code=%s | detail=%s", user_id, e.status_code, e.detail)
        raise

    except Exception as e:

        connection.rollback()

        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete chat session: {str(e)}"
        )

    finally:

        if cursor:
            cursor.close()

        connection.close()
