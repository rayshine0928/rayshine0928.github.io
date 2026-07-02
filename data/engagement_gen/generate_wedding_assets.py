"""0928.love 婚礼网站素材生成器
基于 edit_image.py 的 API 调用，生成所有需要的图片素材。
每个素材有独立的 prompt，基于 img/ 中的真实照片生成。

用法：
  # 生成全部素材（按顺序逐张生成）
  python generate_wedding_assets.py --all

  # 只生成特定素材
  python generate_wedding_assets.py --asset hero_lawn_4k
  python generate_wedding_assets.py --asset cartoon_couple_hero
  python generate_wedding_assets.py --asset cartoon_story_01

  # 预览 prompt（不调用 API）
  python generate_wedding_assets.py --all --dry-run
"""

import argparse
import asyncio
import os
import sys

# 复用 edit_image.py 的 API 调用
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from edit_image import edit_image, download_image

# --- 路径配置 ---
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
IMG_DIR = os.path.abspath(os.path.join(CURRENT_DIR, "..", "..", "img"))
OUTPUT_DIR = os.path.abspath(os.path.join(CURRENT_DIR, "..", "..", "img"))

# --- 参考图路径 ---
PHOTO_REGISTRATION = os.path.join(IMG_DIR, "噜噜和噜妹的结婚登记照.jpg")
PHOTO_WEDDING_DRESS = os.path.join(IMG_DIR, "噜噜和噜妹的结婚婚纱照.jpg")
PHOTO_SELFIE = os.path.join(IMG_DIR, "噜噜（右）和噜妹（左）的自拍照.jpg")
PHOTO_BEACH = os.path.join(IMG_DIR, "噜噜和噜妹的海边婚礼照片.jpg")
PHOTO_BACK = os.path.join(IMG_DIR, "噜噜和噜妹背对着屏幕靠在一起的照片.jpg")
PHOTO_LAWN = os.path.join(IMG_DIR, "草坪婚礼_彩虹装饰实景.jpg")

# ================================================================
# 卡通风格通用规则（所有卡通类 prompt 共用）
# ================================================================
CARTOON_STYLE_RULES = """
CARTOON STYLE RULES (apply to ALL cartoon outputs):
- Art style: modern flat-vector illustration meets soft watercolor — clean lines, gentle gradients, hand-drawn warmth.
- Characters: transform the real couple in the reference photo into cute, chibi-proportion cartoon characters (head slightly larger, body simplified, ~1:3 head-to-body ratio). Keep recognizable features: hairstyle, glasses (if present), face shape, skin tone cues.
- Color palette: soft pastels + warm earth tones. Lawn green (#9CBE8C), cream (#FFF8F0), rose gold (#D4A0A7), warm peach, sky blue.
- Background: transparent PNG (no solid background fill, no white box).
- NO text, NO watermarks, NO logos, NO speech bubbles.
- High resolution, clean edges, suitable for web use at 2x retina.
"""

