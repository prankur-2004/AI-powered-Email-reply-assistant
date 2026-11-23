from .response_validator import validate_reply


if __name__ == '__main__':
    reply = """
Dear Hiring Manager,

Thank you for inviting me to interview for the position.
I am very excited about this opportunity and lookforward
to discussing howmy skills align with your team.

Please let meknow the available dates and times.

[Your Name]

Best regards,
"""

    result = validate_reply(reply)

    print("Response Validation")
    print("===================")

    print()

    print("Valid:", result['is_valid'])

    print()

    print("Issues:")

    for issue in result['issues']:
        print("-", issue)

    print()

    print("Cleaned Reply:")
    print(result['reply'])