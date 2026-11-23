import re
from html import unescape


def remove_html(text):
    """
    Remove HTML tags from email text.
    """

    text = re.sub(
        r'<[^>]+>',
        ' ',
        text
    )

    text = unescape(text)

    return text


def remove_quoted_text(text):
    """
    Remove previous/replied email content.
    """

    lines = text.splitlines()

    cleaned_lines = []

    for line in lines:

        # Remove lines beginning with >
        if line.strip().startswith('>'):
            continue

        # Remove common reply markers
        if re.match(
            r'^\s*(On .+wrote:|From:|Sent:|To:|Subject:)',
            line,
            re.IGNORECASE
        ):
            break

        cleaned_lines.append(line)

    return '\n'.join(cleaned_lines)


def remove_signature(text):
    """
    Remove common email signature sections.
    """

    lines = text.splitlines()

    cleaned_lines = []

    for line in lines:

        if line.strip() in [
            '--',
            '-- ',
            'Thanks,',
            'Regards,',
            'Best regards,',
            'Kind regards,'
        ]:
            break

        cleaned_lines.append(line)

    return '\n'.join(cleaned_lines)


def normalize_whitespace(text):
    """
    Remove unnecessary spaces and blank lines.
    """

    text = re.sub(
        r'[ \t]+',
        ' ',
        text
    )

    text = re.sub(
        r'\n\s*\n+',
        '\n\n',
        text
    )

    return text.strip()


def preprocess_email(text):
    """
    Complete email preprocessing pipeline.
    """

    if not text:
        return ''

    text = remove_html(text)

    text = remove_quoted_text(text)

    text = remove_signature(text)

    text = normalize_whitespace(text)

    return text