# ================================================================
# 8 个素材的 Prompt 定义
# ================================================================
ASSETS = {
    # --- 1. Hero 草坪婚礼超清背景 ---
    "hero_lawn_4k": {
        "input": PHOTO_LAWN,
        "output": "hero_lawn_4k.jpg",
        "size": "2560x1440",
        "prompt": """
PHOTO ENHANCEMENT — ULTRA HIGH RESOLUTION LAWN WEDDING SCENE.

Take this outdoor lawn wedding photo and enhance it to breathtaking 4K quality:

1. RESOLUTION & SHARPNESS: Upscale to 2560x1440 with crisp, tack-sharp detail. Enhance every texture — grass blades, flower petals, fabric folds, rainbow decoration ribbons, wooden arch grain.

2. COLOR & LIGHT: This is a sunny daytime outdoor lawn wedding. Boost natural sunlight warmth — golden hour glow filtering through trees, soft dappled light on the grass. The rainbow decorations should POP with vibrant saturated color (red, orange, yellow, green, blue, purple streamers/bunting). Green lawn should be lush, vivid, natural. Sky should be clear blue with soft white clouds.

3. ATMOSPHERE: Joyful, romantic, warm. Shallow depth of field on distant background elements, sharp focus on the wedding arch/rainbow decorations and foreground. Natural lens flare from sunlight (subtle, not exaggerated).

4. QUALITY: Photorealistic, 4K wedding venue photography, editorial grade. No AI over-smoothing, no plastic HDR, keep natural photographic texture and micro-contrast.

5. PRESERVE: Keep the original scene's layout, decorations, arch, rainbow elements, grass, trees — just enhance quality dramatically. Do NOT add people, do NOT change the scene composition.
""".strip(),
    },

    # --- 2. Hero 前景卡通噜噜噜妹 ---
    "cartoon_couple_hero": {
        "input": PHOTO_WEDDING_DRESS,
        "output": "cartoon_couple_hero.png",
        "size": "1024x1024",
        "prompt": CARTOON_STYLE_RULES + """

SPECIFIC SCENE:
Transform the couple in the reference wedding photo into cute cartoon characters for a wedding website hero section.

POSE: The couple stands side by side, holding hands, facing slightly toward each other with warm smiles. Full body, standing on a subtle soft shadow (no ground/floor drawn — just a gentle oval shadow beneath their feet for grounding).

WARDROBE (cartoonized):
- Man: Simple dark navy suit, white shirt, no tie, clean modern look. Short neat dark hair, gentle smile, warm brown eyes behind round metal-frame glasses.
- Woman: Simple elegant white wedding dress (simplified cartoon version — A-line silhouette, minimal detail), long dark hair flowing naturally over shoulders, gentle warm smile, soft natural makeup.

EXPRESSION: Both looking at each other with loving, happy expressions — the moment just before they say "I do."

COMPOSITION: Centered, full body visible from head to toe, surrounded by transparent background. The characters should be the star — clean, charming, instantly lovable.

SIZE: Characters should fill ~70% of the 1024x1024 canvas height.
""".strip(),
    },

    # --- 3-6. 四格故事连环画 ---
    "cartoon_story_01_first_met": {
        "input": PHOTO_SELFIE,
        "output": "cartoon_story_01_first_met.png",
        "size": "1024x768",
        "prompt": CARTOON_STYLE_RULES + """

SPECIFIC SCENE — "First Met" (初见):
A romantic meet-cute illustration in a cozy coffee shop or bookstore setting.

CHARACTERS: Cartoon versions of the couple, standing a few feet apart. They've just noticed each other. The man (short dark hair, round glasses, gentle expression) holds a book or coffee cup, looking slightly surprised but smiling softly. The woman (long dark hair, warm smile) is glancing up from what she's doing, a slight blush on her cheeks.

COMPOSITION: Warm indoor lighting, bookshelves or coffee bar in soft-focus background. The two characters are the main focus — a "moment frozen in time" feeling. Gentle golden light between them suggesting an instant connection.

MOOD: Serendipity, warmth, the magic of first encounters.

BACKGROUND: Soft watercolor-wash indoor scene (coffee shop / library), warm amber lighting. NOT transparent — this is a full scene illustration.

STYLE NOTE: This should feel like a page from a high-end illustrated storybook — soft, dreamy, editorial.
""".strip(),
    },

    "cartoon_story_02_love": {
        "input": PHOTO_BEACH,
        "output": "cartoon_story_02_love.png",
        "size": "1024x768",
        "prompt": CARTOON_STYLE_RULES + """

SPECIFIC SCENE — "Fell in Love" (相爱):
A joyful outdoor illustration of the cartoon couple on an adventure together.

CHARACTERS: Cartoon versions of the couple walking along a scenic path — could be a beach at sunset, a mountain trail, or a cherry blossom-lined street. They're walking side by side, the woman's arm linked through the man's. Both are laughing, mid-conversation, completely at ease with each other.

COMPOSITION: Wide scenic background with the couple in the midground. Warm golden-pink sunset or soft spring afternoon lighting. Their silhouettes are recognizable — his glasses, her flowing hair.

WARDROBE (cartoonized): Casual outdoor clothes — light jackets or sweaters, comfortable walking shoes. Colors in warm earth tones.

MOOD: Freedom, joy, companionship, "the whole world is ours."

BACKGROUND: Beautiful natural landscape in soft watercolor — NOT transparent. Full scene illustration.

STYLE NOTE: Studio Ghibli meets modern editorial illustration — lush nature, warm light, characters full of life.
""".strip(),
    },

    "cartoon_story_03_proposal": {
        "input": PHOTO_REGISTRATION,
        "output": "cartoon_story_03_proposal.png",
        "size": "1024x768",
        "prompt": CARTOON_STYLE_RULES + """

SPECIFIC SCENE — "The Proposal" (求婚):
A tender, intimate proposal moment illustration.

CHARACTERS: Cartoon version of the man is down on one knee, looking up with hopeful, loving eyes. He holds a small ring box with a sparkling diamond ring visible. The cartoon version of the woman stands before him, both hands covering her mouth in surprise and joy, eyes glistening with happy tears.

COMPOSITION: Close-up focus on the couple. Soft romantic background — maybe a beautiful sunset sky, a field of flowers, or fairy lights in a garden. Shallow depth effect — the couple is sharp, the background is soft dreamy bokeh.

WARDROBE (cartoonized): Both dressed nicely but simply — the man in a clean button-up shirt, the woman in a pretty dress. Not formal wedding attire — this is the proposal moment.

MOOD: Overwhelming love, vulnerability, the most important question of a lifetime.

BACKGROUND: Romantic soft-focus garden or sunset scene — NOT transparent. Full scene illustration.

DETAIL: The diamond ring should catch light with a tiny sparkle.
""".strip(),
    },

    "cartoon_story_04_wedding": {
        "input": PHOTO_LAWN,
        "output": "cartoon_story_04_wedding.png",
        "size": "1024x768",
        "prompt": CARTOON_STYLE_RULES + """

SPECIFIC SCENE — "The Wedding" (婚礼):
A joyful wedding day illustration that echoes the lawn wedding setting.

CHARACTERS: Cartoon versions of the couple standing under a beautiful outdoor wedding arch decorated with rainbow ribbons and flowers — matching the lawn wedding theme. The man in a suit, the woman in a white wedding dress with a simple veil. They're facing each other, hands clasped, exchanging vows.

COMPOSITION: The wedding arch frames the couple. Green lawn stretches around them. Rainbow decorations (bunting, ribbons, flowers) add joyful pops of color. Blue sky with soft white clouds above.

BACKGROUND: Full outdoor lawn wedding scene — NOT transparent. This should feel like a storybook version of the actual wedding venue.

MOOD: Pure happiness, celebration, "happily ever after begins now."

STYLE NOTE: This is the final panel of the story — the colors should be the brightest, the smiles the widest, the scene the most celebratory. Rainbow elements should tie visually to the real lawn wedding photo.
""".strip(),
    },

    # --- 7. 请柬区卡通 ---
    "cartoon_couple_invitation": {
        "input": PHOTO_REGISTRATION,
        "output": "cartoon_couple_invitation.png",
        "size": "800x1024",
        "prompt": CARTOON_STYLE_RULES + """

SPECIFIC SCENE:
Cartoon couple for the wedding invitation section. The characters hold a large elegant wedding invitation card between them.

POSE: Both characters face slightly toward the viewer. Between them, they hold a large cream-colored invitation card (the card faces the viewer). The man's hand supports the left side, the woman's hand supports the right side. Both are smiling warmly, invitingly.

COMPOSITION: Tall vertical composition. Characters from waist up. The invitation card is the centerpiece between them. Transparent background (PNG) — these characters will be placed as a floating element on the webpage.

STYLE: Elegant, warm, inviting. The characters should look like they're personally welcoming each guest to their wedding.

DETAIL: The invitation card can have subtle decorative elements (gold border, small heart or floral motif) but NO readable text — keep it as a beautiful prop.
""".strip(),
    },

    # --- 8. 场地区指路卡通 ---
    "cartoon_couple_guide": {
        "input": PHOTO_BACK,
        "output": "cartoon_couple_guide.png",
        "size": "800x800",
        "prompt": CARTOON_STYLE_RULES + """

SPECIFIC SCENE:
Cartoon couple in a playful "tour guide" pose for the venue information section.

POSE: Both characters are standing together, slightly angled. The man points forward/diagonally with one hand (like "the venue is this way!"). The woman holds a small map or has one hand up in a welcoming "come on in!" gesture. Both have cheerful, welcoming expressions.

COMPOSITION: Full body or 3/4 body characters. Dynamic, slightly diagonal pose — movement and welcome conveyed through body language. Transparent background (PNG).

WARDROBE (cartoonized): Semi-formal outdoor wedding attire — the man in a light blazer, the woman in a pretty outdoor-appropriate dress. Comfortable but elegant, fitting a lawn/garden wedding vibe.

MOOD: "Welcome! We're so glad you're here!" — warm, guiding, celebratory.

STYLE: Clean vector illustration with watercolor texture overlay. Characters pop clearly against any background.
""".strip(),
    },
}


