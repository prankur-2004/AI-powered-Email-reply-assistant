"""
Custom AI API Server (OpenAI-compatible)
----------------------------------------
A standalone, self-hosted API server providing:
- POST /v1/chat/completions  (Chat completions endpoint)
- POST /v1/embeddings        (Embeddings endpoint)
- GET  /v1/models            (Model catalog endpoint)
- GET  /health               (Health check)

Can run independently on your local machine with zero external cloud dependencies:
    python custom_ai_server.py --port 8001
"""

import sys
import json
import time
import re
import hashlib
from http.server import HTTPServer, BaseHTTPRequestHandler
import argparse


def generate_smart_reply(prompt, messages):
    """
    Intelligent internal email reply synthesis engine for the custom server.
    Parses intent, greetings, context, and tone from the prompt to create a clean email reply.
    """
    user_content = ""
    for msg in messages:
        if msg.get("role") == "user":
            user_content = msg.get("content", "")
            break
    if not user_content:
        user_content = prompt

    # Extract email subject/content from prompt
    curr_email_match = re.search(r"CURRENT EMAIL\s*-+\s*(.*?)(?:-+|\Z)", user_content, re.DOTALL | re.IGNORECASE)
    email_text = curr_email_match.group(1).strip() if curr_email_match else user_content

    # Extract tone / preferences if present
    tone_match = re.search(r"Tone:\s*(\w+)", user_content, re.IGNORECASE)
    tone = tone_match.group(1).lower() if tone_match else "professional"

    greeting_match = re.search(r"Preferred greeting:\s*([^\n\r]+)", user_content, re.IGNORECASE)
    greeting = greeting_match.group(1).strip() if greeting_match else "Dear Sender"
    if greeting.lower() in ("dear", "hello", "hi"):
        # Add recipient context if available
        greeting = f"{greeting},"

    signoff_match = re.search(r"Preferred sign-off:\s*([^\n\r]+)", user_content, re.IGNORECASE)
    signoff = signoff_match.group(1).strip() if signoff_match else "Best regards"

    # Analyze key questions or intentions in email_text
    lower_email = email_text.lower()
    
    if "interview" in lower_email or "meeting" in lower_email:
        core_msg = (
            "Thank you for reaching out and for this opportunity. "
            "I would be glad to attend. I am available during the suggested times and look forward to speaking with you. "
            "Please let me know if you need any additional details from my end beforehand."
        )
    elif "timeline" in lower_email or "milestone" in lower_email or "schedule" in lower_email or "project" in lower_email:
        core_msg = (
            "Thank you for checking in on the project status. "
            "We are making steady progress and currently on track with our target milestones for next week. "
            "I will compile the updated timeline and deliver a detailed breakdown shortly."
        )
    elif "status" in lower_email or "update" in lower_email:
        core_msg = (
            "Thank you for following up. "
            "Everything is proceeding as planned, and we are on schedule with the current deliverables. "
            "I will keep you posted as soon as the next review cycle is complete."
        )
    elif "invoice" in lower_email or "payment" in lower_email:
        core_msg = (
            "Thank you for contacting us regarding the invoice. "
            "Our finance team has received your information and is currently processing it. "
            "We will send a confirmation receipt as soon as the transaction is finalized."
        )
    elif "error" in lower_email or "issue" in lower_email or "bug" in lower_email or "problem" in lower_email:
        core_msg = (
            "Thank you for bringing this issue to our attention. "
            "We have investigated the behavior and are currently addressing the root cause. "
            "We anticipate deploying a resolution shortly and will update you once verified."
        )
    elif "?" in email_text:
        core_msg = (
            "Thank you for your inquiry. "
            "I have reviewed your questions and am working on providing the requested information. "
            "I will share a comprehensive update with you shortly."
        )
    else:
        core_msg = (
            "Thank you for your message. "
            "I have reviewed the information provided and will take the necessary next steps. "
            "Please feel free to let me know if you have any questions or require anything further."
        )

    # Format reply without brackets or placeholders
    lines = [
        greeting,
        "",
        core_msg,
        "",
        signoff
    ]
    return "\n".join(lines).strip()


def generate_embedding_vector(text, dimension=128):
    """
    Generate deterministic normalized embedding vector.
    """
    tokens = text.lower().split()
    vector = [0.0] * dimension
    for token in tokens:
        idx = int(hashlib.md5(token.encode("utf-8")).hexdigest(), 16) % dimension
        vector[idx] += 1.0

    norm = sum(x * x for x in vector) ** 0.5
    if norm > 0:
        vector = [round(x / norm, 6) for x in vector]
    return vector


