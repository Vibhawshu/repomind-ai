from groq import Groq

from app.config import settings


_client: Groq | None = None


def _get_client() -> Groq:
    global _client
    if _client is None:
        _client = Groq(api_key=settings.GROQ_API_KEY)
    return _client


def chat(messages: list[dict], temperature: float = 0.2) -> str:
    resp = _get_client().chat.completions.create(
        model=settings.LLM_MODEL,
        messages=messages,
        temperature=temperature,
        max_tokens=1024,
    )
    return resp.choices[0].message.content or ""