# ================================================================
# 主逻辑
# ================================================================
async def generate_one(name: str, cfg: dict, dry_run: bool = False) -> bool:
    """生成单个素材"""
    input_path = cfg["input"]
    output_path = os.path.join(OUTPUT_DIR, cfg["output"])
    size = cfg.get("size", "1024x1024")
    prompt = cfg["prompt"]

    if not os.path.isfile(input_path):
        print(f"❌ 参考图不存在: {input_path}")
        return False

    print(f"\n{'='*60}")
    print(f"🎨 素材: {name}")
    print(f"   输入: {os.path.basename(input_path)}")
    print(f"   输出: {cfg['output']}")
    print(f"   尺寸: {size}")
    print(f"   Prompt 长度: {len(prompt)} 字符")
    print(f"{'='*60}")

    if dry_run:
        print(f"\n📝 PROMPT 预览:\n{'-'*40}\n{prompt}\n{'-'*40}\n")
        return True

    print("⏳ 调用 AI API...")
    kind, payload = await edit_image(input_path, prompt=prompt, size=size)

    if kind == "bytes":
        with open(output_path, "wb") as f:
            f.write(payload)
        print(f"✅ 已保存: {output_path}")
        return True
    elif kind == "url":
        ok = await download_image(payload, output_path)
        if ok:
            print(f"✅ 已从 URL 保存: {output_path}")
            return True
        print(f"❌ 下载失败: {payload}")
        return False
    else:
        print(f"❌ 生成失败: {payload}")
        return False


