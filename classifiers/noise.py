"""
Noise cleaner — ad truncation and URL removal for financial documents.

Configurable patterns: pass your own cutoff patterns via config, or use
the built-in defaults targeting common Taiwan financial document footers.
"""
import re
import logging

logger = logging.getLogger(__name__)

# Default cutoff patterns for Taiwan financial documents
DEFAULT_CUTOFF_PATTERNS = [
    r"<投資人權益通知訊息[ >]",
    r"[～~]\s*總\s*公\s*司\s*訊\s*息\s*[～~]",
    r"依金融監督管理委員會保險局",
    r"謹慎理財.{0,20}信用至上",
    r"本商品由.{0,30}核准",
]

_BLANK_LINES_RE = re.compile(r"\n{3,}")


def clean_text(text, cutoff_patterns=None, min_keep_ratio=0.3):
    """
    Remove known ad/legal footers and clean up whitespace.

    Args:
        text: raw extracted text
        cutoff_patterns: list of regex patterns. Everything after the first
                         match is removed. Defaults to Taiwan financial patterns.
        min_keep_ratio: safety guard — if truncation would remove more than
                        (1 - min_keep_ratio) of the text, skip it and warn.
                        Default 0.3 means at least 30% of content must survive.

    Returns:
        cleaned text
    """
    patterns = cutoff_patterns or DEFAULT_CUTOFF_PATTERNS

    if patterns:
        cutoff_re = re.compile(
            "|".join(f"({p})" for p in patterns),
            re.DOTALL,
        )
        m = cutoff_re.search(text)
        if m:
            kept = text[: m.start()].rstrip()
            keep_ratio = len(kept) / max(len(text), 1)
            if keep_ratio < min_keep_ratio:
                logger.warning(
                    f"Ad truncation would remove {1 - keep_ratio:.0%} of content "
                    f"(pattern matched at pos {m.start()}/{len(text)}). "
                    f"Skipping truncation to prevent data loss."
                )
            else:
                text = kept
                logger.debug(f"Truncated at ad pattern (pos {m.start()}, kept {keep_ratio:.0%})")

    # Remove URLs
    text = re.sub(r"https?://\S+|mma\.tw/\S+", "", text)

    # Compress excessive blank lines
    text = _BLANK_LINES_RE.sub("\n\n", text)

    return text.strip()
