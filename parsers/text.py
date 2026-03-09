"""
Text / Markdown parser — multi-encoding support for CJK documents.

Encoding detection order: UTF-8 → Big5 → CP950 → UTF-16 → UTF-8 (lossy).
Covers the majority of Traditional Chinese documents from Taiwan banks and institutions.
"""
import os
import logging

logger = logging.getLogger(__name__)

# Encoding priority for Traditional Chinese documents
_ENCODINGS = ["utf-8", "big5", "cp950", "utf-16"]


def parse(filepath):
    """
    Read a text or Markdown file with automatic encoding detection.

    Tries encodings in order: UTF-8, Big5, CP950, UTF-16.
    Falls back to UTF-8 with error replacement as last resort.
    """
    for enc in _ENCODINGS:
        try:
            with open(filepath, "r", encoding=enc) as f:
                content = f.read()
            logger.info(f"Read {os.path.basename(filepath)} with encoding: {enc}")
            return content
        except (UnicodeDecodeError, LookupError):
            continue

    # Last resort: lossy UTF-8
    with open(filepath, "r", encoding="utf-8", errors="replace") as f:
        content = f.read()
    logger.warning(f"All encodings failed for {os.path.basename(filepath)}, fell back to UTF-8 lossy")
    return content
