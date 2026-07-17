"""简单图片编辑：调用与 generate_engagement_photos.py 相同的 /images/edits API。

用法示例：
  python edit_image.py -i ./photo.png
  python edit_image.py -i ./a.jpg -o ./out.png
默认 prompt 为空字符串；可用 --prompt 传入指令。
  python edit_image.py -i ./templates/wedding.jpg --preset premium-wood-door -o ./out.png
  python edit_image.py -i ./templates/..._wood_door.png --preset premium-wood-door-v2 -o ./out_v2.png
  python edit_image.py -i ./templates/微信图片_20260502171150_1588_3624.jpg --preset premium-wood-door-luxury -o ./templates/微信图片_20260502171150_1588_3624_luxury_2k_regen.png --size 2048x3072
  # v2 实木门成片再强化质感 / 高级感，2K 竖图（默认尺寸即 2048x3072）：
  python edit_image.py -i ./templates/微信图片_20260502171150_1588_3624_wood_door_v2.png --preset premium-wood-door-v2-2k-finish -o ./templates/微信图片_20260502171150_1588_3624_wood_door_v2_2k_finish.png
  python edit_image.py -i ./templates/微信图片_20260502170650_1586_3624.jpg --preset fujifilm-dining-scene
  # 从 prompt.txt 读取长提示（双人锁脸 + golden hour 街景等）：
  python edit_image.py -i ./templates/人像.jpg --prompt-file ./prompt.txt -o ./outputs/人像_golden_hour_street.png
"""

import argparse
import asyncio
import base64
import json
import os
import tempfile

import aiohttp
import cv2
import numpy as np
from dotenv import load_dotenv

current_dir = os.path.dirname(os.path.abspath(__file__))
env_path = os.path.join(current_dir, "api.env")
load_dotenv(dotenv_path=env_path)

API_KEY = os.getenv("IMAGE_OPENAI_API_KEY")
BASE_URL = os.getenv("IMAGE_OPENAI_BASE_URL")
MODEL = os.getenv("IMAGE_OPENAI_MODEL", "gpt-image-2")
EDITS_ENDPOINT = f"{BASE_URL.rstrip('/')}/images/edits"

# 将背景替换为高级深色实木敞开门：克制、有质感、不夸张；前景保持不变。
PREMIUM_WOOD_DOOR_BACKGROUND_PROMPT = (
    "Replace ONLY the background. Keep the foreground completely unchanged and identical: both hands, "
    "grey suit sleeve and cuff, the small red Chinese double-happiness paper cutout, the pink bridal bouquet, "
    "white ribbon wrap, stems, and every edge and occlusion exactly as in the original—same pose, scale, "
    "sharp focus, and natural skin tones.\n\n"
    "New background: a very high-end interior with a single dark solid hardwood door, slightly open (ajar), "
    "showing fine vertical wood grain, matte or satin lacquer, subtle warm ambient light, shallow depth of "
    "field behind the subject. The wood should feel luxurious and textured—walnut or ebony tone—not glossy "
    "plastic, no carved ornament, no gold trim, no neon, no surreal glow, no exaggerated staging. Photorealistic, "
    "elegant, restrained wedding editorial style."
)

# v2：深色实木敞开门背景 + 左侧囍字水平镜像校正 + 右侧女士手与手臂略纤细、肤色更白皙（自然不假白）。
PREMIUM_WOOD_DOOR_BACKGROUND_PROMPT_V2 = (
    "Photorealistic engagement photo. Background: a very high-end interior with a single dark solid hardwood "
    "door, slightly open (ajar), fine vertical grain, matte or satin lacquer, subtle warm ambient light, shallow "
    "depth of field—walnut or ebony tone, luxurious and textured, no gold trim, no exaggerated staging.\n\n"
    "Foreground edits:\n"
    "- LEFT (man's hand): the red Chinese double-happiness (囍) paper cutout is mirrored/back-to-front; flip it "
    "horizontally so it reads with correct orientation. Keep size, grip between thumb and fingers, paper curl, "
    "and shadows natural.\n"
    "- RIGHT (bride): subtly refine her visible hand and forearm to appear slightly more slender with fairer, "
    "brighter natural skin—realistic indoor light, no porcelain whitening or extreme slimming.\n\n"
    "Keep unchanged unless noted: grey suit sleeve and cuff, pink bouquet, white ribbon, poses, composition, "
    "and focus."
)

