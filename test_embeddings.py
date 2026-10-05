from sentence_transformers import SentenceTransformer
import numpy as np

model = SentenceTransformer("all-MiniLM-L6-v2")

expenses = [
    "Emergency roadside assistance and car towing",
    "Dinner at a restaurant",
    "Monthly electricity bill",
    "Bought a new laptop",
    "Flight ticket to Delhi",
]

query = "Find that time I got my car towed"

expense_embeddings = model.encode(expenses)
query_embedding = model.encode(query)

similarities = np.dot(expense_embeddings, query_embedding) / (
    np.linalg.norm(expense_embeddings, axis=1)
    * np.linalg.norm(query_embedding)
)

results = sorted(
    zip(expenses, similarities),
    key=lambda x: x[1],
    reverse=True
)

for expense, score in results:
    print(f"{score:.3f}  {expense}")