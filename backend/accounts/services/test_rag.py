import os
import sys


if __name__ == '__main__':
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

    from django.contrib.auth.models import User
    from .rag_service import search_personal_knowledge

    user = User.objects.first()

    query = """
Please tell me about your programming skills,
software development experience and technical
background.
"""


    results = search_personal_knowledge(
        query=query,
        user=user,
        top_k=3
    )

    print("RAG Semantic Search")
    print("===================")

    print()

    print("Query:")
    print(query)

    print()

    print("Relevant Knowledge:")
    print("===================")

    for index, result in enumerate(
        results,
        start=1
    ):
        print()
        print(f"{index}. {result['title']}")
        print("Similarity:", round(result['similarity'], 4))
        print("Content:", result['content'])