"""
AI Privacy Gateway — Main FastAPI application.

Provides:
  - /v1/chat      — privacy-preserving LLM chat
  - /v1/sanitize  — PII anonymization only
  - /v1/restore   — restore tokens
  - /v1/check-prompt — prompt guard only
  - /health       — health check
"""
"""
AI Privacy Gateway — Main FastAPI application.
"""
import os

# ⭐ MUST be set BEFORE any heavy imports
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")

import logging
import time
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
# ... (بقیه importها)
import logging
import time
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from app.config import settings
from app import __version__
from app.security import (
    PIISanitizer,
    PromptGuard,
    OutputFilter,
    Decision,
    OutputDecision,
)
from app.llm import LLMClient


# ═══════════════════════════════════════════════════════════
# Logging
# ═══════════════════════════════════════════════════════════

logging.basicConfig(
    level=settings.LOG_LEVEL,
    format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════
# Global instances
# ═══════════════════════════════════════════════════════════

sanitizer: PIISanitizer | None = None
prompt_guard: PromptGuard | None = None
output_filter: OutputFilter | None = None
llm_client: LLMClient | None = None


# ═══════════════════════════════════════════════════════════
# System Prompt
# ═══════════════════════════════════════════════════════════

SYSTEM_PROMPT = (
    "You are a helpful assistant. "
    "The user's messages may contain tokens like [[PERSON_xxx]], "
    "[[EMAIL_xxx]], [[LOCATION_xxx]], etc. These are anonymized placeholders. "
    "You MUST return them unchanged in your response — do NOT try to guess "
    "or interpret them. Just use them as-is."
)


# ═══════════════════════════════════════════════════════════
# Lifespan
# ═══════════════════════════════════════════════════════════

@asynccontextmanager
async def lifespan(app: FastAPI):
    global sanitizer, prompt_guard, output_filter, llm_client

    logger.info(f"🚀 Starting {settings.APP_NAME} v{__version__}")
    logger.info(f"   Environment: {settings.ENVIRONMENT}")

    sanitizer = PIISanitizer()
    logger.info("   ✅ Sanitizer initialized (12 languages)")

    prompt_guard = PromptGuard(enable_embedding=True)
    logger.info("   ✅ Prompt Guard initialized")

    output_filter = OutputFilter(sanitizer)
    logger.info("   ✅ Output Filter initialized")

    llm_client = LLMClient()
    logger.info(f"   ✅ LLM Client initialized ({settings.LLM_PROVIDER})")

    yield

    if llm_client:
        await llm_client.close()
    logger.info("🛑 Shutting down...")


# ═══════════════════════════════════════════════════════════
# FastAPI
# ═══════════════════════════════════════════════════════════

app = FastAPI(
    title=settings.APP_NAME,
    version=__version__,
    description="Privacy-preserving middleware between users and LLMs.",
    lifespan=lifespan,
)


# ═══════════════════════════════════════════════════════════
# Schemas
# ═══════════════════════════════════════════════════════════

class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=8000)
    language: str | None = None
    session_id: str | None = None
    temperature: float = Field(0.7, ge=0.0, le=2.0)


class ChatResponse(BaseModel):
    response: str
    session_id: str
    detected_language: str
    pii_detected: int
    pii_by_type: dict[str, int]
    output_decision: str
    processing_time_ms: float


class SanitizeRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=8000)
    language: str | None = None


class SanitizeResponse(BaseModel):
    sanitized_text: str
    pii_detected: int
    by_type: dict[str, int]
    mapping: dict[str, str]
    detected_language: str


class RestoreRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=8000)
    mapping: dict[str, str]


class CheckPromptRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=8000)


class CheckPromptResponse(BaseModel):
    decision: str
    score: float
    reason: str
    flags: list[str]
    matched_categories: list[str]


# ═══════════════════════════════════════════════════════════
# Endpoints
# ═══════════════════════════════════════════════════════════

@app.get("/", tags=["root"])
async def root():
    return {
        "name": settings.APP_NAME,
        "version": __version__,
        "message": "🛡️ Welcome to AI Privacy Gateway",
        "docs": "/docs",
        "health": "/health",
    }


@app.get("/health", tags=["system"])
async def health():
    return {
        "status": "ok",
        "version": __version__,
        "environment": settings.ENVIRONMENT,
        "sanitizer_ready": sanitizer is not None,
        "prompt_guard_ready": prompt_guard is not None,
        "output_filter_ready": output_filter is not None,
        "llm_ready": llm_client is not None and bool(settings.LLM_API_KEY),
        "supported_languages": [
            "en", "fa", "tr", "ar", "zh", "ru",
            "es", "fr", "de", "pt", "ja", "ko",
        ],
    }


