import re


def clean_spacing(text):
    if not text:
        return ''

    # Fix spaces before punctuation
    text = re.sub(
        r'\s+([,.!?;:])',
        r'\1',
        text
    )

    # Fix missing spaces after punctuation
    text = re.sub(
        r'([,.!?;:])([A-Za-z])',
        r'\1 \2',
        text
    )

    # Common joined-word corrections
    replacements = {
        'howmy': 'how my',
        'howyour': 'how your',

        'theinterview': 'the interview',
        'theopportunity': 'the opportunity',
        'theposition': 'the position',
        'theteam': 'the team',
        'thecompany': 'the company',
        'theproject': 'the project',
        'themeeting': 'the meeting',
        'theemail': 'the email',
        'thejob': 'the job',
        'thenext': 'the next',
        'thefollowing': 'the following',
        'theexperience': 'the experience',
        'thebackground': 'the background',
        'theprocess': 'the process',
        'thedate': 'the date',
        'thetime': 'the time',

        'let meknow': 'let me know',
        'pleaselet': 'please let',
        'I amvery': 'I am very',

        'lookforward': 'look forward',
        'lookforwardto': 'look forward to',

        'thankyou': 'thank you',
        'thankyoufor': 'thank you for',

        'Bestregards': 'Best regards',
        'BestRegards': 'Best Regards',

        'alignwith': 'align with',
        'proposeddates': 'proposed dates',

        'Iwill': 'I will',
        'iwill': 'I will',
        'Iwould': 'I would',
        'iwould': 'I would',
        'Ihave': 'I have',
        'ihave': 'I have',
        'Ican': 'I can',
        'ican': 'I can',
        'Iwouldbe': 'I would be',

        'pleas e': 'please',

        'DearHiring': 'Dear Hiring',
        'HiringManager': 'Hiring Manager',

        'toinvite': 'to invite',
        'forinviting': 'for inviting',
        'invitingme': 'inviting me',

        'excitedabout': 'excited about',
        'interestedin': 'interested in',
        'discussingmy': 'discussing my',
        'discussingyour': 'discussing your',

        'availabledates': 'available dates',
        'availabletimes': 'available times',
        'nextsteps': 'next steps',
        'youravailability': 'your availability',

        'withyour': 'with your',
        'foryour': 'for your',
        'forthis': 'for this',
        'fromyou': 'from you',
        'forme': 'for me',
        'withme': 'with me',

        'andlook': 'and look',
        'anddiscuss': 'and discuss',
        'andthank': 'and thank',

        'veryinterested': 'very interested',
        'veryexcited': 'very excited',

        'thisopportunity': 'this opportunity',
        'mybackground': 'my background',
        'myexperience': 'my experience',
        'myskills': 'my skills',

        'yourteam': 'your team',
        'yourcompany': 'your company',

        'theavailable': 'the available'
    }

    for wrong, correct in replacements.items():
        text = text.replace(
            wrong,
            correct
        )

    # Remove common placeholders
    text = re.sub(
        r'\[(Hiring Manager\s*/\s*Team|'
        r'Hiring Manager\s*/\s*Recruiter|'
        r'Name)\]',
        '',
        text,
        flags=re.IGNORECASE
    )

    # Normalize spaces inside each line
    lines = []

    for line in text.splitlines():

        line = line.strip()

        if line:
            line = re.sub(
                r'[ \t]+',
                ' ',
                line
            )

        lines.append(line)

    text = '\n'.join(lines)

    # Keep paragraph breaks but remove excessive blank lines
    text = re.sub(
        r'\n\s*\n\s*\n+',
        '\n\n',
        text
    )

    return text.strip()


def remove_subject_line(text):
    lines = text.splitlines()

    cleaned_lines = []

    for line in lines:

        if re.match(
            r'^\s*subject\s*:',
            line,
            re.IGNORECASE
        ):
            continue

        cleaned_lines.append(line)

    return '\n'.join(cleaned_lines)