# 用餐/庆生场景：富士单反胶片感（Classic Chrome / Astia 方向）、整理桌面杂物、女士手指纤细白皙、男士肩臂线条更明显。
FUJIFILM_DINING_SCENE_PROMPT = (
    "Photorealistic indoor dining portrait. Re-grade the entire image to mimic high-quality Fujifilm X-series DSLR "
    "output with a film simulation look (Classic Chrome or Astia style): organic color science, warm but natural "
    "skin tones, gentle rolloff in highlights, rich mid-tone contrast, slightly lifted shadows, subtle analog "
    "grain, fine micro-contrast and tactile texture—never plasticky HDR or oversharpened. Add restrained shallow "
    "depth of field so the couple and birthday cake stay crisp while background painting and wallpaper soften "
    "naturally; cohesive warm ambient light.\n\n"
    "Composition cleanup: simplify the tabletop—remove or neatly minimize distracting clutter such as empty or "
    "heavily soiled dishes, messy leftover bowls, and awkward foreground bowl/ladle arrangements that compete "
    "with the cake. Keep the celebration believable: the small birthday cake, glasses, and a few tasteful "
    "elements may remain; the frame should feel cleaner and more editorial.\n\n"
    "Subject refinements (subtle and anatomically plausible):\n"
    "- Woman (right): refine her visible fingers and hands to appear more slender and elongated, with fairer, "
    "more luminous translucent skin under the same warm light—no porcelain mask or extreme slimming.\n"
    "- Man (left): enhance his cutting arm—the deltoid, upper arm, and forearm—with slightly more defined, "
    "athletic muscle tone and separation, especially shoulder contour; keep natural proportions, not exaggerated "
    "bodybuilder bulk.\n\n"
    "Preserve identity, poses, wardrobe, cake lettering, and overall scene layout unless cleanup requires minor "
    "table rearrangement."
)

# 深色实木大门 + 艺术感远景虚化 + 高级光影 + 囍字左右翻转 + 女士手/臂白皙纤细；输出尺寸用 --size（默认 2048x3072，约 2K 竖图）。
PREMIUM_WOOD_DOOR_LUXURY_EDITORIAL_PROMPT = (
    "Photorealistic editorial engagement photograph with strong artistic intent. Deliver ultra-high-definition "
    "output comparable to a 2K vertical master from a full-frame DSLR and fast prime lens—tack-sharp micro-detail "
    "on subjects, refined dynamic range, natural color science, no plastic HDR, no oversharpening, no AI glam "
    "smoothing.\n\n"
    "BACKGROUND — replace the entire current environment (light paneled wall / bright millwork, and the dark soft "
    "area at the far right) with one cohesive luxury scene: an imposing dark solid hardwood door standing openly "
    "ajar (wide enough to feel inviting yet believable), vertical grain, hand-rubbed matte to satin lacquer, "
    "exquisite joinery—walnut, wenge, or fine ebony-stained oak. Real timber under light, not laminate or glossy "
    "plastic. Restrained: no baroque carving, no gold trim, no surreal glow. Through the opening, the deeper "
    "interior or corridor reads as painterly distance: strong circular bokeh, soft gradient, gentle color falloff—"
    "depth and atmosphere like fine art wedding editorial, not a flat backdrop.\n\n"
    "LIGHTING & SHADOWS — mandatory premium look. Evolve (do not flatten) the light: soft but directional key "
    "from front-left with a touch of sculpting on the dark wood, delicate rim/separation on rose petals, suit "
    "cuff texture, and both hands; rich yet controlled shadow density in wood grain recesses; micro-contrast that "
    "feels cinematic and expensive. Preserve believable highlight placement on hands, roses, stems, white ribbon, "
    "and the red cutout; re-map contact shadows and occlusion onto the new door so subjects read as truly "
    "photographed in this space, not composited.\n\n"
    "LEFT — horizontally flip (mirror) ONLY the red Chinese double-happiness (囍) laser-cut paper cutout: it is "
    "currently mirrored/back-to-front; correct its orientation for legible 囍. Keep grip between thumb and "
    "fingers, scale, paper curl, edge sharpness, and interaction with light natural aside from the mirror.\n\n"
    "RIGHT — refine the bride's visible hand and forearm to appear clearly more slender and graceful "
    "(anatomically plausible, not extreme), with fairer, brighter skin—natural porcelain fairness under the same "
    "warm key—no heavy whitening mask, no waxy plastic skin. Pay extra attention to the fingers: they must read "
    "noticeably lighter and more luminous than in the source, with delicate taper—still anatomically correct.\n\n"
    "LOCK unless noted: man's grey suit sleeve and cuff, bouquet species and arrangement, overall crop and "
    "composition, subject focus plane."
)

