"""将 www.0928.love 主页二维码贴到请柬的预留白色区域。

用法：
  python paste_qr.py --set westlake      # 处理某套装全部变体
  python paste_qr.py --set guoxue --only a

原理：按模板坐标缩放得到搜索窗口，在生成图内检测近白色方块轮廓；
留白区为矩形（如举牌牌面）时，内切正方形居中贴码，四周白边充当安静区，
输出 *_final.png。

说明：卡片二维码为主页码 img/site_qr.png（网页内已有出席登记入口，
卡片不再直接放登记码），便于长辈扫码直达主页。
"""

import argparse
import os

import cv2
import numpy as np

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
QR_PATH = os.path.join(CURRENT_DIR, "..", "..", "img", "site_qr.png")

TEMPLATE_W, TEMPLATE_H = 2048, 1365

# 各套装模板中的二维码留白矩形 (x, y, w, h)，与 generate_invitation_card.py 同步
SET_RECTS = {
    "guoxue": {
        "a": (150, 900, 350, 350),
        "b": (170, 880, 400, 400),
        "c": (1560, 930, 330, 330),
    },
    "westlake": {  # 举牌牌面，三变体同布局
        "a": (1328, 654, 384, 292),
        "b": (1328, 654, 384, 292),
        "c": (1328, 654, 384, 292),
    },
}


def detect_white_square(img, cx, cy, win):
    """在以 (cx,cy) 为中心、win 为边长的窗口内找最大近白方块的 bbox。"""
    h, w = img.shape[:2]
    x0, y0 = max(int(cx - win / 2), 0), max(int(cy - win / 2), 0)
    x1, y1 = min(int(cx + win / 2), w), min(int(cy + win / 2), h)
    roi = img[y0:y1, x0:x1]

    mask = cv2.inRange(roi, np.array([235, 235, 235]), np.array([255, 255, 255]))
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return None
    c = max(contours, key=cv2.contourArea)
    bx, by, bw, bh = cv2.boundingRect(c)
    if min(bw, bh) / max(bw, bh) < 0.7:  # 不够方
        return None
    return (x0 + bx, y0 + by, bw, bh)


def paste(set_name, key, qr_img):
    card_path = os.path.join(CURRENT_DIR, "outputs", f"invitation_{set_name}_{key}.png")
    out_path = os.path.join(CURRENT_DIR, "outputs", f"invitation_{set_name}_{key}_final.png")
    img = cv2.imread(card_path)
    if img is None:
        print(f"❌ 读取失败: {card_path}")
        return

    sx = img.shape[1] / TEMPLATE_W
    sy = img.shape[0] / TEMPLATE_H
    x, y, w, h = SET_RECTS[set_name][key]
    cx, cy = (x + w / 2) * sx, (y + h / 2) * sy

    win = max(w, h) * max(sx, sy) * 1.35
    rect = detect_white_square(img, cx, cy, win)
    if rect is not None and abs(rect[2] - w * sx) / (w * sx) <= 0.25 and abs(rect[3] - h * sy) / (h * sy) <= 0.25:
        bx, by, bw, bh = rect
        print(f"🔍 {set_name}/{key} 检测到留白: {bw}x{bh} @ ({bx},{by})")
    else:
        print(f"⚠️ {set_name}/{key} 检测结果不可信，使用模板缩放坐标")
        bx, by, bw, bh = int(x * sx), int(y * sy), int(w * sx), int(h * sy)

    # 矩形留白内切正方形居中贴码（白边充当安静区），内缩 6%
    side = min(bw, bh)
    m = int(side * 0.06)
    qr_side = side - 2 * m
    qx = bx + (bw - qr_side) // 2
    qy = by + (bh - qr_side) // 2
    qr = cv2.resize(qr_img, (qr_side, qr_side), interpolation=cv2.INTER_LANCZOS4)
    img[qy:qy + qr_side, qx:qx + qr_side] = qr

    cv2.imwrite(out_path, img)
    print(f"✅ {set_name}/{key} 成片 → {out_path}")


def main():
    parser = argparse.ArgumentParser(description="贴主页二维码到请柬留白区")
    parser.add_argument("--set", choices=list(SET_RECTS), default="westlake")
    parser.add_argument("--only", nargs="+", choices=["a", "b", "c"], default=None)
    args = parser.parse_args()

    qr_img = cv2.imread(QR_PATH)
    if qr_img is None:
        print(f"❌ 读取二维码失败: {QR_PATH}")
        raise SystemExit(1)

    for key in (args.only or list(SET_RECTS[args.set])):
        paste(args.set, key, qr_img)


if __name__ == "__main__":
    main()
