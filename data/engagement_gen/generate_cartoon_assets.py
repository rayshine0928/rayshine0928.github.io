"""0928.love — 噜噜噜妹卡通素材生成器 v2
使用卡通参考图作为风格锚点，生成同一卡通风格的不同动作/场景。
用法：
  python generate_cartoon_assets.py --all
  python generate_cartoon_assets.py --asset hero_cartoon
  python generate_cartoon_assets.py --all --dry-run
"""

import argparse
import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from edit_image import edit_image, download_image

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
IMG_DIR = os.path.abspath(os.path.join(CURRENT_DIR, "..", "..", "img"))

# --- 卡通风格参考图（必须保持这个风格！）---
REF_CARTOON_01 = os.path.join(IMG_DIR, "cartoon_ref_01.png")
REF_CARTOON_02 = os.path.join(IMG_DIR, "cartoon_ref_02.png")

# ================================================================
# 风格锁定 Prompt（所有素材共用）
# ================================================================
STYLE_LOCK = """
CRITICAL — CHARACTER DESIGN LOCK (highest priority):
The reference image shows TWO cute chibi cartoon characters. You MUST preserve their exact character design:
- 噜噜 (male, LEFT): short neat dark hair, round metal-frame glasses, warm brown eyes, gentle smile, chibi proportions (~1:3 head-to-body).
- 噜妹 (female, RIGHT): long straight black hair flowing over shoulders, soft warm eyes, gentle smile, chibi proportions (~1:3 head-to-body).
- Art style: flat vector illustration with soft watercolor texture, clean bold outlines, pastel color palette, warm lighting, cute and heartwarming feel.
- KEEP the faces, hairstyles, glasses, body proportions, and art style IDENTICAL to the reference.
- DO NOT turn them into realistic 3D people, DO NOT change their facial features, DO NOT make them look like a different art style.

WHAT TO CHANGE: pose, outfit, action, background scene — while keeping characters and art style locked.
"""

