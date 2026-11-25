# 📄 PDF RAG Assistant – Document Question Answering System

## 1. Project Overview

The PDF RAG Assistant is a document-based question-answering application developed using **Python, FastAPI, Streamlit, MySQL, Sentence Transformers and Ollama**.

The application allows users to upload PDF and TXT documents and ask questions based on their content.

Instead of manually searching through lengthy documents, users can interact with their files through a chat interface. The application retrieves relevant text chunks from the uploaded documents and generates answers using a locally running Large Language Model.

One of the main objectives of this project is to build a RAG application without depending on external LLM or embedding APIs.
PDF_RAG_Project/
│
├── app/
│   ├── main.py
│   ├── stream_app.py
│   ├── routes/
│   ├── services/
│   ├── models/
│   └── database/
│
├── tests/
│   ├── conftest.py
│   ├── test_auth.py
│   ├── test_document_service.py
│   └── test_upload.py
│
├── evaluation/
│   └── PDF_RAG_Project_RAGAS_Evaluation.ipynb
│
├── .env
├── requirements.txt
└── README.md

### Key Features

- User registration and login.
- Password hashing using bcrypt.
- JWT-based authentication.
- PDF and TXT document uploads.
- Text extraction and chunking.
- Local embedding generation using Sentence Transformers.
- Embedding storage in MySQL.
- Cosine similarity-based document retrieval.
- Local LLM integration using Ollama.
- Context-based answer generation.
- Chat history management.
- Pytest-based backend testing.
- RAGAS-based answer evaluation.

---

## 2. Technologies Used

| Technology | Purpose |
|---|---|
| Python | Application development |
| FastAPI | Backend API |
| Streamlit | Frontend |
| MySQL | User, document, chunk and chat storage |
| Sentence Transformers | Local embedding generation |
| Ollama | Running the LLM locally |
| bcrypt | Password hashing |
| JWT | User authentication |
| Pytest | Backend testing |
| RAGAS | RAG evaluation |

---


## 3. System Architecture

The application follows a Retrieval-Augmented Generation architecture.

The complete workflow starts when a user uploads a document. The document is processed, divided into chunks, converted into embeddings and stored in MySQL.

When the user asks a question, the system generates an embedding for the question and compares it with the stored document embeddings using cosine similarity.

The most relevant chunks are passed to the local LLM through Ollama to generate an answer.

### Overall Architecture Flowchart

```text
                 USER
                   |
                   v
            STREAMLIT UI
                   |
                   v
             FASTAPI
                   |
          +--------+--------+
          |                 |
          v                 v
    AUTHENTICATION     DOCUMENT UPLOAD
          |                 |
          v                 v
       MYSQL          TEXT EXTRACTION
                            |
                            v
                         CHUNKING
                            |
                            v
                  SENTENCE TRANSFORMERS
                            |
                            v
                   EMBEDDING GENERATION
                            |
                            v
                          MYSQL
                    (Chunks + Vectors)
                            |
                            |
                    USER ASKS QUESTION
                            |
                            v
                   QUESTION EMBEDDING
                            |
                            v
                   COSINE SIMILARITY
                            |
                            v
                  TOP RELEVANT CHUNKS
                            |
                            v
                     LOCAL LLM
                       OLLAMA
                            |
                            v
                    GENERATED ANSWER
                            |
                            v
                      STREAMLIT UI
```

---

## 4. Authentication Workflow

Authentication ensures that only registered users can access protected application features.

The application uses bcrypt for password hashing and JWT for authentication.

### 4.1 Registration Process

When a new user registers, the application receives the user's details and validates the input.

The password is hashed using bcrypt before it is stored in the MySQL database. The original password is never stored as plain text.

```text
          USER REGISTRATION
                  |
                  v
           Enter User Details
                  |
                  v
          Validate User Input
                  |
                  v
          Hash Password (bcrypt)
                  |
                  v
          Store in MySQL Database
                  |
                  v
         Registration Successful
```

### 4.2 Login Process

During login, the user provides an email address and password.

The backend retrieves the corresponding user record from MySQL and verifies the entered password against the stored password hash using bcrypt.

If the credentials are valid, a JWT token is generated and returned to the user.

```text
              USER LOGIN
                  |
                  v
         Enter Email + Password
                  |
                  v
          Search User in MySQL
                  |
                  v
          Verify Password (bcrypt)
                  |
                  v
           Are Credentials Valid?
              /         \
            No           Yes
            |             |
            v             v
       Login Error     Generate JWT
                          |
                          v
                    Return JWT Token
                          |
                          v
                    Login Successful
```

