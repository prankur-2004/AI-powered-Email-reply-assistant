from .email_analyzer import analyze_email


if __name__ == '__main__':
    email = """
Could you please send me the project report by tomorrow?
"""

    result = analyze_email(email)

    print("Email Analysis")
    print("================")

    print("Intent:", result['intent'])
    print("Sentiment:", result['sentiment'])
    print("Urgency:", result['urgency'])
    print("Topic:", result['topic'])
    print("Entities:", result['entities'])
    print("Summary:", result['summary'])