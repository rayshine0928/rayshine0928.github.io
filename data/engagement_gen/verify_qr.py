"""二维码可扫性校验：用 zxing-cpp 检测成图中的主页二维码能否解码出 0928.love。

背景：candy 套装改为「二维码随模板一起喂给模型、由模型融进画面」，
模型重画二维码有失真风险，故生成后必须校验可扫性（见 generate_invitation_card.py 的重试循环）。
cv2 自带检测器对中心带 logo 的码识别不稳，统一用 zxing-cpp。

用法：
  python verify_qr.py outputs/invitation_candy_a.png [更多图片…]
退出码：全部可扫 0，否则 1。

导入：
  from verify_qr import qr_scannable
"""

import argparse
import os

import cv2
import zxingcpp

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))

EXPECT = "0928.love"  # 主页码解码结果应包含的子串


def qr_scannable(path: str, expect: str = EXPECT) -> bool:
    """成图中二维码能解码且包含 expect 子串时返回 True。"""
    img = cv2.imread(path)
    if img is None:
        return False
    try:
        results = zxingcpp.read_barcodes(img)
    except Exception:
        return False
    return any(expect in r.text for r in results)


def main():
    parser = argparse.ArgumentParser(description="校验成图中二维码是否可扫（zxing-cpp）")
    parser.add_argument("images", nargs="+", help="待校验的成图路径")
    args = parser.parse_args()

    ok = True
    for p in args.images:
        good = os.path.isfile(p) and qr_scannable(p)
        print(f"{'✅' if good else '❌'} {p}")
        ok = ok and good
    raise SystemExit(0 if ok else 1)


if __name__ == "__main__":
    main()