def remove_placeholders(text):

    placeholder_patterns = [
        r'\[Your Name\]',
        r'\[Name\]',
        r'\[Your Company\]',
        r'\[Company Name\]',
        r'\[Insert Name\]',
        r'\[Insert Time\]',
        r'\[Insert Date\]',
        r'\[Hiring Manager / Team\]',
        r'\[Hiring Manager/Team\]',
        r'\[Hiring Manager / Recruiter\]',
        r'\[Hiring Manager/Recruiter\]',
        r'\[Recipient Name\]',
        r'\[Recipient\]'
    ]

    for pattern in placeholder_patterns:

        text = re.sub(
            pattern,
            '',
            text,
            flags=re.IGNORECASE
        )

    return text


def remove_ai_mentions(text):

    ai_patterns = [
        r'As an AI[^.]*\.',
        r'As an artificial intelligence[^.]*\.',
        r'I am an AI[^.]*\.',
        r'I am an artificial intelligence[^.]*\.'
    ]

    for pattern in ai_patterns:

        text = re.sub(
            pattern,
            '',
            text,
            flags=re.IGNORECASE
        )

    return text


def detect_spacing_problems(text):

    suspicious_patterns = [
        r'\bIwill\b',
        r'\bBestregards\b',
        r'\balignwith\b',
        r'\bproposeddates\b',

        r'\btheinterview\b',
        r'\btheopportunity\b',
        r'\btheposition\b',
        r'\btheteam\b',
        r'\btheproject\b',
        r'\bthemeeting\b',
        r'\bthenext\b',
        r'\bthefollowing\b',

        r'\bthankyou\b',
        r'\blookforward\b',
        r'\bhowmy\b',

        r'\btoinvite\b',
        r'\bforinviting\b',
        r'\binvitingme\b',
        r'\bexcitedabout\b',
        r'\binterestedin\b',
        r'\bdiscussingmy\b',
        r'\bdiscussingyour\b',

        r'\bnextsteps\b',
        r'\bandlook\b',

        r'\bavailabledates\b',
        r'\bavailabletimes\b',
        r'\byouravailability\b',

        r'\bwithyour\b',
        r'\bforyour\b',

        r'\bmybackground\b',
        r'\bmyexperience\b',
        r'\bmyskills\b',

        r'\byourteam\b',
        r'\byourcompany\b'
    ]

    issues = []

    for pattern in suspicious_patterns:

        if re.search(
            pattern,
            text,
            re.IGNORECASE
        ):

            issues.append(
                'Detected joined words or spacing problems.'
            )

            break

    return issues


def validate_reply(text):

    if not text or not text.strip():

        return {
            'is_valid': False,
            'reply': '',
            'issues': [
                'Generated reply is empty.'
            ]
        }

    issues = []

    # Remove subject line
    original_text = text

    text = remove_subject_line(text)

    if text != original_text:

        issues.append(
            'Removed unwanted subject line.'
        )

    # Remove placeholders
    original_text = text

    text = remove_placeholders(text)

    if text != original_text:

        issues.append(
            'Removed placeholders.'
        )

    # Remove AI mentions
    original_text = text

    text = remove_ai_mentions(text)

    if text != original_text:

        issues.append(
            'Removed AI-related statements.'
        )

    # Detect spacing problems
    spacing_issues = detect_spacing_problems(
        text
    )

    issues.extend(
        spacing_issues
    )

    # Clean formatting
    original_text = text

    text = clean_spacing(text)

    if text != original_text:

        if (
            'Fixed formatting and spacing.'
            not in issues
        ):

            issues.append(
                'Fixed formatting and spacing.'
            )

    text = text.strip()

    # Remove accidental leading commas
    text = re.sub(
        r'^\s*,+',
        '',
        text
    )

    # Remove accidental trailing commas
    text = re.sub(
        r',+\s*$',
        '',
        text
    )

    text = text.strip()

    # Final length validation
    if len(text) < 10:

        return {
            'is_valid': False,
            'reply': text,
            'issues': issues + [
                'Generated reply is too short.'
            ]
        }

    return {
        'is_valid': True,
        'reply': text,
        'issues': issues
    }