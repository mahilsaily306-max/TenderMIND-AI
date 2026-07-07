import logging

from app.services.ai_service import ai_provider

logger = logging.getLogger(__name__)

REWRITE_PROMPT = """You are a bid proposal writing assistant. Rewrite the following section to be more compelling and professional while preserving all factual information. Use active voice and clear language."""  # noqa: E501

EXPAND_PROMPT = """You are a bid proposal writing assistant. Expand the following section with additional detail, evidence, and persuasive language. Keep it concise but thorough."""  # noqa: E501

IMPROVE_PROMPT = """You are a bid proposal editor. Improve the following text for clarity, grammar, and impact. Fix any errors and enhance the professional tone."""  # noqa: E501

TONE_PROMPT = """You are a bid proposal writing assistant. Rewrite the following text in a {tone} tone. Maintain all factual information."""  # noqa: E501


class CopilotService:
    """AI Proposal Copilot — rewrite, expand, improve, change tone."""

    async def rewrite(self, text: str, context: str | None = None) -> str:
        prompt = f"Original text:\n{text}\n"
        if context:
            prompt += f"\nContext: {context}\n"
        return await ai_provider.chat(REWRITE_PROMPT, prompt, temperature=0.3)

    async def expand(self, text: str, context: str | None = None) -> str:
        prompt = f"Original text:\n{text}\n"
        if context:
            prompt += f"\nContext: {context}\n"
        return await ai_provider.chat(EXPAND_PROMPT, prompt, temperature=0.4)

    async def improve(self, text: str) -> str:
        return await ai_provider.chat(IMPROVE_PROMPT, f"Text:\n{text}", temperature=0.2)

    async def change_tone(self, text: str, tone: str) -> str:
        return await ai_provider.chat(
            TONE_PROMPT.format(tone=tone),
            f"Text:\n{text}",
            temperature=0.4,
        )
