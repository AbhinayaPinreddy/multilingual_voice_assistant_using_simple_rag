import json
import numpy as np
import re
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

import config

with open("products.json") as f:
    products = json.load(f)

model = SentenceTransformer("sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
product_vectors = np.load("embeddings.npy")


def extract_price(query):
    nums = re.findall(r"\d+", query)
    return int(nums[0]) if nums else None


def retrieve(query):
    """Multilingual query text is fine — same embedder as products. Top-K kept small for LLM latency."""
    top_k = min(config.RAG_TOP_K, len(products))
    pool = min(max(12, top_k * 4), len(products))

    query_vec = model.encode([query], show_progress_bar=False)
    scores = cosine_similarity(query_vec, product_vectors)[0]

    top_idx = np.argpartition(scores, -pool)[-pool:]
    top_idx = top_idx[np.argsort(scores[top_idx])[::-1]]

    results = [products[i] for i in top_idx]

    max_price = extract_price(query)
    if max_price:
        results = [p for p in results if p["price"] <= max_price]

    return results[:top_k]