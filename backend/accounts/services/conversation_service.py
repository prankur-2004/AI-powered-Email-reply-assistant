from accounts.models import Email, AIReply


def get_conversation_context(
    conversation_id,
    user,
    current_email_id=None
):
    """
    Retrieve the email thread and previous AI replies
    for a specific conversation.
    """

    if not conversation_id:
        return []

    emails = Email.objects.filter(
        user=user,
        conversation_id=conversation_id
    ).order_by('created_at')

    conversation = []

    for email in emails:

        # Skip the current email when requested.
        # The current email will be supplied separately
        # to Gemini as the email being answered.
        if (
            current_email_id is not None
            and email.id == current_email_id
        ):
            continue

        conversation.append(
            {
                'email_id': email.id,
                'sender': email.sender,
                'recipient': email.recipient,
                'subject': email.subject,
                'body': email.body,
                'created_at': email.created_at,
                'ai_replies': []
            }
        )

        replies = AIReply.objects.filter(
            user=user,
            email=email
        ).order_by('created_at')

        for reply in replies:

            conversation[-1]['ai_replies'].append(
                {
                    'reply_id': reply.id,
                    'generated_reply': (
                        reply.generated_reply
                    ),
                    'is_accepted': (
                        reply.is_accepted
                    ),
                    'is_edited': (
                        reply.is_edited
                    ),
                    'created_at': reply.created_at
                }
            )

    return conversation


def format_conversation_context(
    conversation
):
    """
    Convert conversation history into text that can
    be safely included in the Gemini prompt.
    """

    if not conversation:
        return (
            'No previous conversation history '
            'is available.'
        )

    context_parts = []

    for index, email in enumerate(
        conversation,
        start=1
    ):

        context_parts.append(
            f"""
PREVIOUS EMAIL {index}

Sender:
{email['sender']}

Recipient:
{email['recipient']}

Subject:
{email['subject']}

Email:
{email['body']}
"""
        )

        for reply_index, reply in enumerate(
            email['ai_replies'],
            start=1
        ):

            context_parts.append(
                f"""
PREVIOUS AI REPLY {reply_index}

Reply:
{reply['generated_reply']}
"""
            )

    return '\n'.join(
        context_parts
    ).strip()