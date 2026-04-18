"""One-off helper: dump inputs/manuscript.docx body text to logs/manuscript_extract_utf8.txt (UTF-8)."""
from __future__ import annotations

import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
NS = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}


def main() -> None:
    docx = BASE / "inputs" / "manuscript.docx"
    out = BASE / "logs" / "manuscript_extract_utf8.txt"
    out.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(docx) as zf:
        xml = zf.read("word/document.xml")
    root = ET.fromstring(xml)
    paras: list[str] = []
    for p in root.iter("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}p"):
        parts: list[str] = []
        for node in p.iter():
            if node.tag.endswith("}t") and node.text:
                parts.append(node.text)
            if node.tag.endswith("}t") and node.tail:
                parts.append(node.tail)
        t = "".join(parts)
        if t.strip():
            paras.append(t)
    text = "\n".join(paras)
    out.write_text(text, encoding="utf-8")
    print(f"wrote {len(text)} chars -> {out.relative_to(BASE)}")


if __name__ == "__main__":
    main()