# ================================================================
# 素材定义
# ================================================================
ASSETS = {
    # --- Hero: 噜噜噜妹牵手站在草坪婚礼现场 ---
    "hero_cartoon": {
        "input": REF_CARTOON_01,
        "output": "cartoon_hero.png",
        "size": "1024x1024",
        "prompt": STYLE_LOCK + """

SCENE: Outdoor lawn wedding ceremony.
POSE: The two cute chibi cartoon characters stand side by side in the center, holding hands. They face slightly toward each other with warm, loving smiles. Full body visible.
OUTFIT: 噜噜 wears a simple light beige/cream linen suit (no tie, relaxed outdoor wedding style). 噜妹 wears a simple elegant white A-line wedding dress (cartoon simplified), long hair flowing over one shoulder.
BACKGROUND: A beautiful outdoor lawn wedding scene — green grass, a wooden wedding arch decorated with rainbow ribbons and flowers, blue sky with soft clouds, warm golden sunlight. The characters stand on the grass.
STYLE: Same cute chibi cartoon style as reference. Characters are the main focus, filling ~50% of canvas height. Transparent background NOT needed — this is a full scene illustration.
MOOD: Joyful, romantic, "our special day."
""".strip(),
    },

    # --- 请柬: 噜噜噜妹举着请柬 ---
    "invitation_cartoon": {
        "input": REF_CARTOON_01,
        "output": "cartoon_invitation.png",
        "size": "1024x1024",
        "prompt": STYLE_LOCK + """

SCENE: Wedding invitation moment.
POSE: The two cute chibi characters stand close together, each holding one side of a large elegant cream-colored wedding invitation card. The card faces the viewer. Both smile warmly — they're personally inviting guests to their wedding.
OUTFIT: Same style as reference — 噜噜 in dark suit, 噜妹 in white dress. Keep their exact character design from the reference.
BACKGROUND: Simple soft pastel gradient (cream to soft pink) — clean and elegant. The invitation card is the visual anchor between them.
COMPOSITION: Waist-up or 3/4 body. Characters and invitation card centered. Transparent background — this will be placed as a floating element on a webpage.
STYLE: Same cute chibi cartoon style as reference, identical art style.
""".strip(),
    },

    # --- 故事① 初见 ---
    "story_01": {
        "input": REF_CARTOON_01,
        "output": "cartoon_story_01.png",
        "size": "1024x768",
        "prompt": STYLE_LOCK + """

SCENE: "First Met" — a romantic meet-cute moment.
POSE: The two chibi characters stand a short distance apart in a cozy coffee shop. They've just locked eyes for the first time. The man holds a coffee cup, looking slightly surprised but smiling softly. The woman glances up, a gentle blush on her cheeks. A spark of connection between them.
BACKGROUND: Warm cozy coffee shop interior — wooden tables, soft amber lighting, bookshelves in soft blur behind them. Golden light streams through a window.
OUTFIT: Casual everyday clothes — 噜噜 in a light sweater, 噜妹 in a cozy cardigan. Keep their exact faces, glasses, hair.
STYLE: Same cute chibi cartoon art style as reference. Full scene illustration with background.
MOOD: Serendipity, warmth, the magic of first encounters.
""".strip(),
    },

    # --- 故事② 相爱 ---
    "story_02": {
        "input": REF_CARTOON_01,
        "output": "cartoon_story_02.png",
        "size": "1024x768",
        "prompt": STYLE_LOCK + """

SCENE: "Fell in Love" — joyful adventure together.
POSE: The two chibi characters walk side by side along a scenic path at sunset. The woman's arm is linked through the man's. Both are mid-laughter, completely at ease, in the middle of a happy conversation.
BACKGROUND: Beautiful sunset beach or cherry blossom park — warm golden-pink sky, soft distant scenery. Their cartoon silhouettes are instantly recognizable.
OUTFIT: Casual travel/outdoor clothes — light jackets, comfortable shoes, warm earth tones.
STYLE: Same cute chibi cartoon art style as reference. Full scene illustration.
MOOD: Freedom, joy, "the whole world is ours together."
""".strip(),
    },

    # --- 故事③ 求婚 ---
    "story_03": {
        "input": REF_CARTOON_01,
        "output": "cartoon_story_03.png",
        "size": "1024x768",
        "prompt": STYLE_LOCK + """

SCENE: "The Proposal" — tender romantic moment.
POSE: 噜噜 is down on one knee, looking up with hopeful loving eyes, holding a small ring box with a sparkling diamond. 噜妹 stands before him, both hands covering her mouth in joyful surprise, eyes glistening.
BACKGROUND: Romantic sunset garden or fairy-light decorated park — soft dreamy bokeh background. The couple is the crystal-clear focus.
OUTFIT: 噜噜 in a clean button-up shirt, 噜妹 in a pretty dress — not formal wedding attire, this is the proposal.
STYLE: Same cute chibi cartoon art style as reference. Full scene illustration.
MOOD: Overwhelming love, vulnerability, the most important question.
""".strip(),
    },

    # --- 故事④ 婚礼 ---
    "story_04": {
        "input": REF_CARTOON_01,
        "output": "cartoon_story_04.png",
        "size": "1024x768",
        "prompt": STYLE_LOCK + """

SCENE: "The Wedding" — happily ever after.
POSE: The two chibi characters stand under a beautiful outdoor wedding arch decorated with rainbow ribbons. They face each other, hands clasped, exchanging vows. Both have the brightest, most joyful smiles.
BACKGROUND: The same lawn wedding setting — green grass, rainbow arch, blue sky, flower decorations, warm golden sunlight.
OUTFIT: Same wedding attire as reference — 噜噜 in dark suit, 噜妹 in white wedding dress with simple veil. Keep their exact character design.
STYLE: Same cute chibi cartoon art style as reference. Full scene illustration. This is the brightest, most celebratory panel.
MOOD: Pure happiness, "happily ever after begins now."
""".strip(),
    },

    # --- 场地区指路 ---
    "guide_cartoon": {
        "input": REF_CARTOON_01,
        "output": "cartoon_guide.png",
        "size": "1024x1024",
        "prompt": STYLE_LOCK + """

SCENE: "Welcome! The venue is this way!"
POSE: The two chibi characters pose playfully — 噜噜 points forward/diagonally with one hand like a tour guide, 噜妹 waves welcomingly with one hand. Both have cheerful, inviting expressions.
OUTFIT: Semi-formal outdoor wedding guest attire — light blazer for 噜噜, pretty garden-party dress for 噜妹. Fitting the lawn wedding vibe.
COMPOSITION: Full body or 3/4 body, dynamic welcoming pose. Transparent background — floating element for the venue section of a webpage.
STYLE: Same cute chibi cartoon art style as reference. Identical character design.
MOOD: "We're so happy you're here!" — warm and welcoming.
""".strip(),
    },

    # --- 流程小图标 x7 ---
    "schedule_icons": {
        "input": REF_CARTOON_01,
        "output": "cartoon_schedule_icons.png",
        "size": "1536x1024",
        "prompt": STYLE_LOCK + """

SCENE: SEVEN small cute chibi cartoon icons in a horizontal row, each showing a wedding day activity.
The same two chibi characters appear in each tiny icon, doing different things. Icons are simple, clean, instantly readable.

From left to right:
1. 迎亲: 噜噜 holding a small bouquet, walking toward 噜妹 happily.
2. 敬茶: Both characters kneeling, offering a tea cup with both hands respectfully.
3. 拍摄: 噜噜 taking a photo of 噜妹 with a camera, 噜妹 posing cutely.
4. 仪式: Both standing under a tiny wedding arch, exchanging rings.
5. 晚宴: Both sitting at a table with a small cake, raising glasses.
6. Party: Both dancing with musical notes floating around.
7. 送客: Both waving goodbye with warm smiles.

STYLE: Same cute chibi cartoon art style as reference. Simple clean icon style — minimal background (transparent or solid pastel). Each icon should be clearly separated but arranged in one row.
SIZE: All 7 icons arranged horizontally in one image. Each icon ~200x200px.
""".strip(),
    },
}