# v2 实木门场景成片专用：不再替换布景或大改主体，仅整体高级调色 + 微观质感 + 2K 成片描述（配合 --size 2048x3072）。
PREMIUM_WOOD_DOOR_V2_2K_FINISH_PROMPT = (
    "Photorealistic finishing pass on this existing engagement photograph. The composition is already final: dark "
    "hardwood door slightly ajar with vertical grain, warm interior bokeh, man's grey suit sleeve, the red Chinese "
    "double-happiness (囍) paper cutout, and the pink bridal bouquet—do NOT replace the environment, do NOT "
    "re-compose, do NOT mirror or redraw the 囍, do NOT change poses or hand anatomy except microscopic blemish "
    "cleanup if needed.\n\n"
    "GOAL — stronger 质感 and 高级感，as a native 2K vertical master from full-frame + fast prime: tack-sharp "
    "micro-detail on petals, paper edge, wood pores, and suit weave; refined dynamic range with dense but readable "
    "shadows in the timber, gentle highlight rolloff on flowers and skin—never plastic HDR, never oversharpened "
    "halos, never AI glam smoothing or waxy skin.\n\n"
    "COLOR & LIGHT — premium editorial grade: cohesive warm key (soft directional light, believable rim on bouquet "
    "and hands), subtle separation between subject planes, atmospheric depth in the doorway opening; optional "
    "hint of fine photographic grain like ISO 400–800 DSLR, not heavy noise.\n\n"
    "TEXTURE — make materials feel expensive: hand-rubbed matte/satin lacquer on the door, silken ribbon, delicate "
    "petal translucency, crisp laser-cut 囍 red, natural skin texture on visible hands.\n\n"
    "Deliver output that reads as a finished high-end wedding editorial frame at approximately 2K short-side "
    "equivalent clarity."
)


def _read_prompt_file(path: str) -> tuple[str | None, str | None]:
    """读取 UTF-8 文本提示词；出错时返回 (None, error_message)。"""
    if not path:
        return None, "prompt 文件路径为空"
    if not os.path.isfile(path):
        return None, f"找不到 prompt 文件: {path}"
    try:
        with open(path, "r", encoding="utf-8") as f:
            text = f.read().strip()
        if not text:
            return None, f"prompt 文件为空: {path}"
        return text, None
    except OSError as e:
        return None, f"读取 prompt 文件失败: {e}"


