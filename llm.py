import os
from groq import Groq
from dotenv import load_dotenv

# Load .env file
load_dotenv()

# Get API key
api_key = os.getenv("GROQ_API_KEY")

client = Groq(api_key=api_key)


def generate(context, query):
    prompt = f"""
    You are a helpful shopping assistant.

    Answer ONLY using the given products.
    If no relevant product is found, say that clearly.

    Keep the answer short and natural.

    Context:
    {context}

    Question:
    {query}
    """

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7
    )

    return response.choices[0].message.content