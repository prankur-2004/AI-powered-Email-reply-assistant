import re


def detect_intent(text):
    """
    Detect the basic intent of an email.
    """

    text_lower = text.lower()

    if any(
        word in text_lower
        for word in [
            'please send',
            'send me',
            'provide',
            'share',
            'could you',
            'can you'
        ]
    ):
        return 'request'

    if any(
        word in text_lower
        for word in [
            'thank you',
            'thanks',
            'appreciate'
        ]
    ):
        return 'thank_you'

    if any(
        word in text_lower
        for word in [
            'meeting',
            'interview',
            'appointment',
            'schedule'
        ]
    ):
        return 'meeting'

    if any(
        word in text_lower
        for word in [
            'problem',
            'issue',
            'error',
            'not working'
        ]
    ):
        return 'complaint'

    if '?' in text:
        return 'question'

    return 'general'


def detect_sentiment(text):
    """
    Detect basic email sentiment.
    """

    text_lower = text.lower()

    positive_words = [
        'thank',
        'thanks',
        'great',
        'excellent',
        'happy',
        'pleased',
        'appreciate'
    ]

    negative_words = [
        'problem',
        'issue',
        'error',
        'bad',
        'disappointed',
        'angry',
        'urgent'
    ]

    positive_score = sum(
        word in text_lower
        for word in positive_words
    )

    negative_score = sum(
        word in text_lower
        for word in negative_words
    )

    if positive_score > negative_score:
        return 'positive'

    if negative_score > positive_score:
        return 'negative'

    return 'neutral'


def detect_urgency(text):
    """
    Detect email urgency.
    """

    text_lower = text.lower()

    urgent_words = [
        'urgent',
        'immediately',
        'as soon as possible',
        'asap',
        'today',
        'tomorrow',
        'deadline',
        'emergency'
    ]

    for word in urgent_words:

        if word in text_lower:
            return 'high'

    return 'normal'


def detect_topic(text):
    """
    Detect the main topic of the email.
    """

    text_lower = text.lower()

    topics = {
        'interview': [
            'interview',
            'job interview',
            'interview invitation'
        ],

        'project': [
            'project',
            'assignment',
            'report'
        ],

        'meeting': [
            'meeting',
            'appointment',
            'schedule'
        ],

        'payment': [
            'payment',
            'invoice',
            'salary',
            'transaction'
        ],

        'technical': [
            'error',
            'bug',
            'technical',
            'not working'
        ]
    }

    for topic, keywords in topics.items():

        for keyword in keywords:

            if keyword in text_lower:
                return topic

    return 'general'


def extract_entities(text):
    """
    Extract simple entities such as dates and email addresses.
    """

    entities = []

    # Email addresses
    email_addresses = re.findall(
        r'[\w\.-]+@[\w\.-]+\.\w+',
        text
    )

    entities.extend(email_addresses)

    # Common time-related words
    time_words = [
        'today',
        'tomorrow',
        'yesterday',
        'monday',
        'tuesday',
        'wednesday',
        'thursday',
        'friday',
        'saturday',
        'sunday'
    ]

    text_lower = text.lower()

    for word in time_words:

        if word in text_lower:
            entities.append(word)

    return list(dict.fromkeys(entities))


def generate_summary(text):
    """
    Generate a simple summary from the email.
    """

    sentences = re.split(
        r'[.!?]+',
        text
    )

    sentences = [
        sentence.strip()
        for sentence in sentences
        if sentence.strip()
    ]

    if not sentences:
        return ''

    return sentences[0]


def analyze_email(text):
    """
    Analyze an email and return structured information.
    """

    if not text or not text.strip():

        return {
            'intent': 'unknown',
            'sentiment': 'neutral',
            'urgency': 'normal',
            'topic': 'general',
            'entities': [],
            'summary': ''
        }

    return {
        'intent': detect_intent(text),
        'sentiment': detect_sentiment(text),
        'urgency': detect_urgency(text),
        'topic': detect_topic(text),
        'entities': extract_entities(text),
        'summary': generate_summary(text)
    }