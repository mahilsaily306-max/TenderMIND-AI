import json
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)


class AIProvider:
    """Abstract AI provider with OpenAI default, swappable via config."""

    def __init__(self):
        self.provider = settings.ai_provider
        self.model = settings.llm_model
        self._client = None

    def _get_client(self):
        if self._client is not None:
            return self._client
        if self.provider == "openai":
            import openai

            self._client = openai.AsyncOpenAI(api_key=settings.openai_api_key)
        elif self.provider == "anthropic":
            import anthropic

            self._client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
        else:
            from openai import AsyncOpenAI

            self._client = AsyncOpenAI(base_url=settings.ollama_base_url, api_key="ollama")
        return self._client

    async def chat(self, system_prompt: str, user_prompt: str, temperature: float = 0.1) -> str:
        try:
            if self.provider == "anthropic":
                client = self._get_client()
                msg = await client.messages.create(
                    model=self.model,
                    system=system_prompt,
                    messages=[{"role": "user", "content": user_prompt}],
                    temperature=temperature,
                    max_tokens=4096,
                )
                return msg.content[0].text
            else:
                client = self._get_client()
                resp = await client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    temperature=temperature,
                    max_tokens=4096,
                )
                return resp.choices[0].message.content
        except Exception as e:
            logger.error("AI chat failed: %s", e)
            raise

    async def extract_json(self, system_prompt: str, user_prompt: str) -> dict:
        """Extract structured JSON from document text. Returns dict with citations."""
        response = await self.chat(
            system_prompt=system_prompt + "\n\nReturn ONLY valid JSON. No markdown. No explanation.",
            user_prompt=user_prompt,
            temperature=0.05,
        )
        # Strip markdown fences if present
        if "```json" in response:
            response = response.split("```json")[1].split("```")[0].strip()
        elif "```" in response:
            response = response.split("```")[1].split("```")[0].strip()
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            logger.error("Failed to parse AI response as JSON: %s", response[:500])
            return {"error": "parse_failed", "raw": response}


ai_provider = AIProvider()


EXTRACTION_SYSTEM_PROMPT = """You are a tender requirement extraction specialist. Extract structured data from tender/RFP documents.

For every field you extract, you MUST include:
- "source_page": the page number where you found this information (or null if unknown)
- "source_clause": the clause/section reference (or null if unknown)
- "is_resolved": true if the value is clearly stated in the document, false if you had to infer

If you cannot find a value for a field, set it to null with "is_resolved": false.
NEVER fabricate values. If unsure, mark unresolved.

Extract these fields when present:
- submission_deadline: date string
- bid_value: estimated value or budget
- client_name: name of the issuing organization
- project_duration: duration or timeline
- eligibility_criteria: list of eligibility requirements
- key_requirements: list of key requirements
- evaluation_criteria: list with weights if available
- required_certifications: list
- submission_format: format requirements (electronic/paper/both)

Also extract compliance requirements as a list:
- compliance_items: array of {requirement, category, source_page, source_clause}
"""


async def extract_tender_requirements(document_text: str, document_chunks: list[dict] | None = None) -> dict:
    """Extract requirements from tender document text with mandatory citations."""
    chunk_context = ""
    if document_chunks:
        chunk_context = (
            "\n\n---DOCUMENT CHUNKS---\n"
            + "\n\n".join(
                f"[Page {c.get('page_number', '?')}, Clause {c.get('clause_reference', 'N/A')}]: {c.get('content', '')[:2000]}"  # noqa: E501
                for c in document_chunks[:20]
            )
        )

    prompt = f"""Extract all requirements and structured fields from this tender document.

{chunk_context if document_chunks else document_text[:15000]}

Return JSON with:
1. "fields": object of extracted fields, each with value, source_page, source_clause, is_resolved
2. "compliance_items": array of compliance requirements with status="pending", category, source_page, source_clause
3. "unresolved_fields": array of field names that could not be determined"""

    result = await ai_provider.extract_json(EXTRACTION_SYSTEM_PROMPT, prompt)
    return result
