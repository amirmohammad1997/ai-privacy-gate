"""Test Groq API directly."""
import asyncio
import os
from dotenv import load_dotenv
load_dotenv()

import httpx


async def main():
    api_key = os.getenv("LLM_API_KEY")
    base_url = os.getenv("LLM_BASE_URL")
    model = os.getenv("LLM_MODEL")

    print("=" * 60)
    print("Groq API Direct Test")
    print("=" * 60)
    print(f"\nAPI Key: {api_key[:20]}..." if api_key else "API Key: NOT SET")
    print(f"Base URL: {base_url}")
    print(f"Model: {model}")
    print()

    url = f"{base_url}/chat/completions"
    print(f"Testing URL: {url}")
    print()

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            res = await client.post(
                url,
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": model,
                    "messages": [{"role": "user", "content": "Say 'hello' only"}],
                    "max_tokens": 50,
                },
            )
            print(f"Status: {res.status_code}")
            print(f"Response:")
            print(res.text[:500])

        except httpx.HTTPStatusError as e:
            print(f"❌ HTTP Error: {e.response.status_code}")
            print(f"   Body: {e.response.text[:500]}")

        except httpx.ConnectError as e:
            print(f"❌ Connect Error: {e}")
            print("   → Cannot reach api.groq.com")
            print("   → Check internet or firewall")

        except httpx.TimeoutException as e:
            print(f"❌ Timeout: {e}")
            print("   → Request took too long")

        except Exception as e:
            print(f"❌ {type(e).__name__}: {e}")


if __name__ == "__main__":
    asyncio.run(main())