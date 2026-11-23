import os
import sys
import json


# Add the backend directory to Python's path
sys.path.append(
    os.path.dirname(
        os.path.dirname(
            os.path.dirname(
                os.path.abspath(__file__)
            )
        )
    )
)


os.environ.setdefault(
    'DJANGO_SETTINGS_MODULE',
    'config.settings'
)


import django

django.setup()


from accounts.models import PersonalKnowledge

from embedding_service import generate_embedding


print("Generating Knowledge Embeddings")
print("================================")
print()


knowledge_items = PersonalKnowledge.objects.all()


if not knowledge_items.exists():

    print("No personal knowledge entries found.")

    sys.exit()


for item in knowledge_items:

    print(
        f"Processing: {item.title}"
    )

    text = f"""
Title: {item.title}

Content:
{item.content}
"""

    embedding = generate_embedding(
        text
    )

    item.embedding = json.dumps(
        embedding
    )

    item.save(
        update_fields=['embedding']
    )

    print(
        f"Embedding generated: {len(embedding)} dimensions"
    )

    print()


print("================================")
print("All embeddings generated successfully.")