"""0928.love — 卡通素材生成器 v3（修正版）
关键修正：提示词不提及角色名字，只要求保留原图卡通形象，仅变化动作/场景/背景。
"""

import argparse, asyncio, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from edit_image import edit_image, download_image

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
IMG_DIR = os.path.abspath(os.path.join(CURRENT_DIR, "..", "..", "img"))
REF = os.path.join(IMG_DIR, "cartoon_ref_01.png")

# ================================================================
# 核心规则（所有 prompt 共用）
# ================================================================
RULES = """
CRITICAL RULES:
- The reference image contains TWO cartoon characters (a male on the left with short dark hair and round glasses, a female on the right with long black hair).
- PRESERVE these two characters EXACTLY as they appear in the reference: identical faces, hairstyles, glasses, chibi body proportions, flat-vector-with-watercolor art style, and color palette.
- DO NOT redesign, redraw, restyle, or change the characters' appearance in any way.
- DO NOT change their faces, hair color, skin tone, or clothing style unless specifically instructed below.
- ONLY change what is described in the SPECIFIC CHANGE section below.
"""

ASSETS = {
    # --- Hero: 牵手 + 透明背景 ---
    "hero": {
        "output": "cartoon_hero.png", "size": "1024x1024",
        "change": """
SPECIFIC CHANGE:
- Change the pose: both characters stand side by side, holding hands, facing slightly toward each other with warm happy smiles. Full body visible.
- REMOVE the background completely — output MUST have a transparent background (PNG with alpha channel). No white, no colored fill, no scene. Just the two characters with a clean transparent background.
""",
    },

    # --- 请柬: 举着请柬卡片 + 透明背景 ---
    "invitation": {
        "output": "cartoon_invitation.png", "size": "1024x1024",
        "change": """
SPECIFIC CHANGE:
- Change the pose: both characters hold a large elegant cream-colored wedding invitation card between them. Each character holds one side of the card. The card faces the viewer directly. Both smile warmly as if personally inviting guests.
- Only change the pose and add the invitation card prop. Characters remain otherwise identical to the reference.
- REMOVE the background completely — output MUST have a transparent background (PNG with alpha channel).
""",
    },

    # --- 故事① 初见: 咖啡店场景 ---
    "story_01": {
        "output": "cartoon_story_01.png", "size": "1024x768",
        "change": """
SPECIFIC CHANGE:
- Change the pose: the two characters stand a short distance apart, just having noticed each other for the first time. The man holds a coffee cup and looks slightly surprised but smiling softly. The woman glances up with a gentle blush. A moment of serendipitous connection.
- Change the background: a warm cozy coffee shop interior with soft amber lighting, wooden tables, and bookshelves softly blurred in the distance. Full scene illustration.
""",
    },

    # --- 故事② 相爱: 海边/户外场景 ---
    "story_02": {
        "output": "cartoon_story_02.png", "size": "1024x768",
        "change": """
SPECIFIC CHANGE:
- Change the pose: the two characters walk side by side along a beautiful beach at sunset. The woman links her arm through the man's. Both are mid-laughter, completely joyful and at ease.
- Change the background: golden sunset beach scene with soft waves, warm pink-orange sky, gentle clouds. Full scene illustration.
""",
    },

    # --- 故事③ 求婚: 单膝跪地 ---
    "story_03": {
        "output": "cartoon_story_03.png", "size": "1024x768",
        "change": """
SPECIFIC CHANGE:
- Change the pose: the male character is down on one knee, looking up with hopeful loving eyes, holding a small ring box with a sparkling diamond. The female character stands before him, both hands covering her mouth in joyful surprise, eyes glistening with happy tears.
- Change the background: romantic garden at golden hour with soft dreamy bokeh, fairy lights, warm atmosphere. Full scene illustration.
""",
    },

    # --- 故事④ 婚礼: 草坪拱门 ---
    "story_04": {
        "output": "cartoon_story_04.png", "size": "1024x768",
        "change": """
SPECIFIC CHANGE:
- Change the pose: the two characters stand facing each other under a beautiful outdoor wedding arch decorated with rainbow ribbons and flowers. They hold hands, exchanging vows with the brightest most joyful smiles.
- Change the background: outdoor lawn wedding scene — green grass, rainbow-decorated wooden arch, blue sky with white clouds, warm golden sunlight. Full scene illustration.
""",
    },

    # --- 场地区指路: 透明背景 ---
    "guide": {
        "output": "cartoon_guide.png", "size": "1024x1024",
        "change": """
SPECIFIC CHANGE:
- Change the pose: the male character points forward/diagonally with one hand (like a friendly tour guide showing the way). The female character waves welcomingly with one hand and has a cheerful expression. Both look happy and inviting.
- REMOVE the background completely — output MUST have a transparent background (PNG with alpha channel).
""",
    },

    # --- 流程图标 x7: 透明背景横排 ---
    "schedule": {
        "output": "cartoon_schedule_icons.png", "size": "1536x1024",
        "change": """
SPECIFIC CHANGE:
- Create SEVEN small icon versions of the two characters arranged in a horizontal row. Each icon shows them doing a different wedding-day activity:
  1. The man walking toward the woman holding flowers (迎亲)
  2. Both kneeling and offering tea cups respectfully (敬茶)
  3. The man taking a photo of the woman with a camera (拍摄)
  4. Both standing under a tiny wedding arch exchanging rings (仪式)
  5. Both sitting at a table raising glasses with a small cake (晚宴)
  6. Both dancing with musical notes (Party)
  7. Both waving goodbye warmly (送客)
- Keep the characters' appearance IDENTICAL to the reference in every icon — only pose changes.
- REMOVE the background completely — each icon group should have a transparent background (PNG with alpha channel). Arrange all 7 icons in one row with even spacing.
""",
    },
}


