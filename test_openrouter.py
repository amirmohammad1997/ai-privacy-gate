"""Test OpenRouter API directly."""
import asyncio
import os
from dotenv import load_dotenv
load_dotenv()

import httpx


async def main():
    api_key = os.getenv("LLM_API_KEY")
    base_url = os.getenv("LLM_BASE_URL")
    model = os.getenv("LLM_MODEL")

    print("=" * 70)
    print("OpenRouter Direct Test")
    print("=" * 70)
    print()
    print(f"API Key:  {api_key[:25]}..." if api_key else "API Key:  NOT SET")
    print(f"Base URL: {base_url}")
    print(f"Model:    {model}")
    print()

    if not api_key or not api_key.startswith("sk-or-"):
        print("❌ Invalid API key format")
        print("   OpenRouter keys start with 'sk-or-v1-'")
        return

    url = f"{base_url}/chat/completions"
    print(f"Testing URL: {url}")
    print()

    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            res = await client.post(
                url,
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "http://localhost:8000",
                    "X-Title": "AI Privacy Gateway",
                },
                json={
                    "model": model,
                    "messages": [
                        {"role": "user", "content": "Say 'hello' only"}
                    ],
                    "max_tokens": 20,
                },
            )

            print(f"Status: {res.status_code}")
            print()

            if res.status_code == 200:
                data = res.json()
                content = data["choices"][0]["message"]["content"]
                print(f"✅ SUCCESS")
                print(f"   Response: {content}")
                print(f"   Model used: {data.get('model', 'unknown')}")
                if "usage" in data:
                    print(f"   Tokens: {data['usage']}")

            else:
                print(f"❌ FAILED")
                print(f"   Body: {res.text[:500]}")

        except httpx.ConnectError as e:
            print(f"❌ Cannot connect: {e}")
            print("   → Check internet or firewall")

        except httpx.TimeoutException:
            print("❌ Timeout — OpenRouter may be slow")

        except Exception as e:
            print(f"❌ {type(e).__name__}: {e}")


if __name__ == "__main__":
    asyncio.run(main())