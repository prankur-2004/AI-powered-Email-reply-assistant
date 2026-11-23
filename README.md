# 🤖 AI-Powered Email Reply Assistant

> An intelligent, full-stack email automation system that connects directly to real mailboxes (Gmail, Outlook, Yahoo, iCloud, Custom IMAP), parses and sanitizes email threads, performs semantic NLP analysis (Intent, Sentiment, Urgency), and synthesizes context-aware, personalized replies using Retrieval-Augmented Generation (RAG).

---

## 🌟 Key Features

- **⚡ Universal Mailbox Integration (IMAP)**: Connects to Gmail (via App Password), Microsoft Outlook / Office 365, Yahoo Mail, iCloud, or any custom IMAP server. Automatically imports and deduplicates emails.
- **🔍 Semantic NLP Understanding**: Extracts structured parameters from incoming emails:
  - **Intent Classification** (Meeting, Inquiry, Update, Request, Escalation)
  - **Sentiment Detection** (Positive, Neutral, Negative, Urgent)
  - **Urgency Scoring** (High, Normal, Low)
  - **Executive Summarization** (2-line digest of long email threads)
- **🧠 Retrieval-Augmented Generation (RAG)**: Dynamically retrieves relevant personal knowledge (user background, scheduling rules, FAQs) via vector embeddings and cosine similarity to synthesize highly personalized replies.
- **🛡️ Anti-Hallucination Guardrails**: Response validation engine ensures zero placeholder leaks (e.g., `[Name]`, `[Insert Date]`) and guarantees context continuity across multi-turn threads.
- **🔒 Privacy-First Hybrid AI**: Supports Google Gemini API, local private models (Ollama / LLaMA 3.2), and a built-in zero-dependency local AI server for 100% offline self-hosting.

---

## 🛠️ Tech Stack

| Layer | Technologies |
| :--- | :--- |
| **Frontend** | React 19, Vite, Tailwind CSS v4, Axios (JWT auto-refresh interceptors) |
| **Backend API** | Python 3.10+, Django 5+, Django REST Framework (DRF), SimpleJWT |
| **Email Protocol** | Python `imaplib` (IMAP4 over SSL), RFC 2047 MIME Header decoding, HTML sanitizer |
| **AI / NLP** | OpenAI-compatible API (`/v1/chat/completions`), Cosine Similarity Vector Search |
| **Database** | SQLite (Development) / PostgreSQL (Production ready) |

---

## 🚀 Quick Start

### 1. One-Click Launch (Windows)
Double-click [`run.bat`](file:///run.bat) or run in PowerShell:
```powershell
.\run.ps1
```
This automatically boots:
- **Local AI Server**: `http://127.0.0.1:8001`
- **Django REST Backend**: `http://127.0.0.1:8000`
- **React UI**: `http://localhost:5173`
- Automatically opens **http://localhost:5173** in your default browser!

---

### 2. Manual Setup

#### Backend Setup
```bash
cd backend
python -m venv ..\.venv
..\.venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver 8000
```

#### Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

---

## 📡 Core API Endpoints

- `POST /api/auth/register/` - Create a new user account
- `POST /api/auth/login/` - Authenticate & obtain JWT access + refresh tokens
- `GET/POST /api/auth/emails/` - List user emails or create manual email
- `POST /api/auth/emails/<id>/analyze/` - Analyze email semantics (Intent, Sentiment, Urgency)
- `POST /api/auth/emails/<id>/reply/` - Generate context-aware personalized AI reply
- `GET/POST /api/auth/email-accounts/` - List & connect real email accounts via IMAP
- `POST /api/auth/email-accounts/sync/` - Fetch recent emails from connected inbox with auto-analysis

---

## 📄 License
This project is open-source and available under the [MIT License](LICENSE).
