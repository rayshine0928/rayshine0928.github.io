"""0928.love — 噜噜噜妹水豚素材生成器 v4
参考图 = 水豚夫妇照片，保持水豚形象不变，仅变化动作/场景/背景。
"""

import argparse, asyncio, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from edit_image import edit_image, download_image

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
IMG_DIR = os.path.abspath(os.path.join(CURRENT_DIR, "..", "..", "img"))

# --- 正确的水豚参考图 ---
REF_WEDDING = os.path.join(IMG_DIR, "噜噜和噜妹的结婚婚纱照.jpg")
REF_SELFIE  = os.path.join(IMG_DIR, "噜噜（右）和噜妹（左）的自拍照.jpg")
REF_BACK    = os.path.join(IMG_DIR, "噜噜和噜妹背对着屏幕靠在一起的照片.jpg")
REF_BEACH   = os.path.join(IMG_DIR, "噜噜和噜妹的海边婚礼照片.jpg")
REF_REG     = os.path.join(IMG_DIR, "噜噜和噜妹的结婚登记照.jpg")
REF_LAWN    = os.path.join(IMG_DIR, "草坪婚礼_彩虹装饰实景.jpg")

# ================================================================
RULES = """
CRITICAL — PRESERVE THE TWO CAPYBARA CHARACTERS EXACTLY:
- The reference image shows two cute capybara characters (one slightly larger/darker, one slightly smaller/lighter).
- Keep these two capybaras IDENTICAL to how they appear in the reference: same faces, same fur color and texture, same body shape, same cute cartoon-capybara style, same relative sizes.
- DO NOT change them into humans, other animals, or a different art style.
- DO NOT add or remove any capybara features (ears, nose shape, whiskers, fur pattern).
- ONLY change what is described in the SPECIFIC CHANGE below.
"""

ASSETS = {
    # --- Hero: 透明背景，牵手 ---
    "hero": {
        "ref": REF_WEDDING, "output": "cartoon_hero.png", "size": "1024x1024",
        "change": """
SPECIFIC CHANGE:
- Change the background: REMOVE it completely. Output MUST have a transparent background (PNG alpha channel). No white fill, no scene.
- Change the pose slightly: the two capybaras stand side by side, one capybara's paw gently touching the other's. Both facing forward with warm expressions.
- Keep their wedding attire from the reference if they are wearing any.
""",
    },

    # --- 请柬: 透明背景，举卡片 ---
    "invitation": {
        "ref": REF_WEDDING, "output": "cartoon_invitation.png", "size": "1024x1024",
        "change": """
SPECIFIC CHANGE:
- Change the background: REMOVE it completely. Output MUST have a transparent background (PNG alpha channel).
- Add a prop: between the two capybaras, place a large elegant cream-colored wedding invitation card. Each capybara has one paw on the card. The card faces forward.
""",
    },

    # --- 故事① 初见 ---
    "story_01": {
        "ref": REF_SELFIE, "output": "cartoon_story_01.png", "size": "1024x768",
        "change": """
SPECIFIC CHANGE:
- Change the background: a cozy warm coffee shop or park setting with soft lighting. Full illustrated scene.
- Change the pose: the two capybaras are looking at each other for the first time, a sweet moment of connection. Soft blush on cheeks.
- Keep the capybaras IDENTICAL — just change the scene and their head/eye direction.
""",
    },

    # --- 故事② 相爱 ---
    "story_02": {
        "ref": REF_BEACH, "output": "cartoon_story_02.png", "size": "1024x768",
        "change": """
SPECIFIC CHANGE:
- Change the background: a beautiful sunset beach with golden-pink sky. Full illustrated scene.
- Change the pose: the two capybaras walk side by side along the beach, happy and relaxed. One capybara has a small flower tucked behind its ear.
- Keep the capybaras IDENTICAL — just change the scene and walking pose.
""",
    },

    # --- 故事③ 求婚 ---
    "story_03": {
        "ref": REF_REG, "output": "cartoon_story_03.png", "size": "1024x768",
        "change": """
SPECIFIC CHANGE:
- Add a prop: a small sparkling diamond ring in a tiny box placed between the two capybaras.
- Change the pose: one capybara looks at the other with hopeful loving eyes, the other capybara looks surprised and joyful.
- Change the background: romantic garden with soft bokeh lights at golden hour. Full illustrated scene.
- Keep the capybaras IDENTICAL.
""",
    },

    # --- 故事④ 婚礼 ---
    "story_04": {
        "ref": REF_WEDDING, "output": "cartoon_story_04.png", "size": "1024x768",
        "change": """
SPECIFIC CHANGE:
- Change the background: a beautiful outdoor lawn wedding scene with a wooden arch decorated with rainbow ribbons and flowers, green grass, blue sky. This should match the style of a lawn wedding photo.
- Change the pose: the two capybaras stand together under the arch, facing each other lovingly, a wedding moment.
- Keep the capybaras IDENTICAL — just change the scene to a lawn wedding setting.
""",
    },

    # --- 场地区指路: 透明背景 ---
    "guide": {
        "ref": REF_BACK, "output": "cartoon_guide.png", "size": "1024x1024",
        "change": """
SPECIFIC CHANGE:
- Change the background: REMOVE it completely. Output MUST have a transparent background (PNG alpha channel).
- Change the pose: the two capybaras face forward. One capybara has one paw raised as if pointing/waving in a welcoming "this way!" gesture. Both have friendly expressions.
- Keep the capybaras IDENTICAL — just change the pose and remove background.
""",
    },

    # --- 流程图标 x7: 透明背景 ---
    "schedule": {
        "ref": REF_WEDDING, "output": "cartoon_schedule_icons.png", "size": "1536x1024",
        "change": """
SPECIFIC CHANGE:
- Create SEVEN small simple icon versions of the two capybaras arranged horizontally. Each icon shows a wedding activity:
  1. One capybara holding a tiny flower approaching the other (迎亲)
  2. Both capybaras sitting, offering a tiny tea cup (敬茶)
  3. One capybara with a tiny camera, the other posing (拍摄)
  4. Both capybaras under a tiny flower arch (仪式)
  5. Both capybaras at a tiny table with a tiny cake (晚宴)
  6. Both capybaras dancing with tiny musical notes (Party)
  7. Both capybaras waving goodbye (送客)
- REMOVE the background completely — transparent PNG.
- Keep the capybaras IDENTICAL in every icon — same cute style, just simple icon-size poses.
- Arrange all 7 evenly in one horizontal row.
""",
    },

    # --- Hero 草坪背景 4K ---
    "hero_bg": {
        "ref": REF_LAWN, "output": "hero_lawn_4k.jpg", "size": "2560x1440",
        "change": """
SPECIFIC CHANGE:
- Enhance this outdoor lawn wedding photo to breathtaking 4K quality.
- Boost resolution, sharpen details (grass, flowers, rainbow ribbons, wooden arch).
- Enhance sunlight to warm golden hour glow. Make rainbow decorations vibrant and saturated.
- Blue sky with soft clouds. Lush green lawn. Natural, photorealistic, editorial grade.
- DO NOT add any people or animals. Keep the scene empty — this is a venue photo without subjects.
- DO NOT change the composition or layout of the decorations/arch.
""",
    },
}


