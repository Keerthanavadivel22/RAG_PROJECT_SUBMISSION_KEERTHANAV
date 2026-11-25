
import requests

OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL_NAME = "llama3.2:3b"


def generate_answer(question, context, history=None):

    system_prompt = f"""
    You are a helpful document assistant.

    Answer questions using ONLY the information
    available in the document context.

    Instructions:
    1. Combine relevant information from multiple chunks.
    2. Present answers clearly using simple language.
    3. Use bullet points when listing features or steps.
    4. Do not unnecessarily say information is missing
    if the context contains a relevant answer.
    5. If the answer is genuinely unavailable,
    say the document does not contain enough information.
    6. Never invent facts.

    DOCUMENT CONTEXT:
    {context}
    """

    messages = [
        {
            "role": "system",
            "content": system_prompt
        }
    ]

    # Add previous conversation
    if history:
        messages.extend(history[-4:])

    messages.append({
        "role": "user",
        "content": question
    })

    payload = {
        "model": MODEL_NAME,
        "messages": messages,
        "stream": False,
        "options": {
            "temperature": 0.2,
            "num_predict": 512
        }
    }

    response = requests.post(
        OLLAMA_URL,
        json=payload,
        timeout=300
    )

    response.raise_for_status()

    return response.json()["message"]["content"]
