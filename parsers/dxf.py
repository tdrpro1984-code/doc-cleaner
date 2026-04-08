"""
DXF parser — ezdxf entity walking for text, dimensions, attributes, and metadata.

Extracts text-bearing entities (TEXT, MTEXT, DIMENSION, ATTRIB) from modelspace,
plus layer names and block definitions. Returns structured Markdown-friendly text.
"""
import logging

logger = logging.getLogger(__name__)

MAX_ENTITIES = 50000


def _collect_annotations(msp):
    """Collect text from TEXT and MTEXT entities."""
    texts = []
    for entity in msp.query("TEXT"):
        t = entity.dxf.text.strip()
        if t:
            texts.append(t)
        if len(texts) >= MAX_ENTITIES:
            logger.warning(f"DXF annotation limit reached ({MAX_ENTITIES}), truncating")
            return texts
    for entity in msp.query("MTEXT"):
        t = entity.text.strip() if entity.text else ""
        if t:
            texts.append(t)
        if len(texts) >= MAX_ENTITIES:
            logger.warning(f"DXF annotation limit reached ({MAX_ENTITIES}), truncating")
            return texts
    return texts


def _collect_dimensions(msp):
    """Collect dimension values — use override text if present, else get_measurement().

    In DXF, '<>' means 'show the automatic measurement' and is not real override text.
    """
    dims = []
    for entity in msp.query("DIMENSION"):
        override = entity.dxf.text.strip() if entity.dxf.text else ""
        if override and override != "<>":
            dims.append(override)
        else:
            try:
                val = entity.get_measurement()
                dims.append(str(round(val, 4)))
            except Exception:
                pass
        if len(dims) >= MAX_ENTITIES:
            logger.warning(f"DXF dimension limit reached ({MAX_ENTITIES}), truncating")
            return dims
    return dims


def _collect_attributes(msp):
    """Collect tag-value pairs from INSERT entities with ATTRIB sub-entities."""
    attribs = []
    for insert in msp.query("INSERT"):
        if insert.attribs:
            for attrib in insert.attribs:
                tag = attrib.dxf.tag.strip() if attrib.dxf.tag else ""
                value = attrib.dxf.text.strip() if attrib.dxf.text else ""
                if tag or value:
                    attribs.append(f"{tag}: {value}")
                if len(attribs) >= MAX_ENTITIES:
                    logger.warning(f"DXF attribute limit reached ({MAX_ENTITIES}), truncating")
                    return attribs
    return attribs


def _collect_layers(doc):
    """Collect non-default layer names."""
    return [
        layer.dxf.name
        for layer in doc.layers
        if layer.dxf.name not in ("0", "Defpoints")
    ]


def _collect_blocks(doc):
    """Collect user-defined block definition names (skip model/paper space blocks)."""
    return [
        block.name
        for block in doc.blocks
        if not block.name.startswith("*")
    ]


def parse(filepath):
    """
    Parse DXF file, extracting text entities and metadata.

    Returns structured text with sections: Annotations, Dimensions, Layers, Blocks.
    Empty sections are omitted. Entity count capped at MAX_ENTITIES per type.
    """
    import ezdxf

    try:
        doc = ezdxf.readfile(filepath)
    except Exception as e:
        logger.warning(f"DXF parse failed: {e}")
        return ""

    msp = doc.modelspace()

    annotations = _collect_annotations(msp)
    dimensions = _collect_dimensions(msp)
    attributes = _collect_attributes(msp)
    layers = _collect_layers(doc)
    blocks = _collect_blocks(doc)

    # Section order per spec: Annotations, Dimensions, Layers, Blocks
    # Attributes (from block inserts) prepended when present
    parts = []

    if annotations:
        parts.append("## Annotations\n")
        parts.append("\n".join(annotations))

    if attributes:
        parts.append("## Attributes\n")
        parts.append("\n".join(f"- {a}" for a in attributes))

    if dimensions:
        parts.append("## Dimensions\n")
        parts.append("\n".join(f"- {d}" for d in dimensions))

    if layers:
        parts.append("## Layers\n")
        parts.append("\n".join(f"- {name}" for name in layers))

    if blocks:
        parts.append("## Blocks\n")
        parts.append("\n".join(f"- {name}" for name in blocks))

    return "\n\n".join(parts)
