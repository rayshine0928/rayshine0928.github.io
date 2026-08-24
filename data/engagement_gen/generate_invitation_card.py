"""横版婚礼请柬生成：PIL 排版模板（竖排导字 + 印章 + 二维码留白）→ edit_image 润色。

用法：
  # 仅生成排版模板（本地预览，不调 API）
  python generate_invitation_card.py --templates-only
  # 生成某套装全部变体（模板 + 推理）
  python generate_invitation_card.py --set westlake
  # 只跑某几个变体
  python generate_invitation_card.py --set westlake --only a b

套装：
- guoxue  ：v2 国学风三布局（中堂对联 / 左文右图 / 手卷），卡通着中式婚服。
- westlake：v3 西湖主题三配色（宣墨朱砂 / 烟雨青绿 / 桃花胭脂），
  卡通用原装扮举牌款（cartoon_invitation.png），牌面内为二维码留白，
  贴码后呈现「噜噜噜妹举着主页二维码」的互动感；背景带西湖元素
  （雷峰塔 / 断桥 / 垂柳 / 荷花）。

设计说明：
- 系统无毛笔字体，模板中的浅色文字仅为「导字」：锁定文案、位置与竖排方向，
  prompt 要求模型以毛笔行楷原字重写，禁止宋体/印刷体。
- 二维码：模型重画二维码会失效，故模板留纯白方块，生成后由 paste_qr.py 贴入
  www.0928.love 主页码（img/site_qr.png）。
"""

import argparse
import asyncio
import os

from PIL import Image, ImageDraw, ImageFilter, ImageFont

from edit_image import edit_image

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
IMG_DIR = os.path.join(CURRENT_DIR, "..", "..", "img")
TEMPLATES_DIR = os.path.join(CURRENT_DIR, "templates")
OUTPUTS_DIR = os.path.join(CURRENT_DIR, "outputs")

# 导字字体：系统无手写/毛笔中文字体，用黑体做中性导引（最终字形由模型以毛笔重写）
HEITI_LIGHT = "/System/Library/Fonts/STHeiti Light.ttc"
HEITI_MED = "/System/Library/Fonts/STHeiti Medium.ttc"

W, H = 2048, 1365  # 3:2 横版

# 国学基础配色：宣纸 / 墨 / 朱砂 / 古金
PAPER = (244, 239, 229)
INK = (52, 46, 42)
CINNABAR = (171, 47, 40)
GOLD = (173, 138, 88)
GUIDE = (166, 158, 148)  # 浅墨灰导字


def guide(size, bold=False):
    return ImageFont.truetype(HEITI_MED if bold else HEITI_LIGHT, size)


def text_w(draw, text, font):
    l, t, r, b = draw.textbbox((0, 0), text, font=font)
    return r - l, b - t


def draw_center(draw, text, cx, y, font, fill):
    w, _ = text_w(draw, text, font)
    draw.text((cx - w / 2, y), text, font=font, fill=fill)


def draw_left(draw, text, x, y, font, fill):
    draw.text((x, y), text, font=font, fill=fill)


def draw_vtext(draw, text, cx, y, size, fill, gap=0.22):
    """竖排导字：一字一行、水平居中于 cx，自 y 向下；空格作小停顿。返回结束 y。"""
    step = size * (1 + gap)
    for ch in text:
        if ch == " ":
            y += step * 0.6
            continue
        f = guide(size)
        l, t, r, b = draw.textbbox((0, 0), ch, font=f)
        draw.text((cx - (r - l) / 2 - l, y - t), ch, font=f, fill=fill)
        y += step
    return y


