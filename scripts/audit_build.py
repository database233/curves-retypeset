import os
import re
import sys
import pymupdf

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG_PATH = os.path.join(PROJECT_DIR, "main.log")
PDF_PATH = os.path.join(PROJECT_DIR, "main.pdf")
PREVIEW_DIR = os.path.join(PROJECT_DIR, "_audit_renders")


def audit_log(log_path: str):
    if not os.path.exists(log_path):
        print(f"Log not found: {log_path}")
        return False

    with open(log_path, "r", encoding="utf-8", errors="replace") as f:
        lines = f.readlines()

    errors = []
    missing_chars = []
    overfull_hbox = []
    undefined_refs = []

    for idx, line in enumerate(lines, 1):
        s = line.strip()
        if s.startswith("!"):
            errors.append((idx, s))
        elif "Missing character:" in s:
            missing_chars.append((idx, s))
        elif "Overfull \\hbox" in s:
            m = re.search(r"\(([0-9.]+)pt too wide\)", s)
            pt = float(m.group(1)) if m else 0.0
            if pt >= 1.5:
                overfull_hbox.append((idx, pt, s))
        elif "Reference" in s and "undefined" in s:
            undefined_refs.append((idx, s))

    print(f"=== Build Audit Report ===")
    print(f"Errors: {len(errors)}")
    for ln, msg in errors[:20]:
        print(f"  [L{ln}] {msg}")

    print(f"Missing chars: {len(missing_chars)}")
    for ln, msg in missing_chars[:20]:
        print(f"  [L{ln}] {msg}")

    print(f"Overfull \\hbox (>= 1.5pt): {len(overfull_hbox)}")
    for ln, pt, msg in sorted(overfull_hbox, key=lambda x: -x[1])[:25]:
        print(f"  [L{ln}] ({pt:.2f}pt) {msg}")

    print(f"Undefined refs: {len(undefined_refs)}")
    for ln, msg in undefined_refs[:20]:
        print(f"  [L{ln}] {msg}")

    return len(errors) == 0 and len(missing_chars) == 0


def render_pages(pdf_path: str, page_spec: str | None = None, dpi: int = 160):
    if not os.path.exists(pdf_path):
        print(f"PDF not found: {pdf_path}")
        return
    os.makedirs(PREVIEW_DIR, exist_ok=True)
    doc = pymupdf.open(pdf_path)
    print(f"Compiled PDF total pages: {len(doc)}")

    if page_spec:
        pages = []
        for part in page_spec.split(","):
            if "-" in part:
                a, b = map(int, part.split("-"))
                pages.extend(range(a, b + 1))
            else:
                pages.append(int(part))
    else:
        pages = list(range(1, len(doc) + 1))

    for p in pages:
        if 1 <= p <= len(doc):
            pix = doc[p - 1].get_pixmap(dpi=dpi)
            pix.save(os.path.join(PREVIEW_DIR, f"compiled_{p:03d}.png"))
    print(f"Rendered {len(pages)} compiled pages to {PREVIEW_DIR}")


if __name__ == "__main__":
    ok = audit_log(LOG_PATH)
    args = sys.argv[1:]
    if args:
        if args[0] == "--render":
            spec = None if (len(args) < 2 or args[1] == "all") else args[1]
            render_pages(PDF_PATH, spec)
        else:
            spec = None if args[0] == "all" else args[0]
            render_pages(PDF_PATH, spec)
    sys.exit(0 if ok else 1)
