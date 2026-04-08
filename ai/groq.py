"""
Groq backend.

Uses Groq's OpenAI-compatible chat completions API so doc-cleaner can support
fast cloud inference with text and image inputs.
"""
import base64
import io
import json
import logging
import ssl
from typing import Optional
from urllib import error, request

from .base import AIBackend

logger = logging.getLogger(__name__)

DEFAULT_USER_AGENT = "doc-cleaner/0.1"


class GroqBackend(AIBackend):
    """Groq backend via the OpenAI-compatible chat completions API."""

    MAX_IMAGES = 5

    def __init__(
        self,
        api_key: str,
        model: str = "meta-llama/llama-4-scout-17b-16e-instruct",
        base_url: str = "https://api.groq.com/openai/v1",
        timeout: int = 120,
    ):
        self._api_key = api_key
        self._model = model
        self._base_url = self._validate_base_url(base_url)
        self._timeout = timeout

    @staticmethod
    def _validate_base_url(url: str) -> str:
        """Reject private/internal URLs to prevent SSRF via malicious config."""
        from urllib.parse import urlparse
        parsed = urlparse(url.rstrip("/"))
        if parsed.scheme not in ("https", "http"):
            raise ValueError(f"Groq base_url must use http(s), got {parsed.scheme!r}")
        host = parsed.hostname or ""
        if host in ("localhost", "127.0.0.1", "::1") or host.startswith("10.") or \
           host.startswith("192.168.") or host.startswith("169.254.") or \
           host.startswith("172.") and 16 <= int(host.split(".")[1]) <= 31:
            raise ValueError(
                f"Groq base_url must not point to private/internal networks, got {host!r}. "
                f"If you need local inference, use Ollama instead."
            )
        return parsed.geturl()

    def call(self, prompt: str, images: Optional[list] = None, text: Optional[str] = None) -> str:
        """Send prompt + optional images/text to Groq."""
        user_content = []

        if text:
            user_content.append({
                "type": "text",
                "text": f"--- TEXT CONTENT ---\n{text}",
            })

        if images:
            if len(images) > self.MAX_IMAGES:
                logger.warning(
                    f"Groq vision supports at most {self.MAX_IMAGES} images per request; "
                    f"truncating {len(images)} images to the first {self.MAX_IMAGES}."
                )
                images = images[:self.MAX_IMAGES]

            for img in images:
                buf = io.BytesIO()
                img.save(buf, format="PNG")
                encoded = base64.b64encode(buf.getvalue()).decode("utf-8")
                user_content.append({
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/png;base64,{encoded}",
                    },
                })

        if not user_content:
            user_content.append({
                "type": "text",
                "text": "No extracted text or images were available.",
            })

        payload = {
            "model": self._model,
            "messages": [
                {
                    "role": "system",
                    "content": prompt,
                },
                {
                    "role": "user",
                    "content": user_content,
                },
            ],
            "max_tokens": 16384,
            "temperature": 0.2,
        }

        body = json.dumps(payload).encode("utf-8")
        req = request.Request(
            url=f"{self._base_url}/chat/completions",
            data=body,
            headers={
                "Authorization": f"Bearer {self._api_key}",
                "Content-Type": "application/json",
                "User-Agent": DEFAULT_USER_AGENT,
            },
            method="POST",
        )

        ssl_context = None
        try:
            import certifi

            ssl_context = ssl.create_default_context(cafile=certifi.where())
        except ImportError:
            ssl_context = ssl.create_default_context()

        try:
            with request.urlopen(req, timeout=self._timeout, context=ssl_context) as resp:
                data = json.loads(resp.read().decode("utf-8"))
        except error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            logger.error(f"Groq API call failed: {exc.code} {detail}")
            raise RuntimeError(f"Groq API returned HTTP {exc.code}: {detail}") from exc
        except Exception as exc:
            logger.error(f"Groq API call failed: {exc}")
            raise

        choices = data.get("choices", [])
        if choices:
            message = choices[0].get("message", {})
            content = message.get("content")
            if isinstance(content, str) and content:
                return content

        logger.error(f"Unexpected Groq response shape: {data}")
        raise RuntimeError("Groq API returned no message content")