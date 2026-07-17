"""0928.love — 噜噜噜妹水豚素材生成器 v5
多参考图拼接版：将 5 张水豚夫妇照片拼接为一张后上传，让 AI 全面理解角色形象。
"""

import argparse, asyncio, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from edit_image import edit_image, edit_image_multi_ref, download_image

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
IMG_DIR = os.path.abspath(os.path.join(CURRENT_DIR, "..", "..", "img"))

# --- 水豚参考图全集 ---
REF_WEDDING = os.path.join(IMG_DIR, "噜噜和噜妹的结婚婚纱照.jpg")
REF_SELFIE  = os.path.join(IMG_DIR, "噜噜（右）和噜妹（左）的自拍照.jpg")
REF_BACK    = os.path.join(IMG_DIR, "噜噜和噜妹背对着屏幕靠在一起的照片.jpg")
REF_BEACH   = os.path.join(IMG_DIR, "噜噜和噜妹的海边婚礼照片.jpg")
REF_REG     = os.path.join(IMG_DIR, "噜噜和噜妹的结婚登记照.jpg")
REF_LAWN    = os.path.join(IMG_DIR, "草坪婚礼_彩虹装饰实景.jpg")

# 所有水豚角色参考图（用于拼接后上传，让 AI 全面理解角色）
ALL_CAPYBARA_REFS = [REF_WEDDING, REF_SELFIE, REF_BEACH, REF_REG, REF_BACK]

# ================================================================
# 多参考图拼接说明（注入 prompt，帮助 AI 理解拼接布局）
# ================================================================
MULTI_REF_NOTE = """
REFERENCE IMAGE NOTE:
The uploaded reference is a grid montage of 5 photos of the SAME two capybara characters (噜噜 and 噜妹):
- Photo 1 (top-left): Wedding photo — both capybaras facing forward, formal wedding attire
- Photo 2 (top-center): Selfie — both capybaras close-up, casual, front view
- Photo 3 (top-right): Beach wedding — both capybaras in a scenic outdoor setting
- Photo 4 (bottom-left): Registration photo — both capybaras formal close-up, front view
- Photo 5 (bottom-center): Back view — both capybaras seen from behind, showing their back fur/texture

Use ALL views together to understand the capybaras' exact appearance from every angle.
"""

RULES = """
CRITICAL — PRESERVE THE TWO CAPYBARA CHARACTERS EXACTLY:
- The reference montage shows two cute capybara characters (噜噜 = slightly larger/darker, 噜妹 = slightly smaller/lighter).
- Keep these two capybaras IDENTICAL to how they appear in the references: same faces, same fur color and texture, same body shape, same cute cartoon-capybara style, same relative sizes, same ear shape, same nose, same whiskers, same fur pattern.
- DO NOT change them into humans, other animals, or a different art style.
- DO NOT add or remove any capybara features (ears, nose shape, whiskers, fur pattern, tail).
- ONLY change what is described in the SPECIFIC CHANGE below.
- HIGH QUALITY: crisp, detailed, adorable, suitable for a premium wedding website.
"""

