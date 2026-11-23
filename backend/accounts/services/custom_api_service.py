import os
import re
import json
import requests
from dotenv import load_dotenv

load_dotenv()


def is_custom_api_configured():
    """
    Check if a custom API base URL is configured in the environment.
    """
    load_dotenv()
    url = os.getenv("CUSTOM_API_BASE_URL", "").strip()
    return bool(url)


def get_custom_api_config():
    """
    Retrieve custom API configuration from environment variables.
    """
    load_dotenv()
    base_url = os.getenv("CUSTOM_API_BASE_URL", "http://localhost:11434/v1").strip().rstrip("/")
    api_key = os.getenv("CUSTOM_API_KEY", "").strip()
    model = os.getenv("CUSTOM_API_MODEL", "llama3.2").strip()
    timeout = int(os.getenv("CUSTOM_API_TIMEOUT", "60").strip() or "60")
    embedding_model = os.getenv("CUSTOM_EMBEDDING_MODEL", "nomic-embed-text").strip()

    return {
        "base_url": base_url,
        "api_key": api_key,
        "model": model,
        "timeout": timeout,
        "embedding_model": embedding_model,
    }


def call_custom_api(prompt, model=None, system_prompt=None, temperature=0.7, max_tokens=1024):
    """
    Generate an email reply using your own custom API endpoint.
    Supports any OpenAI-compatible server (e.g. Ollama, vLLM, LM Studio, LocalAI, or custom FastAPI/Flask).
    """
    config = get_custom_api_config()
    base_url = config["base_url"]
    api_key = config["api_key"]
    target_model = model or config["model"]
    timeout = config["timeout"]

    if not base_url:
        raise ValueError(
            "CUSTOM_API_BASE_URL is not set in backend/.env. "
            "Please specify your custom API endpoint (e.g. http://localhost:11434/v1)."
        )

    if system_prompt is None:
        system_prompt = (
            "You are an AI-powered personalized email reply assistant. "
            "Generate a natural, polite, and professional email reply strictly following the provided instructions. "
            "Output ONLY the final email body. Do not include subject lines, conversational commentary, or placeholder brackets like [Name]."
        )

    headers = {
        "Content-Type": "application/json",
    }
    if api_key and api_key != "not-needed-for-local":
        headers["Authorization"] = f"Bearer {api_key}"

    # Determine endpoints to attempt:
    # 1. Standard OpenAI-compatible: <base_url>/chat/completions
    # 2. Native Ollama format: <base_url>/api/chat (if base_url points to port 11434 without /v1)
    chat_endpoints = []
    if base_url.endswith("/v1"):
        chat_endpoints.append(f"{base_url}/chat/completions")
    else:
        chat_endpoints.append(f"{base_url}/v1/chat/completions")
        chat_endpoints.append(f"{base_url}/chat/completions")
        chat_endpoints.append(f"{base_url}/api/chat")

    # Add local custom AI server (port 8001) as automatic fallback if primary is offline
    local_fallback = "http://127.0.0.1:8001/v1/chat/completions"
    if local_fallback not in chat_endpoints:
        chat_endpoints.append(local_fallback)

    payload = {
        "model": target_model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt},
        ],
        "temperature": temperature,
        "max_tokens": max_tokens,
        "stream": False,
    }

    print("========================================")
    print("Calling Custom API...")
    print(f"Base URL: {base_url}")
    print(f"Model: {target_model}")
    print("========================================")

    last_error = None
    for endpoint in chat_endpoints:
        try:
            # Handle native Ollama /api/chat difference if needed
            if endpoint.endswith("/api/chat"):
                ollama_payload = {
                    "model": target_model,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": prompt},
                    ],
                    "stream": False,
                    "options": {
                        "temperature": temperature,
                        "num_predict": max_tokens,
                    },
                }
                res = requests.post(endpoint, json=ollama_payload, headers=headers, timeout=timeout)
            else:
                res = requests.post(endpoint, json=payload, headers=headers, timeout=timeout)

            if res.status_code == 404:
                # Try next endpoint candidate
                last_error = f"HTTP 404 Not Found at {endpoint}"
                continue

            res.raise_for_status()
            data = res.json()

            # Parse standard OpenAI format: choices[0].message.content
            if "choices" in data and len(data["choices"]) > 0:
                choice = data["choices"][0]
                reply = ""
                if "message" in choice and isinstance(choice["message"], dict):
                    reply = choice["message"].get("content", "")
                elif "text" in choice:
                    reply = choice.get("text", "")

                if reply and reply.strip():
                    print(f"Custom API ({target_model}) completed successfully.")
                    return reply.strip()

            # Parse native Ollama format: message.content
            if "message" in data and isinstance(data["message"], dict):
                reply = data["message"].get("content", "")
                if reply and reply.strip():
                    print(f"Custom API [Ollama] ({target_model}) completed successfully.")
                    return reply.strip()

            # Parse custom simple format: {"reply": "..."} or {"output": "..."}
            for field in ("reply", "output", "text", "response"):
                if field in data and isinstance(data[field], str) and data[field].strip():
                    print(f"Custom API [direct] ({target_model}) completed successfully.")
                    return data[field].strip()

            raise RuntimeError(f"Unexpected response format from custom API: {data}")

        except requests.exceptions.ConnectionError as conn_err:
            last_error = (
                f"Could not connect to custom API at '{endpoint}'. "
                f"Ensure your local API server (e.g. Ollama, LM Studio, or custom server) is running. Error: {conn_err}"
            )
        except requests.exceptions.Timeout as time_err:
            last_error = f"Request to custom API timed out after {timeout} seconds: {time_err}"
        except Exception as err:
            last_error = f"Custom API call failed on {endpoint}: {err}"

    raise RuntimeError(f"Custom API generation failed: {last_error}")


def generate_custom_embedding(text, model=None):
    """
    Generate vector embeddings using the custom API endpoint (/v1/embeddings).
    Compatible with Ollama, LocalAI, vLLM, and standard embedding servers.
    """
    if not text or not text.strip():
        return []

    config = get_custom_api_config()
    base_url = config["base_url"]
    api_key = config["api_key"]
    embedding_model = model or config["embedding_model"]
    timeout = config["timeout"]

    headers = {
        "Content-Type": "application/json",
    }
    if api_key and api_key != "not-needed-for-local":
        headers["Authorization"] = f"Bearer {api_key}"

    endpoints = []
    if base_url.endswith("/v1"):
        endpoints.append(f"{base_url}/embeddings")
    else:
        endpoints.append(f"{base_url}/v1/embeddings")
        endpoints.append(f"{base_url}/embeddings")
        endpoints.append(f"{base_url}/api/embeddings")

    payload = {
        "model": embedding_model,
        "input": text,
    }

    for endpoint in endpoints:
        try:
            if endpoint.endswith("/api/embeddings"):
                ollama_payload = {
                    "model": embedding_model,
                    "prompt": text,
                }
                res = requests.post(endpoint, json=ollama_payload, headers=headers, timeout=timeout)
                if res.status_code == 200:
                    data = res.json()
                    if "embedding" in data:
                        return data["embedding"]
            else:
                res = requests.post(endpoint, json=payload, headers=headers, timeout=timeout)
                if res.status_code == 200:
                    data = res.json()
                    if "data" in data and len(data["data"]) > 0:
                        return data["data"][0].get("embedding", [])

        except Exception:
            continue

    return []
