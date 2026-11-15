import os
import pymupdf
import re
import sys

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
pdf_path = os.path.join(PROJECT_DIR, "main.pdf")
doc = pymupdf.open(pdf_path)

print(f"=== Total Compiled Pages: {len(doc)} ===")

# 1. Blank Pages Check
blank_pages = []
for idx, page in enumerate(doc, 1):
    text = page.get_text().strip()
    drawings = page.get_drawings()
    images = page.get_images()
    if not text and not drawings and not images:
        blank_pages.append(idx)

print(f"\n1. Blank Pages Check: {len(blank_pages)} found.")
if blank_pages:
    print(f"   [FAIL] Blank pages: {blank_pages}")
else:
    print("   [PASS] 0 blank pages detected across entire book.")

# 2. Footer Collision Check
footer_collisions = []
for idx, page in enumerate(doc, 1):
    blocks = page.get_text("blocks")
    text_blocks = [b for b in blocks if b[4].strip()]
    if len(text_blocks) < 2:
        continue
    sorted_blocks = sorted(text_blocks, key=lambda b: b[3])
    last_block = sorted_blocks[-1]
    second_last = sorted_blocks[-2]
    # Check if last block is page number
    if re.fullmatch(r"\d+", last_block[4].strip()):
        gap = last_block[1] - second_last[3] # y0 of footer - y1 of last content
        if gap < 0: # collision
            footer_collisions.append((idx, gap, last_block[4].strip(), second_last[4].strip()[:30]))

print(f"\n2. Footer Collision Check: {len(footer_collisions)} found.")
if footer_collisions:
    print(f"   [FAIL] Collisions: {footer_collisions}")
else:
    print("   [PASS] 0 footer collisions detected across entire book.")

# 3. Section 17 Single-Page Convergence Check
p32_txt = doc[31].get_text() # Physical Page 32 (sec 16 end)
p33_txt = doc[32].get_text() # Physical Page 33 (sec 17)
p34_txt = doc[33].get_text() # Physical Page 34 (sec 18)

print("\n3. Section 17 Convergence Analysis:")
keywords = ["摆线时钟", "滚珠荡秋千", "图17.1", "惠更斯", "用于改进钟摆而得来的"]
all_in_33 = True
for kw in keywords:
    in_32 = kw in p32_txt
    in_33 = kw in p33_txt
    in_34 = kw in p34_txt
    print(f"   Keyword '{kw}': Page 32={in_32}, Page 33={in_33}, Page 34={in_34}")
    if in_32 or in_34 or not in_33:
        all_in_33 = False

p33_lines = [l.strip() for l in p33_txt.splitlines() if l.strip()]
p34_lines = [l.strip() for l in p34_txt.splitlines() if l.strip()]

print(f"\n   Page 33 bottom 3 lines:")
for l in p33_lines[-3:]:
    print(f"     {repr(l)}")

print(f"\n   Page 34 top 4 lines:")
for l in p34_lines[:4]:
    print(f"     {repr(l)}")

# Header/Heading check
p34_starts_clean = ("18. 短幅摆线和长幅摆线" in p34_lines[0] or "18. 短幅摆线和长幅摆线" in p34_lines[1] or "18. 短幅摆线和长幅摆线" in p34_lines[2])
sec17_clean = all_in_33 and ("用于改进钟摆而得来的。" in p33_lines) and ("用于改进钟摆而得来的。" not in p34_lines)

# Page 33 footer margin
p33_blocks = sorted([b for b in doc[32].get_text("blocks") if b[4].strip()], key=lambda b: b[3])
p33_footer = p33_blocks[-1]
p33_last_content = p33_blocks[-2]
gap_p33 = p33_footer[1] - p33_last_content[3]
print(f"\n   Page 33 text-to-footer gap: {gap_p33:.2f} pt")

if sec17_clean and gap_p33 > 5:
    print("   [PASS] Section 17 perfectly converged on Page 33 with 0 orphan lines and safe footer margin.")
else:
    print("   [FAIL] Section 17 did not converge cleanly.")
    sys.exit(1)