def seal_guide(canvas, cx, cy, size, ch="囍", color=CINNABAR):
    """朱砂印章导引：红方印 + 白字，模型重画为篆刻质感。"""
    d = ImageDraw.Draw(canvas)
    h = size // 2
    d.rounded_rectangle([cx - h, cy - h, cx + h, cy + h], radius=size // 8, fill=color + (235,))
    f = guide(int(size * 0.62), bold=True)
    l, t, r, b = d.textbbox((0, 0), ch, font=f)
    d.text((cx - (r - l) / 2 - l, cy - (b - t) / 2 - t), ch, font=f, fill=PAPER + (255,))


def paste(canvas, path_or_img, box, scale_to_height=None):
    """RGBA 卡通图贴到 canvas；box=(x,y) 左上角，可选按高度等比缩放。"""
    img = path_or_img if isinstance(path_or_img, Image.Image) else Image.open(path_or_img)
    if img.mode != "RGBA":
        img = img.convert("RGBA")
    if scale_to_height:
        ratio = scale_to_height / img.height
        img = img.resize((int(img.width * ratio), scale_to_height), Image.LANCZOS)
    canvas.paste(img, box, img)
    return img


def cartoon(name):
    """优先中式婚服版卡通，未生成时回退原版。"""
    cn_path = os.path.join(IMG_DIR, f"cartoon_{name}_cn.png")
    return cn_path if os.path.isfile(cn_path) else os.path.join(IMG_DIR, f"cartoon_{name}.png")


def qr_placeholder(canvas, x, y, size, border=CINNABAR):
    """纯白正方形二维码留白区：柔和墨色投影 + 细边框，内部保持纯白空白。"""
    shadow = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    sd = ImageDraw.Draw(shadow)
    sd.rectangle([x + 6, y + 10, x + size + 6, y + size + 10], fill=INK + (40,))
    shadow = shadow.filter(ImageFilter.GaussianBlur(14))
    canvas.alpha_composite(shadow)
    d = ImageDraw.Draw(canvas)
    d.rectangle([x, y, x + size, y + size], fill=(255, 255, 255, 255))
    d.rectangle([x, y, x + size, y + size], outline=border + (255,), width=3)


def white_board(canvas, x, y, w, h):
    """把卡通举牌的牌面覆盖为纯白留白（保留牌框与手），供贴码。"""
    d = ImageDraw.Draw(canvas)
    d.rectangle([x, y, x + w, y + h], fill=(255, 255, 255, 255))


def new_canvas(bg=PAPER):
    return Image.new("RGBA", (W, H), bg + (255,))


# ============================================================
# guoxue 套装
# ============================================================
# 变体 A — 中堂对联式：囍印居中、双联护翼、卡通居下
def build_a():
    canvas = new_canvas()
    d = ImageDraw.Draw(canvas)
    d.rectangle([60, 60, W - 60, H - 60], outline=INK + (255,), width=3)
    d.rectangle([84, 84, W - 84, H - 84], outline=GOLD + (200,), width=1)

    seal_guide(canvas, W / 2, 190, 150)
    draw_center(d, "李笑然 严瑞", W / 2, 380, guide(118), GUIDE)
    draw_center(d, "谨订于 农历丙午年八月十八 · 公元二〇二六年九月廿八日", W / 2, 560, guide(40), GUIDE)
    draw_center(d, "恭请 阖第光临", W / 2, 650, guide(50), GUIDE)

    draw_vtext(d, "两姓联姻 一堂缔约", W - 230, 260, 62, GUIDE)
    draw_vtext(d, "良缘永结 匹配同称", 230, 260, 62, GUIDE)

    paste(canvas, cartoon("hero"), (W // 2 - 230, 760), scale_to_height=470)

    qr_placeholder(canvas, 150, 900, 350)
    draw_vtext(d, "扫码观礼", 620, 950, 44, GUIDE)
    draw_center(d, "www.0928.love", 620, 1180, guide(28), GUIDE)

    draw_left(d, "席设 杭州西湖 · 六通宾馆", 1450, 1200, guide(38), GUIDE)
    return canvas


# 变体 B — 左文右图：五列竖排右起 + 举牌卡通
def build_b():
    canvas = new_canvas()
    d = ImageDraw.Draw(canvas)
    d.rectangle([70, 70, W - 70, H - 70], outline=CINNABAR + (160,), width=2)
    d.rectangle([90, 90, W - 90, H - 90], outline=GOLD + (160,), width=1)

    draw_vtext(d, "谨订于农历丙午年八月十八", 960, 180, 46, GUIDE)
    draw_vtext(d, "公元二〇二六年九月廿八日", 860, 180, 46, GUIDE)
    y_end = draw_vtext(d, "李笑然 严瑞", 700, 180, 100, GUIDE)
    draw_vtext(d, "举行婚典 恭请阖第光临", 540, 180, 46, GUIDE)
    draw_vtext(d, "席设杭州西湖六通宾馆", 420, 180, 46, GUIDE)
    seal_guide(canvas, 700, y_end + 90, 90)

    qr_placeholder(canvas, 170, 880, 400)
    draw_left(d, "扫码观礼", 610, 1000, guide(44), GUIDE)
    draw_left(d, "www.0928.love", 610, 1075, guide(32), GUIDE)

    paste(canvas, cartoon("invitation"), (1080, 240), scale_to_height=880)
    return canvas


# 变体 C — 手卷式：左图右文、右上囍印
def build_c():
    canvas = new_canvas()
    d = ImageDraw.Draw(canvas)
    L, T = 70, 70
    tick, th = 110, 4
    for (x, y, dx, dy) in [(L, T, 1, 1), (W - L, T, -1, 1), (L, H - T, 1, -1), (W - L, H - T, -1, -1)]:
        d.line([(x, y), (x + tick * dx, y)], fill=INK + (255,), width=th)
        d.line([(x, y), (x, y + tick * dy)], fill=INK + (255,), width=th)

    paste(canvas, cartoon("hero"), (140, 230), scale_to_height=950)

    seal_guide(canvas, 1930, 130, 120)
    draw_vtext(d, "两姓联姻 一堂缔约", 1930, 220, 46, GUIDE)
    draw_vtext(d, "良缘永结 匹配同称", 1830, 220, 46, GUIDE)
    draw_vtext(d, "李笑然 严瑞", 1660, 220, 96, GUIDE)
    draw_vtext(d, "谨订于农历丙午年八月十八", 1500, 220, 44, GUIDE)
    draw_vtext(d, "公元二〇二六年九月廿八日", 1400, 220, 44, GUIDE)
    draw_vtext(d, "恭请 阖第光临", 1270, 220, 44, GUIDE)

    draw_center(d, "扫码观礼 · www.0928.love", 1725, 875, guide(32), GUIDE)
    qr_placeholder(canvas, 1560, 930, 330)

    draw_left(d, "席设 杭州西湖 · 六通宾馆", 150, 1240, guide(40), GUIDE)
    return canvas


GUOXUE_COMMON = (
    "Redraw this reference layout as a high-end horizontal Chinese wedding invitation card with guoxue "
    "(traditional Chinese literati) aesthetics: warm xuan (rice) paper texture background with subtle fiber "
    "grain. The gray text in the reference is only a POSITIONAL GUIDE — render it as elegant ink BRUSH "
    "CALLIGRAPHY (xingkai / running-regular style, warm and approachable like a handwritten letter, natural "
    "stroke weight and dry-brush ink touches) in ink-black, with EXACTLY the same characters, same positions "
    "and same orientation (vertical columns read top-to-bottom, right-to-left column order). Absolutely no "
    "printed/Song/Ming typefaces, no gray text in the final. The exact strings to appear, and nothing else: "
    "{texts}. The tiny Latin string 'www.0928.love' may use a refined handwritten-style serif. The red square "
    "with a white character is a seal guide: render it as a cinnabar seal stamp with carved seal-script feel. "
    "The white square with thin border is a reserved blank area for a QR code: keep it perfectly blank and "
    "pure white inside, do not draw anything inside it, keep its size and position. The cartoon hippo couple "
    "in traditional Chinese wedding attire must stay faithful to the reference (same faces, poses, outfits), "
    "crisp and high-resolution, softly grounded with a gentle shadow. Palette restricted to ink black, "
    "cinnabar seal red and muted antique gold on xuan paper. Restrained traditional motifs only where the "
    "composition allows: faint ink-wash auspicious clouds or distant mountains, thin gold hairlines. "
    "Cohesive, airy, elegant. No extra text, no watermark."
)

GUOXUE_TEXTS = {
    "a": [
        "囍", "李笑然 严瑞", "谨订于 农历丙午年八月十八 · 公元二〇二六年九月廿八日",
        "恭请 阖第光临", "两姓联姻 一堂缔约", "良缘永结 匹配同称",
        "扫码观礼", "www.0928.love", "席设 杭州西湖 · 六通宾馆",
    ],
    "b": [
        "囍", "谨订于农历丙午年八月十八", "公元二〇二六年九月廿八日", "李笑然 严瑞",
        "举行婚典 恭请阖第光临", "席设杭州西湖六通宾馆", "扫码观礼", "www.0928.love",
    ],
    "c": [
        "囍", "两姓联姻 一堂缔约", "良缘永结 匹配同称", "李笑然 严瑞",
        "谨订于农历丙午年八月十八", "公元二〇二六年九月廿八日", "恭请 阖第光临",
        "扫码观礼", "www.0928.love", "席设 杭州西湖 · 六通宾馆",
    ],
}

GUOXUE_NOTES = {
    "a": (
        "Symmetric Chinese hall composition: cinnabar 囍 seal stamp top center, large horizontal name line "
        "and two date/invitation lines centered, one vertical couplet column at the far right and one at "
        "the far left, cartoon couple at bottom center, QR blank square at bottom left with a vertical "
        "caption beside it, venue line at bottom right."
    ),
    "b": (
        "Composition as in the reference: five vertical calligraphy columns on the left half reading "
        "right-to-left (the large-character column is the couple's names, with a small cinnabar name seal "
        "below it), cartoon couple holding a red 囍 invitation board on the right, QR blank square at the "
        "bottom left with its caption to the right of the square."
    ),
    "c": (
        "Handscroll composition: cartoon couple on the left, vertical calligraphy columns on the right "
        "reading right-to-left (the large-character column is the couple's names), 囍 seal at the top "
        "right, QR blank square at the bottom right with its caption above, venue line at the bottom "
        "left, faint ink-wash distant mountains along the bottom edge, thin corner ticks as the only frame."
    ),
}


# ============================================================
# westlake 套装：原装扮卡通举牌 + 西湖元素 + 三配色主题
# ============================================================
# 卡通举牌贴图参数与牌面留白矩形（由 cartoon_invitation.png 牌框实测换算）
WL_CARTOON_BOX = (1080, 230)
WL_CARTOON_H = 880
WL_BOARD = (1328, 654, 384, 292)  # (x, y, w, h) 模板坐标

THEMES = {
    "a": {
        "name": "宣墨朱砂",
        "paper": (244, 239, 229), "ink": (52, 46, 42), "frame": (52, 46, 42),
        "gold": (173, 138, 88), "seal": (171, 47, 40), "guide": (150, 142, 132),
        "palette": (
            "warm xuan-paper cream background; ink-black brush calligraphy and outer frame; cinnabar red "
            "seal; muted antique gold hairlines; the West Lake panorama along the bottom in pure ink-wash "
            "grayscale with a whisper of gold on the pagoda roof; willow branches in faint ink"
        ),
    },
    "b": {
        "name": "烟雨青绿",
        "paper": (236, 242, 239), "ink": (40, 62, 64), "frame": (74, 124, 132),
        "gold": (146, 140, 104), "seal": (171, 47, 40), "guide": (128, 146, 144),
        "palette": (
            "pale celadon-tinted xuan paper; deep teal-ink brush calligraphy; frame in muted dai-blue; "
            "accents in mineral azurite blue and malachite green (blue-green shanshui style); one cinnabar "
            "red seal as the single warm counterpoint; the West Lake panorama along the bottom in mineral "
            "blue-green shanshui with misty-rain softness; willow branches in soft malachite green; lotus "
            "leaves in muted green"
        ),
    },
    "c": {
        "name": "桃花胭脂",
        "paper": (248, 239, 234), "ink": (72, 52, 52), "frame": (186, 110, 116),
        "gold": (196, 152, 110), "seal": (186, 60, 72), "guide": (158, 136, 134),
        "palette": (
            "warm blush-tinted xuan paper; deep warm umber brush calligraphy; frame and ornamental accents "
            "in rouge pink and peach-blossom tones; antique gold hairlines; deep rouge seal; the West Lake "
            "panorama along the bottom in light ink washed with rouge, a few faint peach-blossom petals "
            "drifting; willow branches in warm gray-rose"
        ),
    },
}

WESTLAKE_TEXTS = [
    "囍", "谨订于农历丙午年八月十八", "公元二〇二六年九月廿八日", "李笑然 严瑞",
    "举行婚典 恭请阖第光临", "席设杭州西湖六通宾馆", "扫码观礼 · www.0928.love",
]


def build_westlake(theme):
    pal = THEMES[theme]
    canvas = new_canvas(pal["paper"])
    d = ImageDraw.Draw(canvas)
    d.rectangle([70, 70, W - 70, H - 70], outline=pal["frame"] + (200,), width=2)
    d.rectangle([92, 92, W - 92, H - 92], outline=pal["gold"] + (160,), width=1)

    # 左侧竖排文案（右起阅读）
    draw_vtext(d, "谨订于农历丙午年八月十八", 960, 180, 46, pal["guide"])
    draw_vtext(d, "公元二〇二六年九月廿八日", 860, 180, 46, pal["guide"])
    y_end = draw_vtext(d, "李笑然 严瑞", 700, 180, 100, pal["guide"])
    draw_vtext(d, "举行婚典 恭请阖第光临", 540, 180, 46, pal["guide"])
    draw_vtext(d, "席设杭州西湖六通宾馆", 420, 180, 46, pal["guide"])
    seal_guide(canvas, 700, y_end + 90, 90, color=pal["seal"])

    # 右侧：原装扮卡通举牌，牌面覆盖为二维码留白（手压牌边 → 举码互动）
    paste(canvas, os.path.join(IMG_DIR, "cartoon_invitation.png"), WL_CARTOON_BOX, scale_to_height=WL_CARTOON_H)
    x, y, w, h = WL_BOARD
    white_board(canvas, x, y, w, h)
    draw_center(d, "扫码观礼 · www.0928.love", x + w / 2, 1150, guide(34), pal["guide"])
    return canvas


WESTLAKE_COMMON = (
    "Redraw this reference layout as a high-end horizontal Chinese wedding invitation card celebrating a "
    "wedding at Hangzhou West Lake, in guoxue aesthetics. Palette: {palette}. The light gray text is only a "
    "POSITIONAL GUIDE — render it as elegant ink BRUSH CALLIGRAPHY (xingkai / running-regular, warm "
    "handwritten feel, natural stroke weight) tinted in the palette's ink color, with EXACTLY the same "
    "characters, same positions and same vertical orientation (columns read top-to-bottom, right-to-left). "
    "Absolutely no printed/Song/Ming typefaces, no gray guide color in the final. The exact strings to "
    "appear, and nothing else: {texts}. The tiny Latin string 'www.0928.love' may use a refined handwritten-"
    "style serif. The small red square with a white character is a seal guide: render it as a carved seal "
    "stamp in the palette's seal color. The cartoon hippo couple must stay faithful to the reference: "
    "ORIGINAL outfits (groom in black tuxedo with red bowtie and strawberry-print trousers, bride in white "
    "lace dress with veil), golden-orange skin (do NOT whiten), same cute faces and the same joyful pose "
    "holding their board, hands gripping the board edges, crisp and high-resolution. The pure white "
    "rectangle inside the couple's board is a reserved blank area for a QR code: keep it perfectly blank "
    "and pure white, keep the board's thin golden frame and the hands exactly as in the reference, do not "
    "draw anything inside the white area. Replace the floating pink hearts with a few tiny sparkles or "
    "petals matching the palette. West Lake elements, faint and traditional: Leifeng Pagoda silhouette on a "
    "distant hill and the Broken Bridge arch along the bottom edge, slender willow branches hanging from a "
    "top corner, lotus flowers and leaves near the bottom. Keep all background motifs very muted so the "
    "cartoon couple remains the focal point; every color strictly within the stated palette so the whole "
    "card feels harmonious with no jarring hues. No extra text, no watermark."
)


SETS = {
    "guoxue": {
        key: {
            "build": {"a": build_a, "b": build_b, "c": build_c}[key],
            "texts": GUOXUE_TEXTS[key],
            "prompt": GUOXUE_COMMON.format(texts=" / ".join(f"「{t}」" for t in GUOXUE_TEXTS[key]))
            + " " + GUOXUE_NOTES[key],
        }
        for key in ("a", "b", "c")
    },
    "westlake": {
        key: {
            "build": (lambda k: lambda: build_westlake(k))(key),
            "texts": WESTLAKE_TEXTS,
            "prompt": WESTLAKE_COMMON.format(
                palette=THEMES[key]["palette"],
                texts=" / ".join(f"「{t}」" for t in WESTLAKE_TEXTS),
            ),
        }
        for key in ("a", "b", "c")
    },
}

PRIMARY_SIZE = "3072x2048"
FALLBACK_SIZE = "1536x1024"


async def generate(set_name: str, key: str, size: str):
    variant = SETS[set_name][key]
    template_path = os.path.join(TEMPLATES_DIR, f"invitation_{set_name}_{key}.png")
    canvas = variant["build"]()
    canvas.convert("RGB").save(template_path, quality=95)
    print(f"📐 {set_name}/{key}（{THEMES[key]['name'] if set_name == 'westlake' else '国学'}）模板 → {os.path.basename(template_path)}")

    out_path = os.path.join(OUTPUTS_DIR, f"invitation_{set_name}_{key}.png")
    kind, payload = await edit_image(template_path, prompt=variant["prompt"], size=size)
    if kind == "error" and "size" in str(payload).lower():
        print(f"⚠️ 尺寸 {size} 不支持，回退 {FALLBACK_SIZE}")
        kind, payload = await edit_image(template_path, prompt=variant["prompt"], size=FALLBACK_SIZE)
    if kind == "error":
        print(f"❌ {set_name}/{key} 失败: {payload}")
        return
    with open(out_path, "wb") as f:
        f.write(payload)
    print(f"✅ {set_name}/{key} → {out_path}")


async def main_async(args):
    os.makedirs(TEMPLATES_DIR, exist_ok=True)
    os.makedirs(OUTPUTS_DIR, exist_ok=True)
    keys = args.only or list(SETS[args.set])
    if args.templates_only:
        for k in keys:
            canvas = SETS[args.set][k]["build"]()
            p = os.path.join(TEMPLATES_DIR, f"invitation_{args.set}_{k}.png")
            canvas.convert("RGB").save(p, quality=95)
            print(f"📐 {args.set}/{k} 模板 → {p}")
        return 0
    for k in keys:  # 串行调用，避免限流
        await generate(args.set, k, args.size)
    return 0


def main():
    parser = argparse.ArgumentParser(description="横版请柬生成（模板排版 + 推理润色），多套装多配色")
    parser.add_argument("--set", choices=list(SETS), default="westlake", help="套装：westlake 西湖三配色 / guoxue 国学三布局")
    parser.add_argument("--only", nargs="+", choices=["a", "b", "c"], default=None, help="只生成指定变体")
    parser.add_argument("--templates-only", action="store_true", help="只输出本地排版模板，不调 API")
    parser.add_argument("--size", default=PRIMARY_SIZE, help="输出尺寸，默认 3072x2048 横版")
    args = parser.parse_args()
    raise SystemExit(asyncio.run(main_async(args)))


if __name__ == "__main__":
    main()
