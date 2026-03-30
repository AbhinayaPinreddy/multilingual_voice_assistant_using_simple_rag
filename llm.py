from groq import Groq
import os
from dotenv import load_dotenv

import config

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))


def generate(context, query):
    prompt = f"""Indian shopping assistant. Answer ONLY from the context. One or two short sentences. Include ₹ price.

Context:
{context}

Question: {query}
"""

    res = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.25,
        max_tokens=config.LLM_MAX_TOKENS,
    )

    return res.choices[0].message.content