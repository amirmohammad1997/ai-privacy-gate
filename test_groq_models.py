"""List available Groq models."""
import asyncio
import os
from dotenv import load_dotenv
load_dotenv()

import httpx


async def main():
    api_key = os.getenv("LLM_API_KEY")
    base_url = os.getenv("LLM_BASE_URL")

    print("=" * 70)
    print("Available Groq Models")
    print("=" * 70)
    print()

    async with httpx.AsyncClient(timeout=15.0) as client:
        try:
            res = await client.get(
                f"{base_url}/models",
                headers={"Authorization": f"Bearer {api_key}"},
            )
            res.raise_for_status()
            data = res.json()

            models = data.get("data", [])
            print(f"Found {len(models)} models:\n")

            for m in sorted(models, key=lambda x: x.get("id", "")):
                model_id = m.get("id", "?")
                owned_by = m.get("owned_by", "?")
                active = m.get("active", True)

                status = "✅" if active else "❌"
                print(f"  {status} {model_id:50} ({owned_by})")

            print()
            print("=" * 70)
            print("Recommended for our project:")
            print("=" * 70)

            # Filter for Llama models
            recommended = [
                m["id"] for m in models
                if "llama" in m["id"].lower()
                and m.get("active", True)
            ]

            for r in recommended[:5]:
                print(f"  → {r}")

        except httpx.HTTPStatusError as e:
            print(f"❌ HTTP {e.response.status_code}: {e.response.text[:300]}")
        except Exception as e:
            print(f"❌ {type(e).__name__}: {e}")


if __name__ == "__main__":
    asyncio.run(main())