async def generate_one(name, cfg, dry_run):
    input_path = REF
    output_path = os.path.join(IMG_DIR, cfg["output"])
    prompt = RULES + "\n\n" + cfg["change"]

    if not os.path.isfile(input_path):
        print(f"❌ 参考图缺失: {input_path}")
        return False

    print(f"\n{'='*60}")
    print(f"🎨 {name} → {cfg['output']} ({cfg['size']})")
    print(f"{'='*60}")

    if dry_run:
        print(f"\n📝 PROMPT:\n{'-'*40}\n{prompt[:600]}\n{'-'*40}\n")
        return True

    print("⏳ 调用 API...")
    kind, payload = await edit_image(input_path, prompt=prompt, size=cfg["size"])

    if kind == "bytes":
        with open(output_path, "wb") as f:
            f.write(payload)
        print(f"✅ 已保存: {output_path}")
        return True
    elif kind == "url":
        ok = await download_image(payload, output_path)
        print(f"{'✅' if ok else '❌'} {'已保存' if ok else '下载失败'}")
        return ok
    else:
        print(f"❌ 失败: {str(payload)[:300]}")
        return False


async def main():
    p = argparse.ArgumentParser(description="卡通素材生成器 v3")
    p.add_argument("--all", action="store_true")
    p.add_argument("--asset", type=str)
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--list", action="store_true")
    args = p.parse_args()

    if args.list:
        for n, c in ASSETS.items(): print(f"  {n} → {c['output']} ({c['size']})")
        return
    if args.asset:
        await generate_one(args.asset, ASSETS[args.asset], args.dry_run)
    elif args.all:
        ok = 0
        for n, c in ASSETS.items():
            if await generate_one(n, c, args.dry_run): ok += 1
        if not args.dry_run: print(f"\n🎉 {ok}/{len(ASSETS)} 成功")
    else:
        p.print_help()


if __name__ == "__main__":
    asyncio.run(main())