async def generate_one(name, cfg, dry_run):
    ref_path = cfg["ref"]
    output_path = os.path.join(IMG_DIR, cfg["output"])
    prompt = RULES + "\n\n" + cfg["change"]

    if not os.path.isfile(ref_path):
        print(f"❌ 参考图缺失: {ref_path}")
        return False

    print(f"\n{'='*60}")
    print(f"🎨 {name} | 参考: {os.path.basename(ref_path)}")
    print(f"   → {cfg['output']} ({cfg['size']})")
    print(f"{'='*60}")

    if dry_run:
        print(f"\n📝 {prompt[:400]}...\n")
        return True

    print("⏳ API...")
    kind, payload = await edit_image(ref_path, prompt=prompt, size=cfg["size"])

    if kind == "bytes":
        with open(output_path, "wb") as f: f.write(payload)
        print(f"✅ {cfg['output']}")
        return True
    elif kind == "url":
        ok = await download_image(payload, output_path)
        print(f"{'✅' if ok else '❌'} {cfg['output']}")
        return ok
    else:
        print(f"❌ {str(payload)[:200]}")
        return False


async def main():
    p = argparse.ArgumentParser()
    p.add_argument("--all", action="store_true")
    p.add_argument("--asset", type=str)
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--list", action="store_true")
    args = p.parse_args()

    if args.list:
        for n, c in ASSETS.items():
            print(f"  {n} ← {os.path.basename(c['ref'])} → {c['output']}")
        return
    if args.asset:
        await generate_one(args.asset, ASSETS[args.asset], args.dry_run)
    elif args.all:
        ok = 0
        for n, c in ASSETS.items():
            if await generate_one(n, c, args.dry_run): ok += 1
        if not args.dry_run: print(f"\n🎉 {ok}/{len(ASSETS)}")
    else:
        p.print_help()


if __name__ == "__main__":
    asyncio.run(main())
