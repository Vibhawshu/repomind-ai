import os
import gc
import torch
from functools import lru_cache
from sentence_transformers import SentenceTransformer
from app.config import settings

# Force PyTorch to use 1 thread to prevent CPU lockups
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"

@lru_cache(maxsize=1)
def get_model() -> SentenceTransformer:
    # Force CPU to prevent GPU memory crashes
    return SentenceTransformer(settings.EMBEDDING_MODEL, device="cpu")

def embed_texts(texts: list[str]) -> list[list[float]]:
    if not texts:
        return []
    model = get_model()
    
    # Small batch size to prevent RAM spike
    vectors = model.encode(
        texts,
        batch_size=8, 
        show_progress_bar=False,
        convert_to_numpy=True,
        normalize_embeddings=True,
    )
    
    # CRITICAL FIX: Force Python and PyTorch to release RAM back to the system
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
        
    return vectors.tolist()

def embed_query(text: str) -> list[float]:
    return embed_texts([text])[0]

def embedding_dim() -> int:
    return get_model().get_sentence_embedding_dimension()