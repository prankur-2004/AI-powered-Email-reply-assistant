import json
import math

from .embedding_service import generate_embedding

from accounts.models import PersonalKnowledge


# Minimum similarity required for a knowledge item
# to be considered relevant.
SIMILARITY_THRESHOLD = 0.55


def cosine_similarity(vector_a, vector_b):
    """
    Calculate cosine similarity between two vectors.
    """

    if not vector_a or not vector_b:
        return 0.0

    if len(vector_a) != len(vector_b):
        return 0.0

    dot_product = 0.0

    magnitude_a = 0.0

    magnitude_b = 0.0

    for i in range(len(vector_a)):

        dot_product += (
            vector_a[i] * vector_b[i]
        )

        magnitude_a += (
            vector_a[i] * vector_a[i]
        )

        magnitude_b += (
            vector_b[i] * vector_b[i]
        )

    magnitude_a = math.sqrt(
        magnitude_a
    )

    magnitude_b = math.sqrt(
        magnitude_b
    )

    if magnitude_a == 0 or magnitude_b == 0:

        return 0.0

    return (
        dot_product
        / (magnitude_a * magnitude_b)
    )


def search_personal_knowledge(
    query,
    user,
    top_k=3
):
    """
    Find the most relevant personal knowledge
    entries for a given query.

    Knowledge items below the similarity threshold
    are ignored.
    """

    if not query or not query.strip():

        return []

    # -----------------------------------------
    # STEP 1: Get user's knowledge first
    # -----------------------------------------

    knowledge_items = PersonalKnowledge.objects.filter(
        user=user
    ).exclude(
        embedding=''
    ).exclude(
        embedding='[]'
    )

    if not knowledge_items.exists():
        return []

    # -----------------------------------------
    # STEP 2: Generate query embedding safely
    # -----------------------------------------

    try:
        query_embedding = generate_embedding(
            query
        )
    except Exception as exc:
        print(f"Warning: RAG embedding generation failed: {exc}. Continuing without knowledge context.")
        return []

    if not query_embedding:
        return []

    results = []

    # -----------------------------------------
    # STEP 3: Calculate similarity
    # -----------------------------------------

    for item in knowledge_items:

        try:

            item_embedding = json.loads(
                item.embedding
            )

        except (
            json.JSONDecodeError,
            TypeError
        ):

            continue

        similarity = cosine_similarity(
            query_embedding,
            item_embedding
        )

        # -----------------------------------------
        # STEP 4: Apply similarity threshold
        # -----------------------------------------

        if similarity < SIMILARITY_THRESHOLD:

            continue

        results.append(
            {
                'id': item.id,
                'title': item.title,
                'content': item.content,
                'similarity': similarity
            }
        )

    # -----------------------------------------
    # STEP 5: Sort by relevance
    # -----------------------------------------

    results.sort(
        key=lambda x: x['similarity'],
        reverse=True
    )

    # -----------------------------------------
    # STEP 6: Return top K results
    # -----------------------------------------

    return results[:top_k]