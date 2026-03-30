import json
import numpy as np
from sentence_transformers import SentenceTransformer

model = SentenceTransformer("sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")

with open("products.json") as f:
    products = json.load(f)

texts = [
    f"{p['name']} {p['description']} {p['category']}"
    for p in products
]

embeddings = model.encode(texts)

np.save("embeddings.npy", embeddings)

print("✅ embeddings saved")