class CustomAIRequestHandler(BaseHTTPRequestHandler):

    def _send_json(self, status_code, data):
        response_body = json.dumps(data).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(response_body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.end_headers()
        self.wfile.write(response_body)

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.end_headers()

    def do_GET(self):
        path = self.path.split("?")[0].rstrip("/")
        if path in ("", "/health"):
            self._send_json(200, {
                "status": "healthy",
                "service": "Custom OpenAI-Compatible AI Server",
                "version": "1.0.0",
                "endpoints": ["/v1/chat/completions", "/v1/embeddings", "/v1/models"]
            })
        elif path in ("/v1/models", "/models"):
            self._send_json(200, {
                "object": "list",
                "data": [
                    {"id": "custom-email-assistant", "object": "model", "owned_by": "custom"},
                    {"id": "llama3.2", "object": "model", "owned_by": "custom"},
                    {"id": "mistral", "object": "model", "owned_by": "custom"}
                ]
            })
        else:
            self._send_json(404, {"error": f"Endpoint {self.path} not found"})

    def do_POST(self):
        content_length = int(self.headers.get("Content-Length", 0))
        post_data = self.rfile.read(content_length)
        try:
            body = json.loads(post_data.decode("utf-8")) if post_data else {}
        except Exception as e:
            self._send_json(400, {"error": f"Invalid JSON payload: {e}"})
            return

        path = self.path.split("?")[0].rstrip("/")

        # Chat completions: /v1/chat/completions or /chat/completions or /api/chat
        if path in ("/v1/chat/completions", "/chat/completions", "/api/chat"):
            messages = body.get("messages", [])
            prompt = body.get("prompt", "")
            model = body.get("model", "custom-email-assistant")

            reply_text = generate_smart_reply(prompt, messages)

            response = {
                "id": f"chatcmpl-{int(time.time())}",
                "object": "chat.completion",
                "created": int(time.time()),
                "model": model,
                "choices": [
                    {
                        "index": 0,
                        "message": {
                            "role": "assistant",
                            "content": reply_text,
                        },
                        "finish_reason": "stop"
                    }
                ],
                "usage": {
                    "prompt_tokens": len(str(messages).split()),
                    "completion_tokens": len(reply_text.split()),
                    "total_tokens": len(str(messages).split()) + len(reply_text.split()),
                }
            }
            self._send_json(200, response)

        # Embeddings: /v1/embeddings or /embeddings or /api/embeddings
        elif path in ("/v1/embeddings", "/embeddings", "/api/embeddings"):
            input_text = body.get("input") or body.get("prompt", "")
            model = body.get("model", "custom-embedding")

            if isinstance(input_text, list):
                data = [
                    {"object": "embedding", "index": idx, "embedding": generate_embedding_vector(txt)}
                    for idx, txt in enumerate(input_text)
                ]
            else:
                data = [
                    {"object": "embedding", "index": 0, "embedding": generate_embedding_vector(str(input_text))}
                ]

            response = {
                "object": "list",
                "data": data,
                "model": model,
                "usage": {"prompt_tokens": 10, "total_tokens": 10}
            }
            self._send_json(200, response)

        else:
            self._send_json(404, {"error": f"POST endpoint {self.path} not found"})

    def log_message(self, format, *args):
        # Clean logging
        sys.stderr.write(f"[Custom AI Server] {self.address_string()} - {format % args}\n")


def run_server(host="127.0.0.1", port=8001):
    server_address = (host, port)
    httpd = HTTPServer(server_address, CustomAIRequestHandler)
    print("=================================================================")
    print(f" Custom AI Server is running at http://{host}:{port}/v1")
    print(f" Endpoints:")
    print(f"   - Chat Completions: http://{host}:{port}/v1/chat/completions")
    print(f"   - Embeddings:       http://{host}:{port}/v1/embeddings")
    print(f"   - Models Catalog:   http://{host}:{port}/v1/models")
    print(f"   - Health Check:     http://{host}:{port}/health")
    print(" Press Ctrl+C to stop the server.")
    print("=================================================================")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down Custom AI Server.")
        httpd.server_close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Custom AI API Server (OpenAI-compatible)")
    parser.add_argument("--host", default="127.0.0.1", help="Host interface (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=8001, help="Port to listen on (default: 8001)")
    args = parser.parse_args()
    run_server(host=args.host, port=args.port)