### 4.3 JWT Authentication for Future Requests

The JWT token is used to authenticate subsequent protected requests.

```text
             USER REQUEST
                  |
                  v
             Send JWT Token
                  |
                  v
           FastAPI Authentication
                  |
                  v
             Verify JWT Token
                  |
             +----+----+
             |         |
           Valid     Invalid
             |         |
             v         v
        Grant Access  HTTP 401
```

---

## 5. Document Upload and Processing

The document upload module handles PDF and TXT files.

Once a user uploads a document, FastAPI validates the file and passes it to the document processing service.

The extracted text is divided into smaller chunks. Sentence Transformers then converts each chunk into a numerical vector representation.

The chunks and their corresponding embeddings are stored in MySQL.

### Document Processing Flowchart

```text
             USER UPLOADS FILE
                     |
                     v
                FASTAPI
                     |
                     v
               FILE VALIDATION
                     |
                     v
              PDF / TXT FILE?
                     |
                     v
               TEXT EXTRACTION
                     |
                     v
                 CHUNKING
                     |
                     v
          SENTENCE TRANSFORMERS
                     |
                     v
           GENERATE EMBEDDINGS
                     |
                     v
               STORE IN MYSQL
                     |
                     v
             DOCUMENT PROCESSED
```

### Processing Steps

1. **File Upload:** The user uploads a PDF or TXT document through Streamlit.
2. **Validation:** FastAPI checks the file type and content.
3. **Text Extraction:** Text is extracted from the uploaded document.
4. **Chunking:** The extracted text is divided into smaller sections.
5. **Embedding Generation:** Sentence Transformers converts each chunk into an embedding.
6. **Storage:** The document information, chunks and embeddings are stored in MySQL.

---

## 6. RAG Question Answering Workflow

This is the main functionality of the application.

When a user asks a question, the system searches the stored document embeddings to identify the most relevant chunks.

The question is converted into an embedding using the same embedding model used during document processing.

Cosine similarity is calculated between the question embedding and stored chunk embeddings.

The most relevant chunks are selected and provided to Ollama along with the user's question.

Ollama generates an answer using the retrieved context.

### RAG Architecture Flowchart

```text
             USER ASKS QUESTION
                     |
                     v
                FASTAPI
                     |
                     v
          GENERATE QUESTION EMBEDDING
                     |
                     v
              MYSQL EMBEDDINGS
                     |
                     v
             COSINE SIMILARITY
                     |
                     v
           RETRIEVE TOP RELEVANT
                  CHUNKS
                     |
                     v
             PREPARE CONTEXT
                     |
                     v
             USER QUESTION
                     |
                     v
                OLLAMA LLM
                     |
                     v
              GENERATE ANSWER
                     |
                     v
             STORE CHAT HISTORY
                     |
                     v
            RETURN ANSWER TO USER
```

### Retrieval Process

| Step | Description |
|---|---|
| Question Input | User submits a question |
| Embedding | Question is converted into a vector |
| Similarity Search | Compare question and document embeddings |
| Retrieval | Select the most relevant chunks |
| Context Preparation | Prepare retrieved chunks for the LLM |
| Generation | Ollama generates the response |
| Response | Display the answer to the user |

### Cosine Similarity

Cosine similarity measures how closely two vectors are related based on their direction.

The formula is:

Cosine Similarity = (A · B) / (||A|| × ||B||)

Where:

- A represents the question embedding.
- B represents a document chunk embedding.
- A · B represents the dot product.
- ||A|| and ||B|| represent vector magnitudes.

A higher similarity score indicates that the two embeddings are more closely related.

---

## 7. Database Design

MySQL is used to store application data.

The database manages user information, uploaded document details, extracted text chunks, embeddings and chat history.

### Main Database Tables

**1. users**

Stores registered user information.

| Column | Description |
|---|---|
| id | Unique user ID |
| username | User name |
| email | User email |
| password | Hashed password |

**2. documents**

Stores uploaded document details.

| Column | Description |
|---|---|
| id | Document ID |
| user_id | Owner of the document |
| filename | Uploaded file name |
| file_type | Document format |
| created_at | Upload timestamp |

**3. chunks**

Stores extracted document chunks and their embeddings.

| Column | Description |
|---|---|
| id | Chunk ID |
| document_id | Related document |
| chunk_text | Extracted text |
| embedding | Generated vector |

**4. chat_messages**

Stores user questions and generated answers.

| Column | Description |
|---|---|
| id | Message ID |
| user_id | User ID |
| document_id | Related document |
| question | User question |
| answer | Generated answer |
| created_at | Message timestamp |

