"""
Test multiple LLM providers to find which one works from your network.

Run: python test_llm_providers.py
"""
import asyncio
import os
from dotenv import load_dotenv
load_dotenv()

import httpx


# ═══════════════════════════════════════════════════════════
# Providers to test
# ═══════════════════════════════════════════════════════════

PROVIDERS = [
    {
        "name": "Ollama (local)",
        "base_url": "http://localhost:11434/v1",
        "api_key": "ollama",
        "model": "llama3.2:1b",
        "needs_key": False,
    },
    {
        "name": "Together.ai",
        "base_url": "https://api.together.xyz/v1",
        "api_key": os.getenv("TOGETHER_API_KEY", ""),
        "model": "meta-llama/Llama-3.3-70B-Instruct-Turbo",
        "needs_key": True,
    },
    {
        "name": "OpenRouter",
        "base_url": "https://openrouter.ai/api/v1",
        "api_key": os.getenv("OPENROUTER_API_KEY", ""),
        "model": "meta-llama/llama-3.2-3b-instruct:free",
        "needs_key": True,
    },
    {
        "name": "HuggingFace",
        "base_url": "https://api-inference.huggingface.co/v1",
        "api_key": os.getenv("HF_TOKEN", ""),
        "model": "meta-llama/Llama-3.2-3B-Instruct",
        "needs_key": True,
    },
    {
        "name": "Groq",
        "base_url": "https://api.groq.com/openai/v1",
        "api_key": os.getenv("GROQ_API_KEY", ""),
        "model": "llama-3.1-8b-instant",
        "needs_key": True,
    },
]


# ═══════════════════════════════════════════════════════════

async def test_provider(provider: dict) -> dict:
    """Test a single provider."""
    name = provider["name"]
    base_url = provider["base_url"]
    api_key = provider["api_key"]
    model = provider["model"]

    result = {
        "name": name,
        "status": "unknown",
        "message": "",
        "response": "",
    }

    # Check if key is needed
    if provider["needs_key"] and not api_key:
        result["status"] = "skipped"
        result["message"] = "No API key configured"
        return result

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            res = await client.post(
                f"{base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": model,
                    "messages": [
                        {"role": "user", "content": "Say 'ok' only"}
                    ],
                    "max_tokens": 10,
                },
            )

            if res.status_code == 200:
                data = res.json()
                response = data["choices"][0]["message"]["content"]
                result["status"] = "✅ OK"
                result["response"] = response[:80]
                return result

            if res.status_code == 401:
                result["status"] = "❌ Auth"
                result["message"] = "Invalid API key"
                return result

            if res.status_code == 403:
                result["status"] = "❌ Forbidden"
                result["message"] = "Geo-blocked or blocked"
                return result

            if res.status_code == 404:
                result["status"] = "❌ Model"
                result["message"] = f"Model not found: {model}"
                return result

            if res.status_code == 429:
                result["status"] = "⚠️ Rate limit"
                result["message"] = "Too many requests"
                return result

            result["status"] = f"❌ {res.status_code}"
            result["message"] = res.text[:100]
            return result

    except httpx.ConnectError as e:
        result["status"] = "❌ No connection"
        result["message"] = f"Cannot reach {base_url}"
        return result

    except httpx.TimeoutException:
        result["status"] = "❌ Timeout"
        result["message"] = "Request timed out"
        return result

    except Exception as e:
        result["status"] = "❌ Error"
        result["message"] = f"{type(e).__name__}: {str(e)[:100]}"
        return result


# ═══════════════════════════════════════════════════════════

async def main():
    print("=" * 78)
    print("LLM Provider Test — Which one works for you?")
    print("=" * 78)

    # Show environment variables
    print("\n📋 Environment variables:")
    print(f"  TOGETHER_API_KEY:   {'✅' if os.getenv('TOGETHER_API_KEY') else '❌ not set'}")
    print(f"  OPENROUTER_API_KEY: {'✅' if os.getenv('OPENROUTER_API_KEY') else '❌ not set'}")
    print(f"  HF_TOKEN:           {'✅' if os.getenv('HF_TOKEN') else '❌ not set'}")
    print(f"  GROQ_API_KEY:       {'✅' if os.getenv('GROQ_API_KEY') else '❌ not set'}")

    print("\n" + "─" * 78)
    print("Testing providers...")
    print("─" * 78)

    # Test all providers in parallel
    tasks = [test_provider(p) for p in PROVIDERS]
    results = await asyncio.gather(*tasks)

    # Print results
    print()
    for r in results:
        print(f"{r['status']:20} {r['name']}")
        if r["message"]:
            print(f"{'':20} → {r['message']}")
        if r["response"]:
            print(f"{'':20} → Response: {r['response']}")

    # Summary
    print("\n" + "=" * 78)
    working = [r for r in results if "✅" in r["status"]]
    if working:
        print(f"✅ Working providers: {', '.join(r['name'] for r in working)}")
        print("\n👉 Use this in .env:")
        # Find first working
        for r in working:
            provider = next(p for p in PROVIDERS if p["name"] == r["name"])
            print(f"   LLM_BASE_URL={provider['base_url']}")
            print(f"   LLM_MODEL={provider['model']}")
            break
    else:
        print("❌ No working providers found")
        print("\n👉 Recommended next steps:")
        print("   1. Install Ollama (local, works offline)")
        print("   2. Get API key from Together.ai (https://api.together.xyz)")
        print("   3. Get API key from OpenRouter (https://openrouter.ai)")

    print("=" * 78)


if __name__ == "__main__":
    asyncio.run(main())