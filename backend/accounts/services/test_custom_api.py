import sys
import os

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from .custom_api_service import call_custom_api, is_custom_api_configured, get_custom_api_config
from .gemini_service import generate_email_reply


def main():
    print("==================================================")
    print("      Testing Custom AI API Integration           ")
    print("==================================================")

    config = get_custom_api_config()
    print(f"Is Custom API Configured: {is_custom_api_configured()}")
    print(f"Base URL:                 {config['base_url']}")
    print(f"Model:                    {config['model']}")
    print(f"Timeout:                  {config['timeout']}s")
    print("--------------------------------------------------")

    sample_email = """
Hi Alex,

We were impressed by your resume and would like to invite you for a 30-minute technical interview this Thursday or Friday.
Please let us know which time works best for your schedule.

Best regards,
Sarah Jenkins
Tech Recruiting Team
"""

    print("Sending prompt to your custom API...")
    try:
        reply = generate_email_reply(
            email_text=sample_email,
            intent="meeting",
            sentiment="positive",
            urgency="normal",
            topic="interview",
            summary="Technical interview invitation and availability request."
        )

        print("\nGenerated Reply from Your Custom API:")
        print("-------------------------------------")
        print(reply)
        print("-------------------------------------")
        print("\nSUCCESS: Your custom API is working properly!")

    except Exception as e:
        print(f"\nCustom API Generation Failed: {e}")
        print("\nTroubleshooting Tips:")
        print("1. If using Ollama: ensure `ollama serve` is running and `ollama run <model>` is available.")
        print("2. If using LM Studio / vLLM: ensure the local server is started on the port in .env.")
        print("3. If using the built-in server: run `python custom_ai_server.py` in a terminal.")
        sys.exit(1)


if __name__ == "__main__":
    main()
