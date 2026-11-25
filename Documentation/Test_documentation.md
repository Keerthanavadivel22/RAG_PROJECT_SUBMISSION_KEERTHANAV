# RAG API – Test Documentation

## 1. Overview

The RAG API project uses **pytest** to verify authentication, document extraction, and file upload validation.

The purpose of testing is to identify errors, validate expected API behavior, and ensure invalid inputs are handled correctly.

## 2. Testing Tools

| Tool | Purpose |
|---|---|
| Pytest | Python testing framework |
| FastAPI TestClient | Testing API endpoints |
| pytest fixtures | Reusable test setup |
| tmp_path | Temporary files for document extraction tests |
| Mocking | Isolating external dependencies |

## 3. Test File Structure

```text
tests/
├── conftest.py
├── test_auth.py
├── test_document_service.py
└── test_upload.py
```

- **conftest.py:** Provides reusable test clients and authentication fixtures.
- **test_auth.py:** Tests user registration and login.
- **test_document_service.py:** Tests text extraction from PDF, DOCX, and TXT files.
- **test_upload.py:** Tests upload validation and authentication.

## 4. Test Cases

### 4.1 Authentication Testing

| Test Case | Expected Result |
|---|---|
| Register valid user | Successful registration |
| Register with invalid email | Validation error |
| Login with wrong password | Login rejected |

### 4.2 Document Extraction Testing

| Test Case | Expected Result |
|---|---|
| Extract TXT file | Text extracted successfully |
| Extract DOCX file | Text extracted successfully |
| Extract PDF file | Text extracted successfully |
| Upload unsupported file type to extraction service | ValueError raised |
| Extract empty TXT file | Empty content handled correctly |

### 4.3 File Upload Testing

| Test Case | Expected Result |
|---|---|
| Upload unsupported file | HTTP 400 |
| Upload empty file | HTTP 400 |
| Upload invalid PDF | HTTP 400 |
| Upload invalid DOCX | HTTP 400 |
| Upload TXT with invalid encoding | HTTP 400 |
| Upload without authentication | HTTP 401 |

## 5. Test Execution

Command used:

```bash
pytest -v
```

The `-v` option displays individual test names and their execution status.

## 6. Test Results

**Execution summary:**

| Metric | Result |
|---|---:|
| Total test cases | 14 |
| Passed | 14 |
| Failed | 0 |
| Warnings | 1 |
| Execution time | 1.35 seconds |

**Overall result: PASS**

All 14 test cases passed successfully.

## 7. Observations

- Authentication validation works as expected for the tested scenarios.
- Document extraction works for PDF, DOCX, and TXT files.
- Invalid file types, empty files, and malformed file content are rejected.
- Protected upload endpoints reject unauthenticated requests.
- A deprecation warning was reported for the `fitz` API. Replacing `import fitz` with `import pymupdf` is recommended.

## 8. Future Testing

The following scenarios are planned for additional coverage:

1. Successful document upload with mocked MySQL.
2. Pinecone integration testing using mocked vector storage.
3. Database rollback when an upload fails.
4. Temporary file cleanup after upload failure.
5. Document listing and user-specific access control.
6. Error handling for database and vector storage failures.

**Note:** The current 14-test result covers the test cases listed above. Successful end-to-end upload, database rollback, and Pinecone storage have not yet been verified by this test run.



![alt text](<Screenshot 2026-11-24 133609.png>)