PRESET_PROMPTS = {
    "premium-wood-door": PREMIUM_WOOD_DOOR_BACKGROUND_PROMPT,
    "premium-wood-door-v2": PREMIUM_WOOD_DOOR_BACKGROUND_PROMPT_V2,
    "premium-wood-door-v2-2k-finish": PREMIUM_WOOD_DOOR_V2_2K_FINISH_PROMPT,
    "premium-wood-door-luxury": PREMIUM_WOOD_DOOR_LUXURY_EDITORIAL_PROMPT,
    "fujifilm-dining-scene": FUJIFILM_DINING_SCENE_PROMPT,
}


def _content_type_for(path: str) -> str:
    ext = os.path.splitext(path)[1].lower()
    if ext in (".jpg", ".jpeg"):
        return "image/jpeg"
    if ext == ".png":
        return "image/png"
    if ext == ".webp":
        return "image/webp"
    return "application/octet-stream"


# ---- Image Merge Utilities (CV2) ---------------------------------
def merge_images(
    image_paths: list[str],
    output_path: str | None = None,
    max_size_per_image: int = 768,
    border: int = 8,
    border_color: tuple[int, int, int] = (255, 255, 255),
    layout: str = "auto",
) -> str:
    """用 CV2 将多张图片拼接成一张大图（grid 布局）。

    Args:
        image_paths: 图片路径列表
        output_path: 输出路径，为 None 则写入临时文件
        max_size_per_image: 每张子图的最长边像素上限
        border: 子图之间的白色分隔边框宽度
        border_color: 边框 BGR 颜色，默认白色
        layout: "auto" 自动选 grid / "horizontal" 水平排列 / "vertical" 垂直排列

    Returns:
        拼接后图片的文件路径
    """
    if not image_paths:
        raise ValueError("至少需要一张图片")
    if len(image_paths) == 1:
        # 单张图直接复制
        if output_path is None:
            _, output_path = tempfile.mkstemp(suffix=".jpg", prefix="merged_")
        img = cv2.imread(image_paths[0])
        if img is None:
            raise ValueError(f"无法读取图片: {image_paths[0]}")
        cv2.imwrite(output_path, img)
        return output_path

    images = []
    for p in image_paths:
        img = cv2.imread(p)
        if img is None:
            raise ValueError(f"无法读取图片: {p}")
        # 等比缩放
        h, w = img.shape[:2]
        longest = max(h, w)
        if longest > max_size_per_image:
            scale = max_size_per_image / longest
            new_w, new_h = int(w * scale), int(h * scale)
            img = cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_LANCZOS4)
        images.append(img)

    n = len(images)

    if layout == "horizontal":
        # 统一高度，水平拼接
        target_h = min(img.shape[0] for img in images)
        resized = []
        for img in images:
            h, w = img.shape[:2]
            scale = target_h / h
            nw, nh = int(w * scale), target_h
            resized.append(cv2.resize(img, (nw, nh), interpolation=cv2.INTER_LANCZOS4))
        # 加分隔线
        rows = [target_h]
        bordered = []
        for i, img in enumerate(resized):
            b_img = img
            if i > 0:
                # 左侧加白色分隔条
                sep = np.full((target_h, border, 3), border_color, dtype=np.uint8)
                b_img = np.hstack([sep, img])
            bordered.append(b_img)
        merged = np.hstack(bordered)

    elif layout == "vertical":
        # 统一宽度，垂直拼接
        target_w = min(img.shape[1] for img in images)
        resized = []
        for img in images:
            h, w = img.shape[:2]
            scale = target_w / w
            nw, nh = target_w, int(h * scale)
            resized.append(cv2.resize(img, (nw, nh), interpolation=cv2.INTER_LANCZOS4))
        bordered = []
        for i, img in enumerate(resized):
            b_img = img
            if i > 0:
                sep = np.full((border, target_w, 3), border_color, dtype=np.uint8)
                b_img = np.vstack([sep, img])
            bordered.append(b_img)
        merged = np.vstack(bordered)

    else:
        # "auto" — 自动选择 grid 布局
        import math
        cols = min(n, 3)  # 最多 3 列
        rows = math.ceil(n / cols)

        # 统一每列宽度和每行高度
        col_widths = [0] * cols
        row_heights = [0] * rows
        for idx, img in enumerate(images):
            r, c = idx // cols, idx % cols
            h, w = img.shape[:2]
            col_widths[c] = max(col_widths[c], w)
            row_heights[r] = max(row_heights[r], h)

        total_w = sum(col_widths) + border * (cols - 1)
        total_h = sum(row_heights) + border * (rows - 1)
        merged = np.full((total_h, total_w, 3), border_color, dtype=np.uint8)

        y_offset = 0
        for r in range(rows):
            x_offset = 0
            for c in range(cols):
                idx = r * cols + c
                if idx >= n:
                    break
                img = images[idx]
                h, w = img.shape[:2]
                # 居中放置在格子里
                pad_left = (col_widths[c] - w) // 2
                pad_top = (row_heights[r] - h) // 2
                merged[y_offset + pad_top:y_offset + pad_top + h,
                       x_offset + pad_left:x_offset + pad_left + w] = img
                x_offset += col_widths[c] + border
            y_offset += row_heights[r] + border

    if output_path is None:
        _, output_path = tempfile.mkstemp(suffix=".jpg", prefix="merged_refs_")
    cv2.imwrite(output_path, merged, [cv2.IMWRITE_JPEG_QUALITY, 95])
    print(f"   🧩 已拼接 {n} 张参考图 → {os.path.basename(output_path)} ({merged.shape[1]}x{merged.shape[0]})")
    return output_path


