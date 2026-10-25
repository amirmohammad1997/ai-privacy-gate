# 🛡️ AI Privacy Gateway

Privacy-preserving middleware between users and LLMs.

## 🎯 What It Does

* **Anonymizes PII** before sending to LLM (names, emails, phones, etc.)
* **Blocks prompt injection** attempts
* **Filters output** for leaked API keys and sensitive data
* **Restores original values** in the response, seamlessly

## 🚀 Quick Start (Development)

```bash
# Clone or create project
cd ai-privacy-gateway

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment template
cp .env.example .env

# Run server
uvicorn app.main:app --reload
# 🛡️ AI Privacy Gateway



A privacy-preserving middleware between users and LLMs.

Automatically detects, anonymizes, and restores Personal Identifiable Information (PII) in real-time.



\## ✨ Features



\### 🌍 Multi-Language PII Detection (12 Languages)

\- \*\*Universal:\*\* Email, URL, IP address, credit cards (Luhn), IBAN, MAC

\- \*\*English:\*\* SSN, US phone numbers, ZIP codes

\- \*\*Persian:\*\* کد ملی (checksum), mobile, postal code, passport

\- \*\*Turkish:\*\* TCKN, mobile phone

\- \*\*Chinese:\*\* 身份证 (checksum), mobile

\- \*\*Japanese:\*\* My Number, phone

\- \*\*Korean:\*\* RRN, phone

\- \*\*Arabic:\*\* Saudi/Egypt/UAE National IDs, mobile

\- \*\*Spanish:\*\* DNI, NIE, phone

\- \*\*French:\*\* INSEE, phone

\- \*\*German:\*\* Steuer-ID, phone

\- \*\*Portuguese:\*\* CPF, CNPJ, phone

\- \*\*Russian:\*\* SNILS, INN, phone



\### 🛡️ Prompt Guard (Anti-Injection)

\- \*\*Pattern Layer:\*\* 17+ regex patterns for known attacks

\- \*\*Embedding Layer:\*\* Semantic similarity detection (all-MiniLM-L6-v2)

\- \*\*Normalizer:\*\* Unicode, homoglyph, base64, leet speak bypass prevention



\### 🚫 Output Filter (Anti-Leakage)

\- \*\*Secrets Detector:\*\* OpenAI, AWS, GitHub, Stripe, Slack, JWT, private keys

\- \*\*Entropy Analyzer:\*\* Detects unknown high-entropy secrets

\- \*\*PII Re-detection:\*\* Catches leaks in LLM responses



\### 🤖 LLM Support

\- \*\*Ollama\*\* (local, free — recommended for development)

\- \*\*Together.ai\*\*

\- \*\*OpenRouter\*\*

\- \*\*Groq\*\*

\- \*\*OpenAI\*\*

\- Any OpenAI-compatible API



\## 🚀 Quick Start



\### Prerequisites

\- Python 3.12 or 3.13

\- Git

\- Optional: Docker (for later steps)

\- Optional: Ollama (for local LLM)



\### 1. Install

```bash

git clone https://github.com/YOUR-USERNAME/ai-privacy-gateway.git

cd ai-privacy-gateway

python -m venv .venv

.venv\\Scripts\\activate  # Windows

pip install -r requirements.txt

python -m spacy download en\_core\_web\_sm

