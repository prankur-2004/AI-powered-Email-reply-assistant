import os
from dotenv import load_dotenv

load_dotenv()

# Reliable text generation models available on Groq
FALLBACK_MODELS = [
    "openai/gpt-oss-120b",
    "openai/gpt-oss-20b",
    "qwen/qwen3.8-27b",
    "llama-3.3-70b-versatile",
]


def is_groq_configured():
    """
    Check if a valid GROQ_API_KEY is configured in the environment.
    """
    load_dotenv()
    key = os.getenv("GROQ_API_KEY", "").strip()
    return bool(key and key != "your_groq_api_key_here")


def call_groq_api(prompt, model=None):
    """
    Generate an email reply using Groq Cloud API.
    Ultra-fast inference (under 1 second) with generous free tier limits.
    """
    load_dotenv()
    api_key = os.getenv("GROQ_API_KEY", "").strip()

    if not api_key or api_key == "your_groq_api_key_here":
        raise ValueError(
            "GROQ_API_KEY is not set in backend/.env. "
            "Please obtain a free key at https://console.groq.com/keys and add it to .env."
        )

    preferred_model = model or os.getenv("GROQ_MODEL", "openai/gpt-oss-120b").strip()
    models_to_try = [preferred_model] + [m for m in FALLBACK_MODELS if m != preferred_model]

    from groq import Groq
    client = Groq(api_key=api_key)

    last_error = None
    for target_model in models_to_try:
        try:
            print("========================================")
            print("Calling Groq Cloud API...")
            print(f"Model: {target_model}")
            print("========================================")

            chat_completion = client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are an AI-powered personalized email reply assistant. "
                            "Generate a natural, polite, and professional email reply strictly following the provided instructions. "
                            "Output ONLY the final email body. Do not include subject lines, conversational commentary, or placeholder brackets like [Name]."
                        ),
                    },
                    {
                        "role": "user",
                        "content": prompt,
                    },
                ],
                model=target_model,
                temperature=0.7,
                max_tokens=1024,
            )

            reply = chat_completion.choices[0].message.content
            if reply and reply.strip():
                print(f"Groq Cloud API ({target_model}) completed successfully.")
                return reply.strip()

        except Exception as err:
            print(f"Groq model {target_model} failed: {err}")
            last_error = err

    raise RuntimeError(f"All Groq models failed. Last error: {last_error}") from last_error
