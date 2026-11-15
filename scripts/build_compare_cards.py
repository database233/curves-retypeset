import glob
import json
import os
import re
import pymupdf
from PIL import Image, ImageDraw, ImageFont

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MAIN_PDF = os.path.join(PROJECT_DIR, "main.pdf")
SECTIONS_DIR = os.path.join(PROJECT_DIR, "sections")
INDEX_JSON = os.path.join(PROJECT_DIR, "sections_index.json")
REF_DIR = os.path.join(PROJECT_DIR, "_ref_pages")
AUDIT_DIR = os.path.join(PROJECT_DIR, "_audit_renders")
OUT_DIR = os.path.join(PROJECT_DIR, "_compare_cards")

COL_W = 750
GAP = 24
PAD = 24
HEADER_H = 54
BG_COLOR = (242, 244, 247)
HEADER_BG = (30, 58, 95)
BORDER_COLOR = (205, 212, 222)


def get_font(size: int):
    candidates = [
        r"C:\Windows\Fonts\msyh.ttc",
        r"C:\Windows\Fonts\simhei.ttf",
        r"C:\Windows\Fonts\simsun.ttc",
    ]
    for c in candidates:
        if os.path.exists(c):
            try:
                return ImageFont.truetype(c, size)
            except Exception:
                pass
    return ImageFont.load_default()


def resize_to_width(img: Image.Image, target_w: int) -> Image.Image:
    w, h = img.size
    target_h = int(round(h * (target_w / w)))
    return img.resize((target_w, target_h), Image.Resampling.LANCZOS)


