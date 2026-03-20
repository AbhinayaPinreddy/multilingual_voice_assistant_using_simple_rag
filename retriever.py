import json
import numpy as np
import re
from sentence_transformers import SentenceTransformer

# Load products
with open("products.json", "r") as f:
    products = json.load(f)

# Load embedding model
model = SentenceTransformer("sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")

# Precompute embeddings
product_texts = [
    f"{p['name']} {p['description']} {p['category']}"
    for p in products
]

product_vectors = model.encode(product_texts)

def extract_price(query):
    nums = re.findall(r"\d+", query)
    return int(nums[0]) if nums else None

def retrieve(query):
    query_vec = model.encode([query])[0]

    scores = np.dot(product_vectors, query_vec)
    top_indices = np.argsort(scores)[-5:][::-1]

    results = [products[i] for i in top_indices]

    # Smart price filtering
    max_price = extract_price(query)
    if max_price:
        results = [p for p in results if p["price"] <= max_price]

    return results[:3]