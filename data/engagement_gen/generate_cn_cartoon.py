"""中式婚服卡通资产生成：把西式礼服版噜噜/噜妹换装为国学风中式婚服。

用法：
  python generate_cn_cartoon.py            # 生成 hero + invitation 两张
  python generate_cn_cartoon.py --only hero

说明：
- 锁脸、锁姿态、锁 3D 渲染风格，只换服装道具：
  新郎 = 红长衫马褂 + 胸前披红绸花球；新娘 = 凤冠霞帔/红秀禾 + 囍字团扇。
- invitation 款的手举牌改为红底金框囍字婚书牌，漂浮爱心改为金色祥云顶饰。
- 输出保持透明背景；若模型返回纯白底，用四角 flood-fill 自动抠白。
"""

import argparse
import asyncio
import os

import cv2
import numpy as np
from PIL import Image

from edit_image import edit_image, edit_image_multi_ref

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
IMG_DIR = os.path.join(CURRENT_DIR, "..", "..", "img")

KEEP = (
    "CRITICAL: both characters keep their GOLDEN-ORANGE hippo skin and faces EXACTLY as in the reference — "
    "do NOT turn the skin white, pale or human-like; keep identical big eyes, blush cheeks, open smiling "
    "mouths, the little orange fruit with green sprout on the groom's head, the green sprout on the bride's "
    "head, identical poses, identical cute 3D render style, soft studio lighting, crisp high resolution. "
    "Change ONLY clothing and props as follows. "
)

HERO_CN_PROMPT = KEEP + (
    "Groom (left): traditional Chinese wedding attire — red changshan-magua (long gown with jacket) with fine "
    "gold trim and a red silk rosette ball with two hanging ribbons on the chest. Bride (right): red xiuhe "
    "wedding gown embroidered with gold phoenix and peony patterns, wearing a golden phoenix crown (fengguan) "
    "with short red tassels instead of the Western veil, holding a round silk tuanshan fan painted with a "
    "golden double-happiness (囍) character. Completely remove the black tuxedo, red bowtie, white Western "
    "wedding dress and veil. Keep transparent background."
)

INV_CN_PROMPT = KEEP + (
    "Same Chinese wedding attire as a classic pair: groom in red changshan-magua with gold trim and red silk "
    "rosette; bride in red xiuhe gown with gold phoenix embroidery and golden phoenix crown with red tassels, green sprout poking out from the top of the crown "
    "(replace strawberry-pattern shorts, black jacket, pink dress and veil). The board they hold becomes a "
    "vertical red lacquer invitation board with a thin gold frame and gold corner ornaments, one large golden "
    "double-happiness (囍) character in the center and two tiny vertical columns reading 婚书 at the top — no "
    "English text on the board. Replace the floating pink hearts with a few tiny golden auspicious-cloud "
    "sparkles. Keep transparent background."
)

# 二阶段回染：模型换装时倾向把金橙皮肤画白，用源图作颜色参考面板把皮肤染回。
RECOLOR_PROMPT = (
    "LEFT panel is the artwork to edit; RIGHT panel is the original character reference. In the LEFT panel, "
    "recolor the skin of both cartoon hippo characters — faces, ears, hands, every visible skin area — from "
    "white to EXACTLY the warm golden-orange hippo skin tone shown in the RIGHT panel, keeping all shading, "
    "blush cheeks, eyes and mouth details crisp. Do NOT change clothing, props, poses, composition, outlines "
    "or background. Keep transparent background."
)

ASSETS = {
    "hero": ("cartoon_hero.png", "cartoon_hero_cn.png", HERO_CN_PROMPT),
    "invitation": ("cartoon_invitation.png", "cartoon_invitation_cn.png", INV_CN_PROMPT),
}


def ensure_alpha(path: str) -> Image.Image:
    """模型若返回不透明白底图，从四角 flood-fill 抠白，恢复透明背景。"""
    img = Image.open(path).convert("RGBA")
    arr = np.array(img)
    if arr[..., 3].min() < 250:  # 已带透明背景
        return img
    bgr = cv2.cvtColor(arr[..., :3], cv2.COLOR_RGB2BGR)
    h, w = bgr.shape[:2]
    mask = np.zeros((h + 2, w + 2), np.uint8)
    for seed in ((0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1)):
        cv2.floodFill(
            bgr, mask, seed, (255, 0, 255),
            (10, 10, 10), (10, 10, 10),
            cv2.FLOODFILL_MASK_ONLY | (255 << 8),
        )
    arr[..., 3] = np.where(mask[1:-1, 1:-1] == 255, 0, 255).astype(np.uint8)
    return Image.fromarray(arr)


async def recolor(key: str):
    """二阶段：以源图为颜色参考，把换装图的白色皮肤染回金橙色。"""
    src, out_name, _ = ASSETS[key]
    out_path = os.path.join(IMG_DIR, out_name)
    kind, payload = await edit_image_multi_ref(
        [out_path, os.path.join(IMG_DIR, src)], prompt=RECOLOR_PROMPT, size="1024x1024"
    )
    if kind == "error":
        print(f"⚠️ {key} 回染失败（保留一阶段结果）: {payload}")
        return
    tmp = out_path + ".tmp.png"
    with open(tmp, "wb") as f:
        f.write(payload)
    ensure_alpha(tmp).save(out_path)
    os.remove(tmp)
    print(f"✅ {key} 肤色回染完成 → {os.path.basename(out_path)}")


async def generate(key: str, recolor_after=True):
    src, out_name, prompt = ASSETS[key]
    out_path = os.path.join(IMG_DIR, out_name)
    kind, payload = await edit_image(os.path.join(IMG_DIR, src), prompt=prompt, size="1024x1024")
    if kind == "error":
        print(f"❌ {key} 失败: {payload}")
        return
    tmp = out_path + ".tmp.png"
    with open(tmp, "wb") as f:
        f.write(payload)
    img = ensure_alpha(tmp)
    img.save(out_path)
    os.remove(tmp)
    print(f"✅ {key} 换装完成 → {os.path.basename(out_path)}")
    if recolor_after:
        await recolor(key)


async def main_async(args):
    for k in (args.only or list(ASSETS)):  # 串行，避免限流
        if args.recolor_only:
            await recolor(k)
        else:
            await generate(k)
    return 0


def main():
    parser = argparse.ArgumentParser(description="中式婚服卡通资产生成")
    parser.add_argument("--only", nargs="+", choices=list(ASSETS), default=None)
    parser.add_argument("--recolor-only", action="store_true", help="跳过换装，只对现有成图做肤色回染")
    args = parser.parse_args()
    raise SystemExit(asyncio.run(main_async(args)))


if __name__ == "__main__":
    main()