ASSETS = {
    # --- Hero: 透明背景，牵手 ---
    "hero": {
        "refs": ALL_CAPYBARA_REFS,
        "output": "cartoon_hero.png", "size": "1024x1024",
        "change": """
SPECIFIC CHANGE:
- Change the background: REMOVE it completely. Output MUST have a transparent background (PNG alpha channel). No white fill, no scene.
- Pose: the two capybaras stand side by side, one capybara's paw gently touching the other's. Both facing forward with warm, loving expressions.
- If they are wearing wedding attire in the references, keep that — but simplify for a clean cartoon look.
- Make them look extra cute and huggable — soft rounded shapes, gentle highlights in the eyes, a subtle warm glow around them.
- Characters should fill ~70% of the canvas, centered.
""",
    },

    # --- 请柬: 透明背景，举卡片 ---
    "invitation": {
        "refs": ALL_CAPYBARA_REFS,
        "output": "cartoon_invitation.png", "size": "1024x1024",
        "change": """
SPECIFIC CHANGE:
- Change the background: REMOVE it completely. Output MUST have a transparent background (PNG alpha channel).
- Add a prop: between the two capybaras, place a large elegant cream-colored wedding invitation card. Each capybara has one paw on the card. The card faces forward.
- The capybaras should look warm and inviting, as if personally welcoming each guest.
- Extra cute details: tiny hearts floating above them, soft sparkles around the card.
""",
    },

    # --- 故事① 初见 ---
    "story_01": {
        "refs": ALL_CAPYBARA_REFS,
        "output": "cartoon_story_01.png", "size": "1024x768",
        "change": """
SPECIFIC CHANGE:
- Change the background: a cozy warm coffee shop or park setting with soft golden lighting. Full illustrated scene.
- Change the pose: the two capybaras are looking at each other for the first time, a sweet moment of connection. Soft blush on cheeks.
- Keep the capybaras IDENTICAL — just change the scene and their head/eye direction.
- Warm, storybook illustration style. Soft watercolor feeling.
""",
    },

    # --- 故事② 相爱 ---
    "story_02": {
        "refs": ALL_CAPYBARA_REFS,
        "output": "cartoon_story_02.png", "size": "1024x768",
        "change": """
SPECIFIC CHANGE:
- Change the background: a beautiful sunset beach with golden-pink sky. Full illustrated scene.
- Change the pose: the two capybaras walk side by side along the beach, happy and relaxed. One capybara has a small flower tucked behind its ear.
- Keep the capybaras IDENTICAL — just change the scene and walking pose.
- Studio Ghibli-esque warm lighting, soft waves, dreamy atmosphere.
""",
    },

    # --- 故事③ 求婚 ---
    "story_03": {
        "refs": ALL_CAPYBARA_REFS,
        "output": "cartoon_story_03.png", "size": "1024x768",
        "change": """
SPECIFIC CHANGE:
- Add a prop: a small sparkling diamond ring in a tiny box placed between the two capybaras.
- Change the pose: one capybara looks at the other with hopeful loving eyes, the other capybara looks surprised and joyful (paws covering mouth).
- Change the background: romantic garden with soft bokeh lights at golden hour. Full illustrated scene.
- Keep the capybaras IDENTICAL.
- Sparkling details on the ring, soft bokeh circles in background, warm romantic mood.
""",
    },

    # --- 故事④ 婚礼 ---
    "story_04": {
        "refs": ALL_CAPYBARA_REFS,
        "output": "cartoon_story_04.png", "size": "1024x768",
        "change": """
SPECIFIC CHANGE:
- Change the background: a beautiful outdoor lawn wedding scene with a wooden arch decorated with rainbow ribbons and flowers, green grass, blue sky.
- Change the pose: the two capybaras stand together under the arch, facing each other lovingly, a wedding moment.
- Keep the capybaras IDENTICAL — just change the scene to a lawn wedding setting.
- Bright, joyful, celebratory colors. This is the happiest panel.
""",
    },

    # --- 场地区指路: 透明背景 ---
    "guide": {
        "refs": ALL_CAPYBARA_REFS,
        "output": "cartoon_guide.png", "size": "1024x1024",
        "change": """
SPECIFIC CHANGE:
- Change the background: REMOVE it completely. Output MUST have a transparent background (PNG alpha channel).
- Change the pose: the two capybaras face forward. One capybara has one paw raised as if pointing/waving in a welcoming "this way!" gesture. Both have friendly, cheerful expressions.
- Keep the capybaras IDENTICAL — just change the pose and remove background.
- Cute tour-guide vibe. Warm, inviting body language.
""",
    },

    # --- 流程图标 x7: 透明背景 ---
    "schedule": {
        "refs": ALL_CAPYBARA_REFS,
        "output": "cartoon_schedule_icons.png", "size": "1536x1024",
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
- Arrange all 7 evenly in one horizontal row with small gaps between each icon.
- Each icon should be cute and clearly readable at small size.
""",
    },

    # --- Hero 草坪背景 4K（只用草坪参考图即可） ---
    "hero_bg": {
        "ref": REF_LAWN,
        "output": "hero_lawn_4k.jpg", "size": "2560x1440",
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
    output_path = os.path.join(IMG_DIR, cfg["output"])

    # 支持单张参考图 (ref) 和多张参考图 (refs)
    refs = cfg.get("refs")
    single_ref = cfg.get("ref")

    if refs:
        # 检查所有参考图
        for rp in refs:
            if not os.path.isfile(rp):
                print(f"❌ 参考图缺失: {rp}")
                return False
        prompt = MULTI_REF_NOTE + "\n\n" + RULES + "\n\n" + cfg["change"]
        ref_label = f"{len(refs)}张拼接"
    elif single_ref:
        if not os.path.isfile(single_ref):
            print(f"❌ 参考图缺失: {single_ref}")
            return False
        prompt = RULES + "\n\n" + cfg["change"]
        ref_label = os.path.basename(single_ref)
        refs = [single_ref]  # 用于打印
    else:
        print(f"❌ {name}: 未配置参考图")
        return False

    print(f"\n{'='*60}")
    print(f"🎨 {name} | 参考: {ref_label}")
    print(f"   → {cfg['output']} ({cfg['size']})")
    print(f"{'='*60}")

    if dry_run:
        print(f"\n📝 {prompt[:500]}...\n")
        return True

    print("⏳ API...")
    if cfg.get("refs"):
        # 多参考图模式：拼接后上传
        kind, payload = await edit_image_multi_ref(
            refs, prompt=prompt, size=cfg["size"], merge_max_size=768,
        )
    else:
        # 单参考图模式
        kind, payload = await edit_image(
            single_ref, prompt=prompt, size=cfg["size"],
        )

    if kind == "bytes":
        with open(output_path, "wb") as f:
            f.write(payload)
        print(f"✅ {cfg['output']} ({len(payload)} bytes)")
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
            if c.get("refs"):
                print(f"  {n} ← {len(c['refs'])}张拼接 → {c['output']}")
            else:
                print(f"  {n} ← {os.path.basename(c['ref'])} → {c['output']}")
        return
    if args.asset:
        await generate_one(args.asset, ASSETS[args.asset], args.dry_run)
    elif args.all:
        ok = 0
        for n, c in ASSETS.items():
            if await generate_one(n, c, args.dry_run):
                ok += 1
        if not args.dry_run:
            print(f"\n🎉 {ok}/{len(ASSETS)}")
    else:
        p.print_help()


if __name__ == "__main__":
    asyncio.run(main())