async def edit_image_multi_ref(
    image_paths: list[str],
    prompt: str = "",
    size: str = "1024x1024",
    merge_max_size: int = 768,
) -> tuple[str, object]:
    """拼接多张参考图为一张后调用 /images/edits。

    Args:
        image_paths: 多张参考图路径列表
        prompt: 编辑指令
        size: 输出尺寸
        merge_max_size: 每张子图缩放的最长边

    Returns:
        同 edit_image: ("bytes", bytes) | ("url", str) | ("error", str)
    """
    merged_path = merge_images(image_paths, max_size_per_image=merge_max_size)
    try:
        return await edit_image(merged_path, prompt=prompt, size=size)
    finally:
        # 清理临时文件
        try:
            os.unlink(merged_path)
        except OSError:
            pass


async def edit_image(image_path: str, prompt: str = "", size: str = "2048x3072") -> tuple[str, object]:
    """调用 /images/edits，返回 ("bytes", bytes) | ("url", str) | ("error", str)。"""
    if not API_KEY or not BASE_URL:
        return "error", "请在 api.env 中配置 IMAGE_OPENAI_API_KEY 与 IMAGE_OPENAI_BASE_URL"

    try:
        form = aiohttp.FormData()
        form.add_field("model", MODEL)
        form.add_field("prompt", prompt)
        form.add_field("size", size)
        form.add_field("n", "1")

        with open(image_path, "rb") as f:
            data = f.read()
        form.add_field(
            "image[]",
            data,
            filename=os.path.basename(image_path),
            content_type=_content_type_for(image_path),
        )

        headers = {"Authorization": f"Bearer {API_KEY}"}
        timeout = aiohttp.ClientTimeout(total=600)

        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(EDITS_ENDPOINT, headers=headers, data=form) as resp:
                text = await resp.text()
                if resp.status != 200:
                    return "error", f"HTTP {resp.status}: {text[:800]}"

                try:
                    payload = json.loads(text)
                except json.JSONDecodeError:
                    return "error", f"非 JSON 响应: {text[:800]}"

        data_list = payload.get("data") or []
        if data_list and data_list[0].get("b64_json"):
            return "bytes", base64.b64decode(data_list[0]["b64_json"])
        if data_list and data_list[0].get("url"):
            return "url", data_list[0]["url"]

        return "error", str(payload)[:800]

    except Exception as e:
        return "error", str(e)


