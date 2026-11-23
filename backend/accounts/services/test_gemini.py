from .gemini_service import generate_email_reply


if __name__ == '__main__':
    email = """
We are pleased to invite you for an interview.
Please let us know your availability for tomorrow.
"""

    reply = generate_email_reply(
        email_text=email,
        intent="meeting",
        sentiment="positive",
        urgency="normal",
        topic="interview",
        summary="Interview invitation and request for availability."
    )

    print("Generated Email Reply")
    print("======================")
    print()
    print(reply)