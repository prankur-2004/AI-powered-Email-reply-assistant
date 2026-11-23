import os
from dotenv import load_dotenv


def get_client():
    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError(
            "GEMINI_API_KEY is not set in the .env file."
        )
    from google import genai
    return genai.Client(api_key=api_key)


def generate_email_reply(
    email_text,
    intent="general",
    sentiment="neutral",
    urgency="normal",
    topic="general",
    summary="",
    user_preferences=None,
    personal_knowledge=None,
    conversation_context=""
):
    """
    Generate a personalized and conversation-aware
    email reply using Google Gemini.
    """

    if user_preferences is None:
        user_preferences = {}

    if personal_knowledge is None:
        personal_knowledge = []

    tone = user_preferences.get(
        "tone",
        "professional"
    )

    reply_length = user_preferences.get(
        "reply_length",
        "concise"
    )

    greeting = user_preferences.get(
        "greeting",
        "Dear"
    )

    sign_off = user_preferences.get(
        "sign_off",
        "Best regards"
    )

    knowledge_text = ""

    for item in personal_knowledge:
        knowledge_text += (
            f"- {item['title']}: "
            f"{item['content']}\n"
        )

    if not knowledge_text:
        knowledge_text = (
            "No relevant personal knowledge was found."
        )

    if not conversation_context:
        conversation_context = (
            "No previous conversation history "
            "is available."
        )

    prompt = f"""
You are an AI-powered personalized email reply assistant.

Your task is to generate a natural, professional,
personalized reply to the CURRENT EMAIL.

Use the following information:

1. CURRENT EMAIL
2. EMAIL ANALYSIS
3. PREVIOUS CONVERSATION HISTORY
4. USER PREFERENCES
5. RELEVANT PERSONAL KNOWLEDGE

--------------------------------------------------
CURRENT EMAIL
--------------------------------------------------

{email_text}

--------------------------------------------------
EMAIL ANALYSIS
--------------------------------------------------

Intent: {intent}
Sentiment: {sentiment}
Urgency: {urgency}
Topic: {topic}
Summary: {summary}

--------------------------------------------------
PREVIOUS CONVERSATION HISTORY
--------------------------------------------------

{conversation_context}

--------------------------------------------------
USER PREFERENCES
--------------------------------------------------

Tone: {tone}
Reply length: {reply_length}
Preferred greeting: {greeting}
Preferred sign-off: {sign_off}

--------------------------------------------------
RELEVANT PERSONAL KNOWLEDGE
--------------------------------------------------

{knowledge_text}

--------------------------------------------------
CONVERSATION RULES
--------------------------------------------------

1. Understand the CURRENT EMAIL first.

2. Use previous conversation history to understand
   the context of the discussion.

3. Maintain continuity with the previous conversation
   when appropriate.

4. Do not repeat information unnecessarily.

5. Do not blindly copy previous AI replies.

6. Previous AI replies may contain mistakes.
   Treat them only as historical context.

7. Prefer the CURRENT EMAIL over older messages
   if there is conflicting information.

--------------------------------------------------
PERSONAL KNOWLEDGE RULES
--------------------------------------------------

1. Use personal knowledge only when it is relevant.

2. Do not force personal knowledge into the reply.

3. Do not invent personal information.

4. Do not make claims that are not supported by
   the email or personal knowledge.

5. Never mention the RAG system.

6. Never mention similarity scores.

--------------------------------------------------
REPLY INSTRUCTIONS
--------------------------------------------------

1. Generate a natural professional email reply.

2. Follow the user's preferred tone.

3. Follow the requested reply length.

4. Maintain conversation continuity.

5. Use relevant personal knowledge naturally.

6. Do not mention that you are an AI.

7. Do not include a subject line.

8. Use the preferred greeting when appropriate.

9. End with the preferred sign-off when appropriate.

10. Do not use placeholders such as:

[Name]
[Your Name]
[Date]
[Time]
[Company Name]
[Hiring Manager]
[Recipient Name]

11. Do not invent names, dates, times, companies,
or other missing information.

12. Return ONLY the email reply.
"""

    from .custom_api_service import call_custom_api

    # Call user's own custom API endpoint exclusively
    try:
        reply = call_custom_api(prompt)
    except Exception as error:
        print("========================================")
        print("CUSTOM API ERROR")
        print(f"{type(error).__name__}: {error}")
        print("========================================")
        raise RuntimeError(f"AI reply generation failed on Custom API: {error}") from error

    if not reply or not reply.strip():
        raise RuntimeError("Custom AI API returned an empty response.")

    return reply.strip()