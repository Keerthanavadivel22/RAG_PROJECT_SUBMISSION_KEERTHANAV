import os

from pinecone import Pinecone
from dotenv import load_dotenv

load_dotenv()


# Connect to Pinecone

pc = Pinecone(
    api_key=os.getenv("PINECONE_KEY")
)

# Existing document index

index = pc.Index(
    os.getenv("PINECONE_INDEX_NAME") # type: ignore
)
print("Index type:", type(index))
print("Has documents:", hasattr(index, "documents"))

try:
    print("Documents object:", index.documents) # type: ignore
except Exception as e:
    print("Error:", repr(e))

# Generate namespace for each user

def get_namespace(user_id):

    return f"user_{user_id}"


# Store chunks in Pinecone

def store_chunks(
    user_id,
    document_id,
    file_name,
    chunks,
    chunk_ids
):

    namespace = get_namespace(user_id)

    documents = []

    for idx, chunk in enumerate(chunks):

        documents.append({

            "_id": f"doc_{document_id}_chunk_{idx}",

            "title": file_name,

            "chunk_text": chunk,

            "user_id": int(user_id),

            "document_id": int(document_id),

            "chunk_id": int(chunk_ids[idx]),

            "chunk_index": idx,

            "file_name": file_name

        })

    # Upload in batches

    batch_size = 50

    for start in range(0, len(documents), batch_size):

        batch = documents[start:start + batch_size]

        index.documents.upsert( # type: ignore
            namespace=namespace,
            documents=batch
        )

    return len(documents)


# Search selected document

def search_chunks(
    user_id,
    document_id,
    question,
    top_k=5
):

    namespace = get_namespace(user_id)

    results = index.documents.search( # type: ignore

        namespace=namespace,

        top_k=top_k,

        score_by=[
            {
                "type": "embed",
                "fields": ["chunk_text"],
                "query": question
            }
        ],

        filter={
            "document_id": {
                "$eq": int(document_id)
            },

            "user_id": {
                "$eq": int(user_id)
            }
        },

        include_fields=[
            "title",
            "chunk_text",
            "document_id",
            "chunk_index",
            "file_name"
        ]
    )

    # Current Documents API returns matches directly.
    matches = results.matches

    retrieved_chunks = []

    for match in matches:

        retrieved_chunks.append({

            "text": match.chunk_text,

            "score": match.score,

            "chunk_index": match.chunk_index

        })

    return retrieved_chunks


# Delete a document's chunks

def delete_document_vectors(user_id, document_id):

    namespace = get_namespace(user_id)

    index.documents.delete( # type: ignore

        namespace=namespace,

        filter={
            "document_id": {
                "$eq": int(document_id)
            },

            "user_id": {
                "$eq": int(user_id)
            }
        }
    )