async def generate_one(name, cfg, dry_run=False):
    input_path = cfg["input"]
    output_path = os.path.join(IMG_DIR, cfg["output"])
    size = cfg.get("size", "1024x1024")
    prompt = cfg["prompt"]

    if not os.path.isfile(input_path):
        print(f"❌ 输入文件不存在: {input_path}")
        return False

    print(f"\n{'='*60}")
    print(f"🎨 {name}")
    print(f"   参考: {os.path.basename(input_path)}")
    print(f"   输出: {cfg['output']} ({size})")
    print(f"{'='*60}")

    if dry_run:
        print(f"\n📝 PROMPT:\n{'-'*40}\n{prompt[:500]}...\n{'-'*40}\n")
        return True

    print("⏳ 调用 API...")
    kind, payload = await edit_image(input_path, prompt=prompt, size=size)

    if kind == "bytes":
        with open(output_path, "wb") as f:
            f.write(payload)
        print(f"✅ 已保存: {output_path}")
        return True
    elif kind == "url":
        ok = await download_image(payload, output_path)
        print(f"{'✅' if ok else '❌'} {'已保存' if ok else '下载失败'}: {output_path}")
        return ok
    else:
        print(f"❌ 失败: {payload[:300]}")
        return False


async def main():
    parser = argparse.ArgumentParser(description="噜噜噜妹卡通素材生成器")
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--asset", type=str)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--list", action="store_true")
    args = parser.parse_args()

    if args.list:
        for name, cfg in ASSETS.items():
            print(f"  {name} → {cfg['output']} ({cfg.get('size','1024x1024')})")
        return

    if args.asset:
        await generate_one(args.asset, ASSETS[args.asset], args.dry_run)
    elif args.all:
        ok = 0
        for name, cfg in ASSETS.items():
            if await generate_one(name, cfg, args.dry_run): ok += 1
        if not args.dry_run:
            print(f"\n🎉 {ok}/{len(ASSETS)} 成功")
    else:
        parser.print_help()


if __name__ == "__main__":
    asyncio.run(main())
