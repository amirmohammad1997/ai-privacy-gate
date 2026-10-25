"""
LLM client — abstraction over OpenAI, Anthropic, etc.
"""
import logging
from typing import Optional

import httpx

from app.config import settings

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════
# LLM Client
# ═══════════════════════════════════════════════════════════

class LLMClient:
    """
    Client for LLM providers.

    Supports OpenAI-compatible APIs (OpenAI, Azure, local, etc.).
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        timeout: float = 60.0,
    ):
        self.api_key = api_key or settings.LLM_API_KEY
        self.base_url = (base_url or settings.LLM_BASE_URL).rstrip("/")
        self.model = model or settings.LLM_MODEL
        self.timeout = timeout

        self._client: Optional[httpx.AsyncClient] = None

    # ═══════════════════════════════════════════════════════

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(
                timeout=self.timeout,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
            )
        return self._client

    async def close(self):
        if self._client:
            await self._client.aclose()
            self._client = None

    # ═══════════════════════════════════════════════════════

    async def chat(
        self,
        message: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
    ) -> str:
        """
        Send a chat message and get response.

        Args:
            message: User message
            system_prompt: Optional system prompt
            temperature: Sampling temperature
            max_tokens: Max response tokens

        Returns:
            LLM response text
        """
        if not self.api_key:
            return (
                "⚠️ LLM API key not configured. "
                "Set LLM_API_KEY in .env to enable real responses."
            )

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": message})

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        try:
            client = await self._get_client()
            res = await client.post(
                f"{self.base_url}/chat/completions",
                json=payload,
            )
            res.raise_for_status()
            data = res.json()

            return data["choices"][0]["message"]["content"]

        except httpx.HTTPStatusError as e:
            logger.error(
                f"LLM API error: {e.response.status_code} — {e.response.text[:200]}"
            )
            return f"⚠️ LLM API error: {e.response.status_code}"

        except httpx.RequestError as e:
            logger.error(f"LLM network error: {e}")
            return "⚠️ LLM network error"

        except Exception as e:
            logger.exception(f"LLM unknown error: {e}")
            return "⚠️ LLM unavailable"