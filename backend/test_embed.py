from app.embeddings.embedder import embed_texts, embed_query, embedding_dim

print("dim:", embedding_dim())
vecs = embed_texts(["def login(user): pass", "class Database: pass", "hello world"])
print("num vectors:", len(vecs))
print("vec[0] length:", len(vecs[0]))
q = embed_query("where is login handled?")
print("query vector length:", len(q))