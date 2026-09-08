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
- scene   ：v4 立体糖果西湖三景（断桥 / 雷峰塔 / 莲舟），卡通走进景中。
- candy   ：v5 糖果动态互动版——真实二维码作为牌面道具直接拼进模板，
  由模型整体融进画面（手部握框、投影、糖果框饰），不再后贴；
  卡通每变体一个动态姿势（奔跑举牌 / 攀爬挂码 / 跳跃欢呼），眼神看向二维码。

设计说明：
- 系统无毛笔字体，模板中的浅色文字仅为「导字」：锁定文案、位置与竖排方向，
  prompt 要求模型以毛笔行楷原字重写，禁止宋体/印刷体；全部文字均由模型生成。
- 二维码：guoxue/westlake/scene 为模板留纯白方块、生成后由 paste_qr.py 贴码；
  candy 套装改为真码入模板 + 模型融合，生成后用 verify_qr.py（zxing-cpp）
  校验可扫性，失败自动重试（--qr-retries）。
"""

import argparse
import asyncio
import os

from PIL import Image, ImageDraw, ImageFilter, ImageFont

from edit_image import edit_image
from verify_qr import qr_scannable

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
IMG_DIR = os.path.join(CURRENT_DIR, "..", "..", "img")
QR_PATH = os.path.join(IMG_DIR, "site_qr.png")  # 主页码，candy 套装真码入模板
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


def qr_prop(canvas, x, y, size, frame=GOLD):
    """真实主页二维码作为牌面道具入模板（candy 套装）：柔和投影 + 白牌 + 细框 + 真码。

    与 qr_placeholder 的「纯白留白、后贴码」相反：这里把 img/site_qr.png 原码
    拼进参考图，prompt 要求模型逐模块保真重绘并融入场景（握框的手、投影、框饰），
    成图再由 verify_qr 校验可扫性。
    """
    shadow = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    sd = ImageDraw.Draw(shadow)
    sd.rectangle([x + 8, y + 12, x + size + 8, y + size + 12], fill=INK + (50,))
    shadow = shadow.filter(ImageFilter.GaussianBlur(16))
    canvas.alpha_composite(shadow)
    d = ImageDraw.Draw(canvas)
    pad = int(size * 0.07)  # 白牌边距充当安静区
    d.rectangle([x - pad, y - pad, x + size + pad, y + size + pad], fill=(255, 255, 255, 255))
    d.rectangle([x - pad, y - pad, x + size + pad, y + size + pad], outline=frame + (255,), width=4)
    qr = Image.open(QR_PATH).convert("RGBA").resize((size, size), Image.BOX)
    canvas.paste(qr, (x, y), qr)


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


# ============================================================
# scene 套装：卡通走进立体糖果色西湖场景（光照阴影融为一体）
# ============================================================
def gradient_canvas(top, bottom):
    base = Image.new("RGBA", (W, H), bottom + (255,))
    topimg = Image.new("RGBA", (W, H), top + (255,))
    grad = Image.new("L", (1, H))
    for y in range(H):
        grad.putpixel((0, y), int(255 * y / H))
    return Image.composite(base, topimg, grad.resize((W, H)))


def scene_left(canvas, d, pal):
    """左侧竖排导字 + 名章，返回无（与 westlake 文案一致）。"""
    draw_vtext(d, "谨订于农历丙午年八月十八", 960, 180, 46, pal["guide"])
    draw_vtext(d, "公元二〇二六年九月廿八日", 860, 180, 46, pal["guide"])
    y_end = draw_vtext(d, "李笑然 严瑞", 700, 180, 100, pal["guide"])
    draw_vtext(d, "举行婚典 恭请阖第光临", 540, 180, 46, pal["guide"])
    draw_vtext(d, "席设杭州西湖六通宾馆", 420, 180, 46, pal["guide"])
    seal_guide(canvas, 700, y_end + 90, 90, color=pal["seal"])


def board_rect(box, ch):
    """cartoon_invitation 牌面在模板中的矩形（源图牌框实测 141,241,218,166 @500px）。"""
    s = ch / 500
    return (int(box[0] + 141 * s), int(box[1] + 241 * s), int(218 * s), int(166 * s))


SCENE_THEMES = {
    "a": {
        "name": "断桥·柳浪薄荷糖",
        "sky_top": (250, 246, 238), "sky_bottom": (222, 240, 232),
        "frame": (96, 146, 138), "gold": (146, 140, 104), "seal": (171, 47, 40),
        "guide": (126, 146, 142), "water": (168, 216, 203), "bridge": (235, 200, 186),
        "willow": (140, 190, 120), "lotus": (240, 170, 185), "sun": (255, 214, 140),
        "ink_desc": "deep teal ink",
        "palette": "cream-to-mint sky, mint-teal candy water, blush-pink stone bridge, fresh willow green, "
                   "soft pink lotus, warm honey sun, teal-ink calligraphy, one cinnabar seal",
    },
    "b": {
        "name": "雷峰·晴日桃金糖",
        "sky_top": (252, 246, 236), "sky_bottom": (250, 232, 216),
        "frame": (200, 140, 110), "gold": (214, 164, 96), "seal": (171, 47, 40),
        "guide": (158, 132, 116), "ground": (214, 232, 196), "pagoda": (240, 150, 120),
        "roof": (240, 190, 110), "tree": (150, 200, 140), "sun": (255, 208, 130),
        "ink_desc": "warm umber ink",
        "palette": "cream-to-peach sunny sky, coral pagoda tiers with honey-gold roofs, soft green meadow, "
                   "candy green trees, warm umber calligraphy, one cinnabar seal",
    },
    "c": {
        "name": "莲舟·藕粉莲糖",
        "sky_top": (228, 240, 246), "sky_bottom": (250, 246, 238),
        "frame": (186, 120, 140), "gold": (196, 152, 110), "seal": (186, 60, 72),
        "guide": (150, 132, 140), "water": (150, 205, 205), "hull": (215, 160, 110),
        "lotus": (242, 168, 186), "pad": (140, 190, 150), "hill": (196, 226, 220), "sun": (255, 214, 140),
        "ink_desc": "deep plum-brown ink",
        "palette": "pale blue-to-cream sky, teal candy water, candy pink lotus with green pads, warm honey "
                   "wood boat, soft mint hills, plum-brown calligraphy, one rouge seal",
    },
}

SCENE_CARTOON_H = 620


def build_scene_a():
    """断桥相会：情侣立于断桥拱顶，垂柳荷花薄荷糖水色。"""
    pal = SCENE_THEMES["a"]
    canvas = gradient_canvas(pal["sky_top"], pal["sky_bottom"])
    d = ImageDraw.Draw(canvas)
    d.rectangle([70, 70, W - 70, H - 70], outline=pal["frame"] + (180,), width=2)
    d.rectangle([92, 92, W - 92, H - 92], outline=pal["gold"] + (150,), width=1)

    d.ellipse([1770, 140, 1900, 270], fill=pal["sun"] + (255,))
    d.ellipse([1150, 150, 1360, 225], fill=(255, 255, 255, 235))
    d.ellipse([1860, 320, 2020, 385], fill=(255, 255, 255, 220))

    # 断桥拱身 + 水面 + 柳枝
    d.pieslice([1080, 900, 2060, 1980], 180, 360, fill=pal["bridge"] + (255,))
    d.rectangle([950, 1150, W - 60, 1295], fill=pal["water"] + (255,))
    for (ex, ey) in [(1050, 1190), (1300, 1230), (1700, 1200), (1950, 1240)]:
        d.ellipse([ex, ey, ex + 140, ey + 26], fill=(255, 255, 255, 120))
    for (wx, ln) in [(1905, 470), (1955, 560), (2005, 430)]:
        d.rounded_rectangle([wx, 60, wx + 26, ln], radius=13, fill=pal["willow"] + (200,))

    box = (1330, 360)
    paste(canvas, os.path.join(IMG_DIR, "cartoon_invitation.png"), box, scale_to_height=SCENE_CARTOON_H)
    bx, by, bw, bh = board_rect(box, SCENE_CARTOON_H)
    white_board(canvas, bx, by, bw, bh)

    d.ellipse([1080, 1180, 1180, 1260], fill=pal["lotus"] + (255,))
    d.ellipse([1030, 1230, 1150, 1270], fill=pal["willow"] + (220,))
    d.ellipse([1880, 1200, 1970, 1270], fill=pal["lotus"] + (255,))

    scene_left(canvas, d, pal)
    draw_center(d, "扫码观礼 · www.0928.love", 560, 1200, guide(34), pal["guide"])
    return canvas


def build_scene_b():
    """雷峰塔同游：糖果塔层金顶，情侣立于塔前石台。"""
    pal = SCENE_THEMES["b"]
    canvas = gradient_canvas(pal["sky_top"], pal["sky_bottom"])
    d = ImageDraw.Draw(canvas)
    d.rectangle([70, 70, W - 70, H - 70], outline=pal["frame"] + (180,), width=2)
    d.rectangle([92, 92, W - 92, H - 92], outline=pal["gold"] + (150,), width=1)

    d.ellipse([1120, 130, 1250, 260], fill=pal["sun"] + (255,))
    d.ellipse([1750, 180, 1950, 250], fill=(255, 255, 255, 235))
    d.ellipse([1400, 110, 1560, 170], fill=(255, 255, 255, 220))

    # 草地 + 糖果雷峰塔（五层圆角塔身 + 金顶檐）
    d.rectangle([950, 1120, W - 60, 1295], fill=pal["ground"] + (255,))
    d.rounded_rectangle([1280, 1040, 1960, 1120], radius=30, fill=(240, 226, 204, 255))
    cx = 1620
    for i, tw in enumerate([560, 480, 400, 320, 240]):
        y1 = 1040 - (i + 1) * 140
        d.rounded_rectangle([cx - tw // 2, y1, cx + tw // 2, y1 + 120], radius=24, fill=pal["pagoda"] + (255,))
        d.ellipse([cx - tw // 2 - 40, y1 - 26, cx + tw // 2 + 40, y1 + 6], fill=pal["roof"] + (255,))
    d.ellipse([cx - 14, 1040 - 5 * 140 - 60, cx + 14, 1040 - 5 * 140 - 6], fill=pal["gold"] + (255,))
    # 糖果树
    d.rounded_rectangle([1030, 1020, 1054, 1120], radius=12, fill=(160, 120, 90, 255))
    d.ellipse([970, 920, 1110, 1050], fill=pal["tree"] + (255,))

    box = (1250, 530)
    paste(canvas, os.path.join(IMG_DIR, "cartoon_invitation.png"), box, scale_to_height=SCENE_CARTOON_H)
    bx, by, bw, bh = board_rect(box, SCENE_CARTOON_H)
    white_board(canvas, bx, by, bw, bh)

    scene_left(canvas, d, pal)
    draw_center(d, "扫码观礼 · www.0928.love", 560, 1200, guide(34), pal["guide"])
    return canvas


def build_scene_c():
    """莲舟共渡：情侣立于圆木舟中，荷花三潭印月。"""
    pal = SCENE_THEMES["c"]
    canvas = gradient_canvas(pal["sky_top"], pal["sky_bottom"])
    d = ImageDraw.Draw(canvas)
    d.rectangle([70, 70, W - 70, H - 70], outline=pal["frame"] + (180,), width=2)
    d.rectangle([92, 92, W - 92, H - 92], outline=pal["gold"] + (150,), width=1)

    d.ellipse([1790, 140, 1920, 270], fill=pal["sun"] + (255,))
    d.ellipse([1150, 160, 1350, 230], fill=(255, 255, 255, 235))

    # 远山 + 湖水 + 三潭印月小石塔
    d.ellipse([950, 880, 1400, 1010], fill=pal["hill"] + (255,))
    d.ellipse([1500, 900, 2000, 1020], fill=pal["hill"] + (200,))
    d.rectangle([950, 980, W - 60, 1295], fill=pal["water"] + (255,))
    for (px, py) in [(1060, 1000), (1140, 1030), (1010, 1050)]:
        d.ellipse([px, py, px + 36, py + 46], fill=(235, 230, 220, 255))
        d.ellipse([px + 10, py - 14, px + 26, py + 2], fill=(235, 230, 220, 255))

    box = (1300, 430)
    paste(canvas, os.path.join(IMG_DIR, "cartoon_invitation.png"), box, scale_to_height=SCENE_CARTOON_H)
    bx, by, bw, bh = board_rect(box, SCENE_CARTOON_H)
    white_board(canvas, bx, by, bw, bh)

    # 船身压住脚部 + 前景荷花荷叶
    d.pieslice([1230, 960, 1990, 1330], 0, 180, fill=pal["hull"] + (255,))
    d.rounded_rectangle([1210, 940, 2010, 995], radius=26, fill=(190, 135, 90, 255))
    d.ellipse([1080, 1120, 1200, 1210], fill=pal["lotus"] + (255,))
    d.ellipse([1020, 1180, 1170, 1240], fill=pal["pad"] + (230,))
    d.ellipse([1930, 1100, 2020, 1180], fill=pal["lotus"] + (255,))
    d.ellipse([1860, 1180, 1990, 1240], fill=pal["pad"] + (230,))

    scene_left(canvas, d, pal)
    draw_center(d, "扫码观礼 · www.0928.love", 560, 1200, guide(34), pal["guide"])
    return canvas


SCENE_NOTES = {
    "a": "an arched stone Broken Bridge over mint water with the couple standing at the arch top, soft "
         "willow branches hanging from the top-right corner, candy lotus flowers and pads floating on the "
         "water, gentle wave highlights",
    "b": "a tall candy Leifeng Pagoda with rounded coral tiers and honey-gold eaves behind the couple "
         "standing on the stone platform, one round candy tree, warm sunny meadow ground",
    "c": "the couple standing in a rounded wooden boat floating among oversized candy lotus flowers and "
         "pads, three tiny Three-Pools-Mirroring-the-Moon stone mini-pagodas in the water at the left, soft "
         "mint distant hills",
}

SCENE_COMMON = (
    "Redraw this rough layout as a high-end horizontal wedding invitation card set at Hangzhou West Lake. "
    "STYLE: refined 3D candy / designer-toy diorama render — rounded volumetric shapes, soft glossy-matte "
    "candy colors, smooth clean surfaces, cute yet premium; NOT photorealistic. Bright sunny daylight from "
    "the upper left with consistent warm sunlight; believable soft lighting and shadows: the couple casts "
    "contact shadows where they stand, scenery objects have gentle ambient occlusion and warm rim light, so "
    "the cartoon characters truly exist INSIDE the scenery as one cohesive world. "
    "The flat colored shapes in the reference are only a composition draft — turn them into volumetric candy "
    "scenery exactly where they are: {scene_note}. "
    "The cartoon hippo couple must stay faithful to the reference: golden-orange skin (do NOT whiten), "
    "original outfits (groom black tuxedo with red bowtie and strawberry-print trousers, bride white lace "
    "dress with veil), same cute faces, relit by the same sunlight as the scene. The white rectangle on "
    "their board is a reserved blank QR area: keep it perfectly blank pure white, keep the board's thin "
    "golden frame and the hands gripping it; replace the floating hearts with a few tiny sparkles. "
    "The LEFT third stays a calm soft sky gradient reserved for text: render the light gray guide text as "
    "elegant ink BRUSH CALLIGRAPHY (xingkai, warm handwritten feel) in {ink_desc}, EXACTLY the same "
    "characters, same positions, same vertical orientation (columns read top-to-bottom, right-to-left); no "
    "printed/Song typefaces, no gray guide color. The exact strings to appear, and nothing else: {texts}. "
    "The small red square is a seal guide: render it as a carved seal stamp. "
    "All colors strictly within this harmonious candy palette: {palette}. No extra text, no watermark."
)

SCENE_TEXTS = [
    "囍", "谨订于农历丙午年八月十八", "公元二〇二六年九月廿八日", "李笑然 严瑞",
    "举行婚典 恭请阖第光临", "席设杭州西湖六通宾馆", "扫码观礼 · www.0928.love",
]


# ============================================================
# candy 套装：糖果动态互动版——真码入模板由模型融合，卡通每变体一个动态姿势
# ============================================================
CANDY_CARTOON = os.path.join(IMG_DIR, "cartoon_invitation.png")  # 身份锚，模型按 prompt 重摆姿势


def ladder(d, p0, p1, rail_dx, color, width=14, rungs=6):
    """糖果梯子草稿：双轨 + 横档；p0 底、p1 顶。"""
    d.line([p0, p1], fill=color + (255,), width=width)
    d.line([(p0[0] + rail_dx, p0[1]), (p1[0] + rail_dx, p1[1])], fill=color + (255,), width=width)
    for i in range(1, rungs + 1):
        t = i / (rungs + 1)
        x = p0[0] + (p1[0] - p0[0]) * t
        y = p0[1] + (p1[1] - p0[1]) * t
        d.line([(x - 4, y), (x + rail_dx + 4, y)], fill=color + (255,), width=width - 4)


def build_candy_a():
    """断桥·奔跑举牌：情侣拱顶蹦跳奔跑、共举二维码牌，眼神看码。"""
    pal = SCENE_THEMES["a"]
    canvas = gradient_canvas(pal["sky_top"], pal["sky_bottom"])
    d = ImageDraw.Draw(canvas)
    d.rectangle([70, 70, W - 70, H - 70], outline=pal["frame"] + (180,), width=2)
    d.rectangle([92, 92, W - 92, H - 92], outline=pal["gold"] + (150,), width=1)

    d.ellipse([1000, 130, 1130, 260], fill=pal["sun"] + (255,))
    d.ellipse([1160, 180, 1370, 255], fill=(255, 255, 255, 235))

    # 断桥拱身（拱顶 ~y950）+ 水面 + 柳枝
    d.pieslice([1000, 950, 2040, 1990], 180, 360, fill=pal["bridge"] + (255,))
    d.rectangle([900, 1180, W - 60, 1295], fill=pal["water"] + (255,))
    for (ex, ey) in [(980, 1210), (1250, 1245), (1700, 1215), (1930, 1250)]:
        d.ellipse([ex, ey, ex + 140, ey + 26], fill=(255, 255, 255, 120))
    for (wx, ln) in [(1905, 470), (1955, 560), (2005, 430)]:
        d.rounded_rectangle([wx, 60, wx + 26, ln], radius=13, fill=pal["willow"] + (200,))

    paste(canvas, CANDY_CARTOON, (1230, 380), scale_to_height=620)
    qr_prop(canvas, 1400, 560, 300)

    d.ellipse([1000, 1210, 1120, 1290], fill=pal["lotus"] + (255,))
    d.ellipse([950, 1255, 1090, 1295], fill=pal["willow"] + (220,))
    d.ellipse([1880, 1220, 1970, 1290], fill=pal["lotus"] + (255,))

    scene_left(canvas, d, pal)
    draw_center(d, "扫码观礼 · www.0928.love", 560, 1200, guide(34), pal["guide"])
    return canvas


def build_candy_b():
    """雷峰·攀爬挂码：新郎爬梯把码牌挂上塔身，新娘下方跳跃递工具。"""
    pal = SCENE_THEMES["b"]
    canvas = gradient_canvas(pal["sky_top"], pal["sky_bottom"])
    d = ImageDraw.Draw(canvas)
    d.rectangle([70, 70, W - 70, H - 70], outline=pal["frame"] + (180,), width=2)
    d.rectangle([92, 92, W - 92, H - 92], outline=pal["gold"] + (150,), width=1)

    d.ellipse([1080, 130, 1210, 260], fill=pal["sun"] + (255,))
    d.ellipse([1750, 180, 1950, 250], fill=(255, 255, 255, 235))

    # 草地 + 石台 + 糖果雷峰塔
    d.rectangle([950, 1120, W - 60, 1295], fill=pal["ground"] + (255,))
    d.rounded_rectangle([1280, 1040, 1960, 1120], radius=30, fill=(240, 226, 204, 255))
    cx = 1680
    for i, tw in enumerate([560, 480, 400, 320, 240]):
        y1 = 1040 - (i + 1) * 140
        d.rounded_rectangle([cx - tw // 2, y1, cx + tw // 2, y1 + 120], radius=24, fill=pal["pagoda"] + (255,))
        d.ellipse([cx - tw // 2 - 40, y1 - 26, cx + tw // 2 + 40, y1 + 6], fill=pal["roof"] + (255,))
    d.ellipse([cx - 14, 1040 - 5 * 140 - 60, cx + 14, 1040 - 5 * 140 - 6], fill=pal["gold"] + (255,))
    # 糖果树（移到石台左外，避让梯子与人物）
    d.rounded_rectangle([1000, 1020, 1024, 1120], radius=12, fill=(160, 120, 90, 255))
    d.ellipse([940, 920, 1080, 1050], fill=pal["tree"] + (255,))

    # 斜靠石台左缘的糖果梯（人物与码牌之间，清晰可见）
    ladder(d, (1300, 1100), (1480, 720), 55, (190, 140, 90))

    paste(canvas, CANDY_CARTOON, (1000, 520), scale_to_height=600)
    qr_prop(canvas, 1500, 450, 320)

    scene_left(canvas, d, pal)
    draw_center(d, "扫码观礼 · www.0928.love", 560, 1200, guide(34), pal["guide"])
    return canvas


def build_candy_c():
    """莲舟·跳跃欢迎：码牌立舟中画架，情侣并排跳跃欢呼、眼神看码。"""
    pal = SCENE_THEMES["c"]
    canvas = gradient_canvas(pal["sky_top"], pal["sky_bottom"])
    d = ImageDraw.Draw(canvas)
    d.rectangle([70, 70, W - 70, H - 70], outline=pal["frame"] + (180,), width=2)
    d.rectangle([92, 92, W - 92, H - 92], outline=pal["gold"] + (150,), width=1)

    d.ellipse([1790, 140, 1920, 270], fill=pal["sun"] + (255,))
    d.ellipse([1150, 160, 1350, 230], fill=(255, 255, 255, 235))

    # 远山 + 湖水 + 三潭印月小石塔
    d.ellipse([950, 880, 1400, 1010], fill=pal["hill"] + (255,))
    d.ellipse([1500, 900, 2000, 1020], fill=pal["hill"] + (200,))
    d.rectangle([950, 980, W - 60, 1295], fill=pal["water"] + (255,))
    for (px, py) in [(1010, 1000), (1090, 1030), (960, 1050)]:
        d.ellipse([px, py, px + 36, py + 46], fill=(235, 230, 220, 255))
        d.ellipse([px + 10, py - 14, px + 26, py + 2], fill=(235, 230, 220, 255))

    # 船身 + 舷缘 + 画架（撑住码牌）
    d.pieslice([1080, 960, 1920, 1330], 0, 180, fill=pal["hull"] + (255,))
    d.rounded_rectangle([1060, 940, 1940, 995], radius=26, fill=(190, 135, 90, 255))
    d.line([(1580, 780), (1540, 960)], fill=(160, 110, 70, 255), width=12)
    d.line([(1820, 780), (1860, 960)], fill=(160, 110, 70, 255), width=12)
    d.line([(1560, 880), (1840, 880)], fill=(160, 110, 70, 255), width=10)

    paste(canvas, CANDY_CARTOON, (1040, 430), scale_to_height=540)
    qr_prop(canvas, 1560, 440, 300)

    # 前景荷花荷叶
    d.ellipse([1000, 1120, 1120, 1210], fill=pal["lotus"] + (255,))
    d.ellipse([940, 1180, 1090, 1240], fill=pal["pad"] + (230,))
    d.ellipse([1930, 1100, 2020, 1180], fill=pal["lotus"] + (255,))
    d.ellipse([1860, 1180, 1990, 1240], fill=pal["pad"] + (230,))

    scene_left(canvas, d, pal)
    draw_center(d, "扫码观礼 · www.0928.love", 560, 1200, guide(34), pal["guide"])
    return canvas


CANDY_NOTES = {
    "a": {
        "scene": "an arched stone Broken Bridge over mint water, soft willow branches hanging from the "
                 "top-right corner, candy lotus flowers and pads floating on the water, gentle wave highlights",
        "pose": "the couple bounces across the bridge arch top toward the viewer in a lively running "
                "stride (one foot lifted each, bodies leaning forward), together carrying the QR signboard "
                "in front of them; the groom grips the frame with one paw and points at the QR with the "
                "other, the bride tilts her head toward the board; BOTH characters' eyes look at the QR "
                "code with delight; a few tiny candy sparkles trail behind them for motion",
    },
    "b": {
        "scene": "a tall candy Leifeng Pagoda with rounded coral tiers and honey-gold eaves on a stone "
                 "platform, a candy wooden ladder leaning against the platform's left edge, warm sunny "
                 "meadow ground, one round candy tree at the left of the platform",
        "pose": "the groom stands a few rungs up the ladder, both paws gripping the signboard frame as he "
                "hangs the QR signboard on the pagoda front, one foot raised on a rung; the bride below "
                "jumps on tiptoes reaching up to hand him a tiny candy hammer; both faces turned up with "
                "their eyes on the signboard",
    },
    "c": {
        "scene": "a rounded wooden boat floating among oversized candy lotus flowers and pads, the QR "
                 "signboard standing on a small wooden easel in the boat, three tiny "
                 "Three-Pools-Mirroring-the-Moon stone mini-pagodas in the water at the left, soft mint "
                 "distant hills",
        "pose": "the couple bounces in a joyful jump side by side in the boat, feet clearly off the floor, "
                "arms thrown up cheering, heads turned to look at the QR signboard beside them; tiny "
                "sparkles around them",
    },
}

CANDY_COMMON = (
    "Redraw this rough layout as a high-end horizontal wedding invitation card set at Hangzhou West Lake. "
    "STYLE: refined 3D candy / designer-toy diorama render — rounded volumetric shapes, soft glossy-matte "
    "candy colors, smooth clean surfaces, cute yet premium; NOT photorealistic. Bright sunny daylight from "
    "the upper left with consistent warm sunlight; believable soft lighting and shadows: the characters cast "
    "contact shadows, scenery objects have gentle ambient occlusion and warm rim light, so the cartoon "
    "characters truly exist INSIDE the scenery as one cohesive world. "
    "The flat colored shapes in the reference are only a composition draft — turn them into volumetric candy "
    "scenery exactly where they are: {scene_note}. "
    "CHARACTERS: the two cartoon hippos from the reference (groom: golden-orange skin, black tuxedo, red "
    "bowtie, strawberry-print trousers, little orange fruit with green sprout on his head; bride: "
    "golden-orange skin, white lace dress, veil, green sprout on her head) must keep identical faces, "
    "golden-orange skin (do NOT whiten) and outfits, but RE-POSE them into this lively action: {pose_note}. "
    "The small cream 'Wedding Invitation' card they hold in the reference must DISAPPEAR completely — the "
    "only board in the final image is the QR signboard. "
    "QR SIGNBOARD: the white board carrying the black-on-white QR code in the reference must be reproduced "
    "EXACTLY, module for module — crisp square black modules on a pure white field, front-facing, no tilt, "
    "no perspective, no rounded or restyled modules; it must remain perfectly scannable after rendering. "
    "Fuse the signboard into the world so it does not look pasted: a thin candy-gold frame, the characters' "
    "hands gripping the frame edges as described, a soft shadow beneath it, and at most a few tiny candy "
    "flowers or sparkles on the OUTER corners of the frame — never over the QR modules. "
    "The LEFT third stays a calm soft sky gradient reserved for text: render the light gray guide text as "
    "elegant ink BRUSH CALLIGRAPHY (xingkai, warm handwritten feel) in {ink_desc}, EXACTLY the same "
    "characters, same positions, same vertical orientation (columns read top-to-bottom, right-to-left); no "
    "printed/Song typefaces, no gray guide color. The exact strings to appear, and nothing else: {texts}. "
    "The small red square is a seal guide: render it as a carved seal stamp. "
    "All colors strictly within this harmonious candy palette: {palette}. No extra text, no watermark."
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
    "scene": {
        key: {
            "build": {"a": build_scene_a, "b": build_scene_b, "c": build_scene_c}[key],
            "texts": SCENE_TEXTS,
            "prompt": SCENE_COMMON.format(
                scene_note=SCENE_NOTES[key],
                ink_desc=SCENE_THEMES[key]["ink_desc"],
                palette=SCENE_THEMES[key]["palette"],
                texts=" / ".join(f"「{t}」" for t in SCENE_TEXTS),
            ),
        }
        for key in ("a", "b", "c")
    },
    "candy": {
        key: {
            "build": {"a": build_candy_a, "b": build_candy_b, "c": build_candy_c}[key],
            "texts": SCENE_TEXTS,
            "prompt": CANDY_COMMON.format(
                scene_note=CANDY_NOTES[key]["scene"],
                pose_note=CANDY_NOTES[key]["pose"],
                ink_desc=SCENE_THEMES[key]["ink_desc"],
                palette=SCENE_THEMES[key]["palette"],
                texts=" / ".join(f"「{t}」" for t in SCENE_TEXTS),
            ),
        }
        for key in ("a", "b", "c")
    },
}

SET_THEME_NAMES = {"westlake": THEMES, "scene": SCENE_THEMES, "candy": SCENE_THEMES}

# 真码入模板、模型融合二维码的套装：成图须过 verify_qr 可扫性校验，失败自动重试
QR_FUSED_SETS = {"candy"}

PRIMARY_SIZE = "3072x2048"
FALLBACK_SIZE = "1536x1024"


async def generate(set_name: str, key: str, size: str, qr_retries: int = 0):
    variant = SETS[set_name][key]
    template_path = os.path.join(TEMPLATES_DIR, f"invitation_{set_name}_{key}.png")
    canvas = variant["build"]()
    canvas.convert("RGB").save(template_path, quality=95)
    theme_name = SET_THEME_NAMES.get(set_name, {}).get(key, {}).get("name", "国学")
    print(f"📐 {set_name}/{key}（{theme_name}）模板 → {os.path.basename(template_path)}")

    out_path = os.path.join(OUTPUTS_DIR, f"invitation_{set_name}_{key}.png")
    need_scan = set_name in QR_FUSED_SETS
    attempts = qr_retries + 1 if need_scan else 1
    for attempt in range(1, attempts + 1):
        kind, payload = await edit_image(template_path, prompt=variant["prompt"], size=size)
        if kind == "error" and "size" in str(payload).lower():
            print(f"⚠️ 尺寸 {size} 不支持，回退 {FALLBACK_SIZE}")
            kind, payload = await edit_image(template_path, prompt=variant["prompt"], size=FALLBACK_SIZE)
        if kind == "error":
            print(f"❌ {set_name}/{key} 失败: {payload}")
            return
        with open(out_path, "wb") as f:
            f.write(payload)
        if not need_scan:
            print(f"✅ {set_name}/{key} → {out_path}")
            return
        if qr_scannable(out_path):
            print(f"✅ {set_name}/{key} → {out_path} 🔗 二维码可扫，无需后贴")
            return
        print(f"⚠️ {set_name}/{key} 第 {attempt} 次生成二维码不可扫"
              + ("，重试中…" if attempt < attempts else ""))
    print(f"❌ {set_name}/{key} {attempts} 次后二维码仍不可扫，保留最后一张待人工处理: {out_path}")


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
        await generate(args.set, k, args.size, args.qr_retries)
    return 0


def main():
    parser = argparse.ArgumentParser(description="横版请柬生成（模板排版 + 推理润色），多套装多配色")
    parser.add_argument("--set", choices=list(SETS), default="westlake", help="套装：westlake 西湖三配色 / guoxue 国学三布局")
    parser.add_argument("--only", nargs="+", choices=["a", "b", "c"], default=None, help="只生成指定变体")
    parser.add_argument("--templates-only", action="store_true", help="只输出本地排版模板，不调 API")
    parser.add_argument("--size", default=PRIMARY_SIZE, help="输出尺寸，默认 3072x2048 横版")
    parser.add_argument("--qr-retries", type=int, default=2,
                        help="真码融合套装（candy）二维码不可扫时的重试次数，默认 2")
    args = parser.parse_args()
    raise SystemExit(asyncio.run(main_async(args)))


if __name__ == "__main__":
    main()
