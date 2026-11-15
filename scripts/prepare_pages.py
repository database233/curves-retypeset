import json
import os
import sys
import pymupdf

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_PDF = os.path.join(os.path.dirname(PROJECT_DIR), "形形色色的曲线__蒋声-中学生文库.pdf")
PDF_PATH = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_PDF
REF_DIR = os.path.join(PROJECT_DIR, "_ref_pages")
SECTIONS_DIR = os.path.join(PROJECT_DIR, "sections")


def main():
    os.makedirs(REF_DIR, exist_ok=True)
    os.makedirs(SECTIONS_DIR, exist_ok=True)

    doc = pymupdf.open(PDF_PATH)
    total_pages = len(doc)
    print(f"Total PDF pages: {total_pages}")

    # 1. 解析全书目录书签
    toc = doc.get_toc()
    entries = []
    for level, title, page in toc:
        try:
            decoded = title.encode("latin1").decode("gbk")
        except Exception:
            decoded = title
        entries.append({"level": level, "title": decoded, "pdf_page": page})

    # 计算每节的起始页与结束页
    sections_meta = []
    for idx, entry in enumerate(entries):
        start_p = entry["pdf_page"]
        end_p = entries[idx + 1]["pdf_page"] if idx + 1 < len(entries) else total_pages
        # 注意：若下一节开始于同一页或后续页，包含 end_p 以防跨页收尾
        if idx + 1 < len(entries) and end_p > start_p:
            # 下一节的起始页可能包含上一节末尾几行，保留重叠页以便转录核对
            pass
        sections_meta.append({
            "index": idx + 1,
            "title": entry["title"],
            "start_pdf_page": start_p,
            "end_pdf_page": end_p,
        })

    meta_path = os.path.join(PROJECT_DIR, "sections_index.json")
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(sections_meta, f, ensure_ascii=False, indent=2)
    print(f"Wrote {len(sections_meta)} entries to {meta_path}")

    # 2. 渲染全书 300 DPI 参考图（跳过已存在文件以支持断点续跑）
    rendered = 0
    for i in range(total_pages):
        out_png = os.path.join(REF_DIR, f"page_{i + 1:03d}.png")
        if not os.path.exists(out_png):
            pix = doc[i].get_pixmap(dpi=300)
            pix.save(out_png)
            rendered += 1
    print(f"Rendered {rendered} new 300-DPI PNGs (total {total_pages}) in {REF_DIR}")


if __name__ == "__main__":
    main()
