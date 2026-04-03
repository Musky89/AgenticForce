from __future__ import annotations

from openai import OpenAI

from agency.config import Settings


def get_client(settings: Settings) -> OpenAI:
    if not settings.openai_api_key:
        raise RuntimeError(
            "OPENAI_API_KEY is not set. Copy .env.example to .env and add your key."
        )
    return OpenAI(api_key=settings.openai_api_key)


def complete(
    client: OpenAI,
    model: str,
    system: str,
    user: str,
    temperature: float = 0.7,
) -> str:
    resp = client.chat.completions.create(
        model=model,
        temperature=temperature,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    )
    choice = resp.choices[0]
    content = choice.message.content
    if not content:
        raise RuntimeError("Empty model response")
    return content.strip()
