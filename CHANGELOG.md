# Changelog

## v1.2.0

### New Features

- **DXF support**: Extract text annotations, dimensions, layer names, block attributes from `.dxf` engineering drawings via `ezdxf`
- **PPTX support**: Extract slide text, tables (as Markdown pipe tables), and speaker notes from `.pptx` via `python-pptx`
- **PPT support**: Legacy `.ppt` extraction via macOS `textutil`
- **DOC support**: Legacy `.doc` extraction via macOS `textutil`

### Breaking Changes

- **YAML frontmatter**: `source_path` renamed to `sourcePath` (camelCase, consistent with `pubDate`)

### Security

- Fix YAML newline injection in `_escape_yaml_str` — `\n` and `\r` now properly escaped
- Add entity count limit (`MAX_ENTITIES=50000`) to DXF parser to prevent resource exhaustion
- Add ZIP decompressed size check (`500MB`) and slide limit (`500`) to PPTX parser
- Add `timeout=60s` to all `textutil` subprocess calls

### Improvements

- Extract shared `textutil` conversion logic into `parsers/_textutil.py` (deduplicates 3 copy-paste instances)