def stack_column(paths: list[str], col_w: int) -> Image.Image:
    if not paths:
        placeholder = Image.new("RGB", (col_w, 400), (255, 255, 255))
        return placeholder
    imgs = []
    for p in paths:
        im = Image.open(p).convert("RGB")
        imgs.append(resize_to_width(im, col_w))
    total_h = sum(im.height for im in imgs) + GAP * (len(imgs) - 1)
    canvas = Image.new("RGB", (col_w, total_h), BG_COLOR)
    y = 0
    for im in imgs:
        canvas.paste(im, (0, y))
        draw = ImageDraw.Draw(canvas)
        draw.rectangle([0, y, col_w - 1, y + im.height - 1], outline=BORDER_COLOR, width=2)
        y += im.height + GAP
    return canvas


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    # Clean old cards
    for old in glob.glob(os.path.join(OUT_DIR, "*.png")):
        os.remove(old)

    with open(INDEX_JSON, encoding="utf-8") as f:
        orig_index = {int(e["index"]): e for e in json.load(f)}

    doc = pymupdf.open(MAIN_PDF)
    toc = doc.get_toc()
    toc_secs = {}
    for _, title, pno in toc:
        parts = title.split()
        if parts and parts[0].isdigit():
            toc_secs[int(parts[0])] = pno

    # Detect where each section starts vertically on its start page
    sec_starts_top = {}
    for s in range(1, 101):
        pno = toc_secs[s]
        page = doc[pno - 1]
        prefix = f"{s}. "
        top_y = None
        for b in page.get_text("blocks"):
            if b[4].strip().startswith(prefix):
                top_y = b[1]
                break
        sec_starts_top[s] = (top_y is not None and top_y < 95)

    # Also detect exact page of every figure caption "图 X.Y"
    cap_pages = {}
    for pno in range(7, len(doc)):
        txt = doc[pno].get_text("text")
        for m in re.finditer(r"图\s*(\d+)\.(\d+)", txt):
            s = int(m.group(1))
            cap_pages.setdefault(s, set()).add(pno + 1)

    font_title = get_font(22)
    font_sub = get_font(16)

    manifest = []
    card_count = 0

    for s in range(1, 101):
        tex_path = os.path.join(SECTIONS_DIR, f"sec_{s:03d}.tex")
        tex = open(tex_path, encoding="utf-8").read()
        has_fig = ("\\begin{tikzpicture}" in tex) or ("\\includegraphics" in tex)
        figs = []
        for m in re.finditer(r"图\\?\s*(\d+\.\d+)", tex):
            if m.group(1) not in figs:
                figs.append(m.group(1))
        if not has_fig:
            continue

        c_start = toc_secs[s]
        if s < 100:
            next_p = toc_secs[s + 1]
            if sec_starts_top.get(s + 1, False):
                c_end = max(c_start, next_p - 1)
            else:
                c_end = next_p
        else:
            # Section 100 ends before appendix (index 101 in orig, TOC title starts with 附)
            app_p = next((p for _, t, p in toc if t.startswith("附")), len(doc))
            c_end = max(c_start, app_p - 1)

        comp_pages = sorted(set(range(c_start, c_end + 1)) | cap_pages.get(s, set()))
        # Filter out any accidental mention outside section window +/-1
        comp_pages = [p for p in comp_pages if c_start <= p <= c_end + 1]

        orig_meta = orig_index[s]
        o_start = orig_meta["start_pdf_page"]
        o_end = orig_meta["end_pdf_page"]
        orig_pages = list(range(o_start, o_end + 1))

        # Chunk into <=2 pages per card row so cards stay readable
        n_chunks = max(1, (max(len(comp_pages), len(orig_pages)) + 1) // 2)
        cards = []
        for ci in range(n_chunks):
            c_slice = comp_pages[ci * 2 : (ci + 1) * 2]
            o_slice = orig_pages[ci * 2 : (ci + 1) * 2]
            c_paths = [os.path.join(AUDIT_DIR, f"compiled_{p:03d}.png") for p in c_slice]
            o_paths = [os.path.join(REF_DIR, f"page_{p:03d}.png") for p in o_slice]

            left_col = stack_column(c_paths, COL_W)
            right_col = stack_column(o_paths, COL_W)

            body_h = max(left_col.height, right_col.height)
            total_w = PAD * 2 + COL_W * 2 + GAP
            total_h = HEADER_H + PAD * 2 + body_h

            card = Image.new("RGB", (total_w, total_h), BG_COLOR)
            draw = ImageDraw.Draw(card)
            draw.rectangle([0, 0, total_w, HEADER_H], fill=HEADER_BG)

            part_tag = f" ({ci + 1}/{n_chunks})" if n_chunks > 1 else ""
            header_txt = f"{orig_meta['title']}{part_tag}   |   图: {', '.join(figs)}"
            c_lbl = f"重排 PDF p.{c_slice[0]}" + (f"-{c_slice[-1]}" if len(c_slice) > 1 else "") if c_slice else "重排页(接上页)"
            o_lbl = f"原书扫描 p.{o_slice[0]}" + (f"-{o_slice[-1]}" if len(o_slice) > 1 else "") if o_slice else "原书页(接上页)"
            sub_txt = f"左: {c_lbl}    vs    右: {o_lbl}"

            draw.text((PAD, 10), header_txt, fill=(255, 255, 255), font=font_title)
            draw.text((total_w - PAD - 460, 15), sub_txt, fill=(210, 228, 248), font=font_sub)

            card.paste(left_col, (PAD, HEADER_H + PAD))
            card.paste(right_col, (PAD + COL_W + GAP, HEADER_H + PAD))

            fname = f"sec_{s:03d}.png" if n_chunks == 1 else f"sec_{s:03d}_p{ci + 1}.png"
            out_path = os.path.join(OUT_DIR, fname)
            card.save(out_path, optimize=True)
            cards.append(fname)
            card_count += 1

        manifest.append({
            "section": s,
            "title": orig_meta["title"],
            "figs": figs,
            "compiled_pages": comp_pages,
            "orig_pages": orig_pages,
            "cards": cards,
        })

    manifest_path = os.path.join(OUT_DIR, "manifest.json")
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)

    print(f"Generated {card_count} comparison cards covering {len(manifest)} sections in {OUT_DIR}")


if __name__ == "__main__":
    main()
