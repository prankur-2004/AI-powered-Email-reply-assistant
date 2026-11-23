import os
import hashlib
from dotenv import load_dotenv

load_dotenv()


def generate_embedding(text):
    """
    Generate a vector embedding for the supplied text.
    First tries the user's custom API endpoint (/v1/embeddings).
    If custom embedding is unavailable, generates a lightweight deterministic vector
    so RAG similarity matching functions without any third-party external API.
    """
    if not text or not text.strip():
        return []

    # 1. Try Custom API embeddings
    try:
        from .custom_api_service import generate_custom_embedding
        custom_emb = generate_custom_embedding(text)
        if custom_emb and len(custom_emb) > 0:
            return custom_emb
    except Exception as err:
        print(f"Custom embedding attempt failed: {err}")

    # 2. Optional Gemini fallback only if GEMINI_API_KEY is explicitly configured
    gemini_key = os.getenv("GEMINI_API_KEY", "").strip()
    if gemini_key and gemini_key != "your_gemini_api_key_here":
        try:
            from google import genai
            client = genai.Client(api_key=gemini_key)
            result = client.models.embed_content(
                model="gemini-embedding-001",
                contents=text
            )
            return result.embeddings[0].values
        except Exception as gemini_err:
            print(f"Gemini embedding fallback failed: {gemini_err}")

    # 3. Deterministic lightweight local vector (dimension: 128) based on text tokens
    # Ensures RAG never crashes even if the custom server only runs chat completion
    return _generate_local_fallback_embedding(text)


def _generate_local_fallback_embedding(text, dimension=128):
    """
    Generate a simple normalized token-frequency vector for offline / standalone use.
    """
    tokens = text.lower().split()
    if not tokens:
        return [0.0] * dimension

    vector = [0.0] * dimension
    for token in tokens:
        idx = int(hashlib.md5(token.encode("utf-8")).hexdigest(), 16) % dimension
        vector[idx] += 1.0

    # L2 normalize
    norm = sum(x * x for x in vector) ** 0.5
    if norm > 0:
        vector = [x / norm for x in vector]

    return vector