async def main():
    parser = argparse.ArgumentParser(description="0928.love 婚礼网站素材生成器")
    parser.add_argument("--all", action="store_true", help="生成全部素材")
    parser.add_argument("--asset", type=str, help="只生成指定素材（名称见 ASSETS 字典 key）")
    parser.add_argument("--dry-run", action="store_true", help="仅打印 prompt，不调用 API")
    parser.add_argument("--list", action="store_true", help="列出所有可生成素材")
    args = parser.parse_args()

    if args.list:
        print("可生成素材列表：\n")
        for name, cfg in ASSETS.items():
            in_file = os.path.basename(cfg["input"])
            print(f"  {name}")
            print(f"    参考图: {in_file}")
            print(f"    输出:   {cfg['output']} ({cfg.get('size', '1024x1024')})")
            print()
        return

    if args.asset:
        if args.asset not in ASSETS:
            print(f"❌ 未知素材: {args.asset}")
            print(f"   可用: {', '.join(ASSETS.keys())}")
            return
        await generate_one(args.asset, ASSETS[args.asset], dry_run=args.dry_run)
        return

    if args.all:
        success = 0
        total = len(ASSETS)
        for name, cfg in ASSETS.items():
            ok = await generate_one(name, cfg, dry_run=args.dry_run)
            if ok:
                success += 1
        if not args.dry_run:
            print(f"\n🎉 完成: {success}/{total} 个素材生成成功")
        return

    parser.print_help()


if __name__ == "__main__":
    asyncio.run(main())
