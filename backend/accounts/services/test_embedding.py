from .embedding_service import generate_embedding


if __name__ == '__main__':
    text = """
Java, MERN Stack, Python, Django, REST API,
MongoDB and SQL.
"""

    embedding = generate_embedding(text)

    print("Embedding Test")
    print("==============")

    print()

    print("Embedding generated successfully.")

    print(
        "Vector dimensions:",
        len(embedding)
    )

    print()

    print(
        "First 10 values:",
        embedding[:10]
    )