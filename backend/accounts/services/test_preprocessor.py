from .email_preprocessor import preprocess_email


if __name__ == '__main__':
    email = """
<html>
<body>

Hello,

Could you please send me the project report?

Regards,
Parth

> Previous email content
> This is an old message

</body>
</html>
"""

    clean_email = preprocess_email(email)

    print("Original Email:")
    print(email)

    print("\nClean Email:")
    print(clean_email)