# Custom AI API Setup Guide

This project is now configured to use **your own custom AI API endpoint** exclusively, removing any third-party external dependencies (Groq, Gemini cloud, etc.).

---

## 1. Quick Configuration in `backend/.env`

Open [backend/.env](file:///c:/Users/prank/OneDrive/Pictures/project/AI-Powered%20Email%20Reply%20Assistant%20%282%29/AI-Powered%20Email%20Reply%20Assistant/backend/.env) and configure:

```env
# URL of your API server (OpenAI-compatible format)
CUSTOM_API_BASE_URL=http://localhost:11434/v1

# Optional API key (if your server requires authentication)
CUSTOM_API_KEY=not-needed-for-local

# The model name hosted on your server
CUSTOM_API_MODEL=llama3.2

# Request timeout in seconds
CUSTOM_API_TIMEOUT=60

# Optional embedding model for RAG
CUSTOM_EMBEDDING_MODEL=nomic-embed-text
```

---

## 2. Supported Custom API Providers

Any OpenAI-compatible `/v1/chat/completions` server is supported out of the box:

### Option A: Ollama (Recommended for Local LLMs)
1. Install [Ollama](https://ollama.com).
2. Pull your desired model:
   ```bash
   ollama run llama3.2
   ```
3. Set in `backend/.env`:
   ```env
   CUSTOM_API_BASE_URL=http://localhost:11434/v1
   CUSTOM_API_MODEL=llama3.2
   ```

### Option B: LM Studio
1. Start LM Studio and load any open-source GGUF model.
2. Click the **Local Server** tab (double-arrow icon) and press **Start Server** (default: `http://localhost:1234`).
3. Set in `backend/.env`:
   ```env
   CUSTOM_API_BASE_URL=http://localhost:1234/v1
   CUSTOM_API_MODEL=local-model
   ```

### Option C: Built-in Standalone Local Server
If you don't have Ollama or LM Studio installed yet, this project includes a built-in zero-dependency local AI server:
1. Run in terminal:
   ```bash
   python custom_ai_server.py --port 8001
   ```
2. Set in `backend/.env`:
   ```env
   CUSTOM_API_BASE_URL=http://127.0.0.1:8001/v1
   CUSTOM_API_MODEL=custom-email-assistant
   ```

### Option D: vLLM / LocalAI / Custom FastAPI
Run your custom server with any IP or port, and set `CUSTOM_API_BASE_URL=http://<host>:<port>/v1`.

---

## 3. Testing Your Custom API

Run the verification script from the `backend/` directory:

```powershell
..\.venv\Scripts\python.exe -m accounts.services.test_custom_api
```

This will test:
1. Endpoint connectivity.
2. Chat completion reply generation with system prompt and user preferences.
3. Proper formatting and validation of the returned email.
