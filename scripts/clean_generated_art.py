import sys
import os
import cv2
import numpy as np


def clean_line_art(input_path: str, output_path: str):
    # 使用 np.fromfile + imdecode 以兼容 Windows 中文路径
    raw = np.fromfile(input_path, dtype=np.uint8)
    img = cv2.imdecode(raw, cv2.IMREAD_COLOR)
    if img is None:
        raise FileNotFoundError(f"Cannot read {input_path}")

    # 转为灰度并做对比度拉伸：高于 225 的浅灰背景强制变白(255)，低于 45 的暗线增强为纯黑
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    out = np.clip((gray.astype(np.float32) - 45.0) * (255.0 / (225.0 - 45.0)), 0, 255).astype(np.uint8)

    # 裁剪四周纯白多余留白，保留 12px 内边距
    mask = out < 245
    coords = np.argwhere(mask)
    if coords.size > 0:
        y0, x0 = coords.min(axis=0)
        y1, x1 = coords.max(axis=0) + 1
        pad = 12
        y0 = max(0, y0 - pad)
        x0 = max(0, x0 - pad)
        y1 = min(out.shape[0], y1 + pad)
        x1 = min(out.shape[1], x1 + pad)
        out = out[y0:y1, x0:x1]

    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    ext = os.path.splitext(output_path)[1] or ".png"
    ok, buf = cv2.imencode(ext, out)
    if not ok:
        raise RuntimeError(f"Failed to encode image for {output_path}")
    buf.tofile(output_path)
    print(f"Cleaned line art saved to {output_path} ({out.shape[1]}x{out.shape[0]})")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python clean_generated_art.py <input> <output>")
        sys.exit(1)
    clean_line_art(sys.argv[1], sys.argv[2])
