# Security Policy

## Supported Versions

Only the latest release on the `main` branch receives security fixes.

## Sensitive Files — Never Commit These

| File | Contains |
|---|---|
| `.env` | `GEMINI_API_KEY`, `PDF_PASSWORD` |
| `config.json` | AI model/host settings, ad patterns — **no secrets** |

Both are excluded by `.gitignore`. API keys and passwords belong in `.env` only.
doc-cleaner warns at startup if it detects secret-like fields in `config.json`.

## Threat Model

doc-cleaner processes documents from local disk. It does **not** fetch files from the network.
The primary risks are:

### Malicious input files

- **PDF bombs**: PyMuPDF (fitz) handles page rendering; extremely large PDFs may consume memory. The text extraction cap (`max_chars=150,000`) limits exposure.
- **Malicious DOCX/XLSX**: `python-docx` and `openpyxl`/`pandas` parse XML internally. Keep these dependencies updated.
- **ZIP bombs via pikepdf**: pikepdf operates on PDF streams, not ZIP archives. No decompression bomb risk here (that concern belongs to [gmail-statement-fetcher](https://github.com/notoriouslab/gmail-statement-fetcher)).

### AI backend exposure

- **Gemini mode**: document content is sent to Google's API. Do not use `--ai gemini` for documents you cannot share with a cloud provider.
- **Ollama mode**: all processing stays local. Use `--ai ollama` or `--ai none` for sensitive documents.

### Output files

- Atomic writes (`tmp` + `os.replace()`) prevent partial output files.
- Output filenames are derived from input filenames — no user-controlled path traversal.

## Known Limitations

- **No input sanitisation for AI prompts**: extracted text is sent directly to the AI backend. If a document contains prompt injection attempts, the AI may follow them. This is a known limitation of LLM-based processing.
- **Encoding detection is heuristic**: the Big5 → CP950 → UTF-16 fallback chain covers most Traditional Chinese documents, but may misdetect rare encodings.

## Reporting a Vulnerability

Please **do not** open a public GitHub issue for security vulnerabilities.

Email the maintainer directly (see profile) or open a
[private security advisory](https://github.com/notoriouslab/doc-cleaner/security/advisories/new).

Expect a response within 72 hours.