*The column names are illustrative and should be aligned with the actual database schema.*

---

## 8. Complete Application Workflow

The following flowchart represents the complete application lifecycle, from user registration to answer generation.

```text
             1. USER REGISTERS
                     |
                     v
                USERS TABLE
                     |
                     v
               2. USER LOGS IN
                     |
                     v
                JWT CREATED
                     |
                     v
              3. UPLOAD DOCUMENT
                     |
                     v
              DOCUMENTS TABLE
                     |
                     v
             4. EXTRACT TEXT
                     |
                     v
              5. SPLIT INTO CHUNKS
                     |
                     v
                CHUNKS TABLE
                     |
                     v
           6. GENERATE EMBEDDINGS
                     |
                     v
              STORE IN MYSQL
                     |
                     v
           7. USER ASKS QUESTION
                     |
                     v
          GENERATE QUESTION EMBEDDING
                     |
                     v
             8. COSINE SIMILARITY
                     |
                     v
             RETRIEVE RELEVANT CHUNKS
                     |
                     v
              9. LOCAL LLM (OLLAMA)
                     |
                     v
              GENERATE ANSWER
                     |
                     v
            10. STORE CHAT HISTORY
                     |
                     v
              CHAT_MESSAGES TABLE
                     |
                     v
             11. RETURN ANSWER
                     |
                     v
                 STREAMLIT
```

---

## 9. Frontend Implementation

Streamlit is used to build the frontend.

The interface provides a simple way for users to interact with their documents.

The main functionalities include:

- User registration and login.
- Welcome message displaying the logged-in username.
- Document upload.
- Displaying uploaded document information.
- Asking questions about uploaded documents.
- Displaying generated answers.
- Viewing previous chat history.

The frontend communicates with FastAPI endpoints to perform these operations.

---

## 10. Backend API Structure

FastAPI handles the backend functionality through separate API routes.

The main API operations include:

| Module | Responsibility |
|---|---|
| Authentication | Registration, login and JWT verification |
| Document Upload | File validation and document upload |
| Document Service | Text extraction and chunking |
| Embedding Service | Local embedding generation |
| Retrieval Service | Cosine similarity search |
| Chat Service | Question answering and chat history |

---

## 11. Testing

Pytest is used to test the backend functionality.

The current test coverage includes:

- User registration validation.
- Login validation.
- Invalid password handling.
- PDF text extraction.
- DOCX text extraction, if enabled in the document service.
- TXT text extraction.
- Empty document validation.
- Unsupported file validation.
- Upload authentication.

The tests help identify issues in the backend and ensure that invalid requests are handled correctly.

---

## 12. RAG Evaluation

RAGAS is used to evaluate the quality of the generated responses.

The evaluation focuses on the following metrics:

| Metric | Description |
|---|---|
| Faithfulness | Checks whether the answer is supported by the retrieved context |
| Answer Relevancy | Checks whether the answer addresses the question |
| Context Precision | Measures the relevance of retrieved chunks |
| Context Recall | Measures how much relevant information is retrieved |

The evaluation results help identify areas where retrieval and answer generation can be improved.

---

## 13. Advantages

- No external embedding API is required.
- The LLM runs locally using Ollama.
- Document processing and retrieval are handled within the application.
- Supports semantic search using vector embeddings.
- Uses JWT authentication to protect endpoints.
- Stores user and document information in MySQL.
- Provides a simple chat-based interface.
- Allows evaluation of answer quality using RAGAS.

---

## 14. Future Enhancements

1. Improve retrieval accuracy through chunk size and overlap optimization.
2. Add support for more document formats.
3. Improve performance for large document collections.
4. Implement document-level access control.
5. Add advanced chat history management.
6. Improve answer faithfulness through better context retrieval.
7. Add support for additional local embedding models.
8. Implement more complete end-to-end testing.
9. Improve handling of database and LLM failures.

---

## 15. Conclusion

The PDF RAG Assistant provides a way to interact with documents using natural-language questions.

The application combines FastAPI, Streamlit, MySQL, Sentence Transformers and Ollama to build a document question-answering system without depending on external embedding or LLM APIs.

Through this project, I implemented user authentication, document processing, embedding generation, similarity-based retrieval and local LLM integration.

The project also helped me understand how Retrieval-Augmented Generation works in practice, from converting documents into embeddings to retrieving relevant information and generating answers using an LLM.

Overall, the application demonstrates how locally running AI models can be integrated with backend technologies to build a practical document-based question-answering system.