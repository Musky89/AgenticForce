from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    openai_api_key: str | None
    model: str

    @classmethod
    def load(cls) -> Settings:
        key = os.getenv("OPENAI_API_KEY")
        model = os.getenv("AGENCY_MODEL", "gpt-4o")
        return cls(openai_api_key=key, model=model)