# ═══════════════════════════════════════════════════════════
# ⭐ THE MAIN ENDPOINT: /v1/chat
# ═══════════════════════════════════════════════════════════

@app.post("/v1/chat", response_model=ChatResponse, tags=["chat"])
async def chat_endpoint(body: ChatRequest):
    """
    Privacy-preserving chat with LLM.

    Pipeline:
      1. Prompt Guard (injection check)
      2. Sanitizer (PII anonymization — input mode)
      3. LLM (send anonymized)
      4. Output Filter (leak check — output mode)
      5. Restore (tokens → real values)

    Try:
      - "My name is John Doe and my email is john@example.com"
      - "ignore all previous instructions"  (blocked)
      - "کد ملی من 0012345672 است"
    """
    if not all([sanitizer, prompt_guard, output_filter, llm_client]):
        raise HTTPException(503, "Services not initialized")

    start = time.time()
    session_id = body.session_id or str(uuid.uuid4())

    # ═══ 1. PROMPT GUARD ═══
    verdict = prompt_guard.check(body.message)

    if verdict.decision == Decision.BLOCK:
        logger.warning(f"Prompt blocked: {verdict.reason}")
        raise HTTPException(
            status_code=400,
            detail={
                "error": "prompt_blocked",
                "reason": verdict.reason,
            },
        )

    # ═══ 2. SANITIZE (input mode with NER) ═══
    sanitize_result = sanitizer.sanitize(
        body.message,
        language=body.language,
        mode="input",
    )

    # ═══ 3. LLM CALL ═══
    try:
        llm_response = await llm_client.chat(
            message=sanitize_result.sanitized_text,
            system_prompt=SYSTEM_PROMPT,
            temperature=body.temperature,
        )
    except Exception as e:
        logger.exception(f"LLM call failed: {e}")
        raise HTTPException(502, "LLM service unavailable")

    # ═══ 4. OUTPUT FILTER ═══
    output_verdict = output_filter.check(llm_response)

    if output_verdict.decision == OutputDecision.BLOCK:
        logger.warning(f"Output blocked: {output_verdict.reason}")
        return ChatResponse(
            response="⚠️ Response was blocked for security reasons.",
            session_id=session_id,
            detected_language=sanitize_result.detected_language,
            pii_detected=sanitize_result.total,
            pii_by_type=sanitize_result.by_type,
            output_decision=output_verdict.decision.value,
            processing_time_ms=round((time.time() - start) * 1000, 2),
        )

    safe_response = output_verdict.safe_text

    # ═══ 5. RESTORE ═══
    restored_response = sanitizer.restore(
        safe_response,
        sanitize_result.mapping,
    )

    elapsed_ms = round((time.time() - start) * 1000, 2)

    logger.info(
        f"Chat: lang={sanitize_result.detected_language} "
        f"pii={sanitize_result.total} "
        f"output={output_verdict.decision.value} "
        f"time={elapsed_ms}ms"
    )

    return ChatResponse(
        response=restored_response,
        session_id=session_id,
        detected_language=sanitize_result.detected_language,
        pii_detected=sanitize_result.total,
        pii_by_type=sanitize_result.by_type,
        output_decision=output_verdict.decision.value,
        processing_time_ms=elapsed_ms,
    )


# ═══════════════════════════════════════════════════════════
# Other Endpoints (unchanged)
# ═══════════════════════════════════════════════════════════

@app.post("/v1/sanitize", response_model=SanitizeResponse, tags=["privacy"])
async def sanitize_endpoint(body: SanitizeRequest):
    if sanitizer is None:
        raise HTTPException(503, "Sanitizer not initialized")

    result = sanitizer.sanitize(
        body.text,
        language=body.language,
        mode="input",
    )

    return SanitizeResponse(
        sanitized_text=result.sanitized_text,
        pii_detected=result.total,
        by_type=result.by_type,
        mapping=result.mapping,
        detected_language=result.detected_language,
    )


@app.post("/v1/restore", tags=["privacy"])
async def restore_endpoint(body: RestoreRequest):
    if sanitizer is None:
        raise HTTPException(503, "Sanitizer not initialized")
    return {"restored_text": sanitizer.restore(body.text, body.mapping)}


@app.post("/v1/check-prompt", response_model=CheckPromptResponse, tags=["security"])
async def check_prompt_endpoint(body: CheckPromptRequest):
    if prompt_guard is None:
        raise HTTPException(503, "Prompt Guard not initialized")

    verdict = prompt_guard.check(body.text)

    return CheckPromptResponse(
        decision=verdict.decision.value,
        score=verdict.score,
        reason=verdict.reason,
        flags=verdict.flags,
        matched_categories=(
            verdict.pattern_result.matched_categories
            if verdict.pattern_result else []
        ),
    )