async def download_image(url: str, filename: str) -> bool:
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=120)) as response:
                response.raise_for_status()
                content = await response.read()
        with open(filename, "wb") as f:
            f.write(content)
        return True
    except Exception:
        return False


async def main_async(args):
    if not os.path.isfile(args.input):
        print(f"❌ 找不到输入文件: {args.input}")
        return 1

    out_path = args.output
    if not out_path:
        stem, ext = os.path.splitext(args.input)
        out_path = f"{stem}_edited.png"

    if args.preset is not None and args.prompt_file:
        print("❌ 不能同时使用 --preset 与 --prompt-file")
        return 1

    if args.preset is not None:
        prompt = PRESET_PROMPTS[args.preset]
    elif args.prompt_file:
        prompt, err = _read_prompt_file(args.prompt_file)
        if err:
            print(f"❌ {err}")
            return 1
    else:
        prompt = args.prompt if args.prompt is not None else ""

    print(f"模型: {MODEL}")
    print(f"输入: {args.input}")
    print(f"输出: {out_path}")
    print(f"prompt: {'(空)' if prompt == '' else prompt[:100] + ('…' if len(prompt) > 100 else '')}")

    kind, payload = await edit_image(args.input, prompt=prompt, size=args.size)

    if kind == "bytes":
        with open(out_path, "wb") as f:
            f.write(payload)
        print(f"✅ 已保存: {out_path}")
        return 0

    if kind == "url":
        ok = await download_image(payload, out_path)
        if ok:
            print(f"✅ 已从 URL 下载保存: {out_path}")
            return 0
        print(f"❌ 下载失败: {payload}")
        return 1

    print(f"❌ 编辑失败: {payload}")
    return 1


def main():
    parser = argparse.ArgumentParser(description="简单图片编辑（images/edits，prompt 默认可为空）")
    parser.add_argument("-i", "--input", required=True, help="输入图片路径")
    parser.add_argument("-o", "--output", default="", help="输出路径（默认：<输入名>_edited.png）")
    parser.add_argument(
        "--prompt",
        default="",
        help="编辑指令（默认空字符串；与 --preset / --prompt-file 互斥时以后者为准）",
    )
    parser.add_argument(
        "--prompt-file",
        default="",
        help="从 UTF-8 文本文件读取整段 prompt（与 --preset 不可同时使用）",
    )
    parser.add_argument(
        "--preset",
        choices=[
            "premium-wood-door",
            "premium-wood-door-v2",
            "premium-wood-door-v2-2k-finish",
            "premium-wood-door-luxury",
            "fujifilm-dining-scene",
        ],
        default=None,
        help=(
            "premium-wood-door = 深色实木敞开门背景；"
            "premium-wood-door-v2 = 同上 + 左侧囍字左右校正 + 右侧女士手/臂略纤细白皙；"
            "premium-wood-door-v2-2k-finish = 已有 v2 成片专用：整体高级调色 + 质感细节 + 2K 说明（不重做布景/不翻囍）；"
            "premium-wood-door-luxury = 高级实木大门 + 严格保留光影 + 囍字镜像 + 女士手/臂白皙纤细 + 2K 质感说明（配合默认尺寸）；"
            "fujifilm-dining-scene = 富士胶片感成片 + 整理桌面杂物 + 女士手指纤细白皙 + 男士肩臂线条"
        ),
    )
    parser.add_argument(
        "--size",
        default="2048x3072",
        help="输出尺寸，默认 2048x3072（约 2K 竖图）；若接口不支持可改 1024x1536",
    )
    args = parser.parse_args()
    raise SystemExit(asyncio.run(main_async(args)))


if __name__ == "__main__":
    main()
