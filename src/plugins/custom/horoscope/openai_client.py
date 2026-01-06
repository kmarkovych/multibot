"""OpenAI client for horoscope generation."""

from __future__ import annotations

import logging
from datetime import date

from openai import AsyncOpenAI, RateLimitError

from .i18n import get_lang
from .zodiac import ZodiacSign

logger = logging.getLogger(__name__)

# Language names for prompts
LANGUAGE_NAMES = {
    "en": "English",
    "uk": "Ukrainian",
    "pt": "Brazilian Portuguese",
    "kk": "Kazakh",
}


class HoroscopeGenerationError(Exception):
    """Error generating horoscope."""

    pass


class OpenAIClient:
    """Client for generating horoscopes using OpenAI API."""

    MODEL = "gpt-4.1-nano"

    def __init__(self, api_key: str):
        self.api_key = api_key
        self._client: AsyncOpenAI | None = None

    async def _get_client(self) -> AsyncOpenAI:
        """Get or create the async OpenAI client."""
        if self._client is None:
            self._client = AsyncOpenAI(api_key=self.api_key)
        return self._client

    async def generate_horoscope(
        self, sign: ZodiacSign, target_date: date, lang: str | None = None
    ) -> str:
        """
        Generate a horoscope for the given zodiac sign and date.

        Args:
            sign: The zodiac sign to generate horoscope for
            target_date: The date for the horoscope
            lang: Language code for the horoscope

        Returns:
            Generated horoscope text

        Raises:
            HoroscopeGenerationError: If generation fails
        """
        client = await self._get_client()
        lang = get_lang(lang)
        language_name = LANGUAGE_NAMES.get(lang, "English")

        prompt = f"""Generate a daily horoscope for {sign.value} for {target_date.strftime('%B %d, %Y')}.

IMPORTANT: Write the entire horoscope in {language_name} language.

Include insights about:
- Love & Relationships
- Career & Finance
- Health & Wellness
- Lucky numbers (3 numbers between 1-99)

Guidelines:
- Keep it positive and encouraging
- Be specific but not too personal
- Around 100-150 words total
- Use a warm, friendly tone

Format using HTML tags for Telegram:
- Use <b>Section Name:</b> for section headers (in {language_name})
- Use plain text for content
- End with <b>Lucky Numbers:</b> (in {language_name}) followed by the numbers
- Do NOT use markdown formatting like ** or __"""

        try:
            response = await client.chat.completions.create(
                model=self.MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": f"You are a mystical astrologer providing daily horoscopes. "
                        f"Your predictions are uplifting, insightful, and entertaining. "
                        f"Always write in {language_name} and format output using HTML tags "
                        f"(like <b> for bold), never markdown.",
                    },
                    {"role": "user", "content": prompt},
                ],
                max_tokens=400,
                temperature=0.8,
            )

            content = response.choices[0].message.content
            if not content:
                raise HoroscopeGenerationError("Empty response from OpenAI")

            return content.strip()

        except RateLimitError as e:
            logger.warning(f"OpenAI rate limit hit: {e}")
            raise HoroscopeGenerationError(
                "Service is temporarily busy. Please try again in a moment."
            )
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            raise HoroscopeGenerationError(f"Failed to generate horoscope: {e}")

    async def close(self) -> None:
        """Close the client connection."""
        if self._client:
            await self._client.close()
            self._client = None
